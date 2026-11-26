import json

from ..models import Issue, ReviewResult
from ..review.settings import VALID_SEVERITIES

VALID_VERDICTS = ("approve", "approve_with_suggestions", "changes_requested")


class ReviewParseError(Exception):
    """Raised when the AI's answer can't be understood."""


def _parse_line(value) -> int | None:
    """Accept 12 or "12" or "L12". Anything else (null, true, 0, text) becomes None."""
    if isinstance(value, bool):  # in Python, True counts as an int, so reject it first
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, str):
        text = value.strip().upper().removeprefix("L")
        if text.isdigit() and int(text) > 0:
            return int(text)
    return None


def _verdict_from_issues(issues: list[Issue]) -> str:
    severities = {issue.severity for issue in issues}
    if "critical" in severities:
        return "changes_requested"
    if issues:
        return "approve_with_suggestions"
    return "approve"


def parse_review(raw: str, input_tokens: int = 0, output_tokens: int = 0) -> ReviewResult:
    """Turn the AI's JSON answer into a ReviewResult, fixing small mistakes safely."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ReviewParseError(f"AI did not return valid JSON: {e}") from e
    if not isinstance(data, dict):
        raise ReviewParseError("AI response must be a JSON object")

    issues = []
    for item in data.get("issues") or []:
        if not isinstance(item, dict):
            continue
        severity = str(item.get("severity", "suggestion")).strip().lower()
        if severity not in VALID_SEVERITIES:
            severity = "suggestion"
        issues.append(Issue(
            severity=severity,
            file=str(item.get("file", "")),
            title=str(item.get("title", "")),
            details=str(item.get("details", "")),
            fix=str(item.get("fix", "")),
            rule_violation=bool(item.get("rule_violation", False)),
            line=_parse_line(item.get("line")),
        ))

    verdict = str(data.get("verdict", "")).strip().lower()
    if verdict not in VALID_VERDICTS:
        verdict = _verdict_from_issues(issues)

    return ReviewResult(
        summary=str(data.get("summary", "")),
        issues=tuple(issues),
        verdict=verdict,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
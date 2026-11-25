from .diff_utils import DiffResult
from .models import Issue, ReviewResult
from .review_config import OutputConfig

MARKER = "<!-- ai-code-review -->"

SEVERITY_ORDER = {"critical": 0, "warning": 1, "suggestion": 2}
SEVERITY_LABELS = {
    "critical": "🔴 Critical",
    "warning": "🟠 Warning",
    "suggestion": "🟡 Suggestion",
}
VERDICT_LABELS = {
    "approve": "✅ Approve",
    "approve_with_suggestions": "👍 Approve with suggestions",
    "changes_requested": "❌ Changes requested",
}


def _format_issue(issue: Issue, output: OutputConfig) -> str:
    label = f"{SEVERITY_LABELS[issue.severity]} — " if output.severity_labels else ""
    location = f"`{issue.file}`: " if issue.file else ""
    rule_tag = " 📏 *(team rule)*" if issue.rule_violation else ""

    lines = [f"- {label}{location}**{issue.title}**{rule_tag}"]
    if issue.details:
        lines.append(f"  - {issue.details}")
    if output.show_fixes and issue.fix:
        lines.append(f"  - **Fix:** {issue.fix}")
    return "\n".join(lines)


def format_comment(
    review: ReviewResult,
    diff: DiffResult,
    model: str,
    max_chars: int,
    output: OutputConfig,
    blocked: bool = False,
) -> str:
    parts = [MARKER, "## AI Code Review", ""]

    if output.summary and review.summary:
        parts += ["### Summary", review.summary, ""]

    parts.append("### Issues")
    if review.issues:
        for issue in sorted(review.issues, key=lambda i: SEVERITY_ORDER.get(i.severity, 3)):
            parts.append(_format_issue(issue, output))
    else:
        parts.append("No issues found ✅")
    parts.append("")

    if output.verdict:
        parts += ["### Verdict", VERDICT_LABELS.get(review.verdict, review.verdict), ""]

    if blocked:
        parts += [
            (
                "> ⛔ **Merge blocked** by this repo's review settings. "
                "Fix the issues above and push again."
            ),
            "",
        ]
    notes = []
    if diff.truncated:
        notes.append(f"⚠️ Diff was too large; only the first {max_chars:,} characters were reviewed.")
    if diff.skipped_files:
        notes.append(f"Skipped {len(diff.skipped_files)} ignored/generated file(s).")

    parts.append("---")
    parts += [f"_{note}_" for note in notes]
    parts.append(
        f"<sub>Model: {model} · Tokens: {review.input_tokens} in / "
        f"{review.output_tokens} out</sub>"
    )
    return "\n".join(parts)
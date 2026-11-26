from collections import Counter

from ..diff.filtering import DiffResult
from ..models import Issue, ReviewResult
from ..review.settings import OutputConfig

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


def _sorted(issues) -> list[Issue]:
    return sorted(issues, key=lambda i: SEVERITY_ORDER.get(i.severity, 3))


def _count_line(issues) -> str:
    """e.g. '2 🔴 Critical, 1 🟠 Warning'"""
    counts = Counter(issue.severity for issue in issues)
    return ", ".join(f"{counts[s]} {SEVERITY_LABELS[s]}" for s in SEVERITY_ORDER if counts[s])


def _format_issue(issue: Issue, output: OutputConfig) -> str:
    """One issue as a bullet in the summary comment."""
    label = f"{SEVERITY_LABELS[issue.severity]} — " if output.severity_labels else ""
    if issue.file and issue.line:
        location = f"`{issue.file}:{issue.line}`: "
    elif issue.file:
        location = f"`{issue.file}`: "
    else:
        location = ""
    rule_tag = " 📏 *(team rule)*" if issue.rule_violation else ""

    lines = [f"- {label}{location}**{issue.title}**{rule_tag}"]
    if issue.details:
        lines.append(f"  - {issue.details}")
    if output.show_fixes and issue.fix:
        lines.append(f"  - **Fix:** {issue.fix}")
    return "\n".join(lines)


def format_inline_comment(issue: Issue, output: OutputConfig) -> str:
    """The text of one comment posted directly on a line of code."""
    label = f"{SEVERITY_LABELS[issue.severity]} — " if output.severity_labels else ""
    rule_tag = " 📏 *(team rule)*" if issue.rule_violation else ""

    lines = [f"{label}**{issue.title}**{rule_tag}"]
    if issue.details:
        lines += ["", issue.details]
    if output.show_fixes and issue.fix:
        lines += ["", f"**Fix:** {issue.fix}"]
    return "\n".join(lines)


def format_comment(
    review: ReviewResult,
    diff: DiffResult,
    model: str,
    max_chars: int,
    output: OutputConfig,
    blocked: bool = False,
    inline_count: int = 0,
    listed_issues: tuple[Issue, ...] | None = None,
) -> str:
    """
    Build the summary comment.
    - inline_count: how many issues were posted as line comments
    - listed_issues: which issues to list here (default: all of them)
    """
    listed = review.issues if listed_issues is None else listed_issues

    parts = [MARKER, "## AI Code Review", ""]

    if output.summary and review.summary:
        parts += ["### Summary", review.summary, ""]

    parts.append("### Issues")
    if not review.issues:
        parts.append("No issues found ✅")
    else:
        if inline_count:
            parts.append(
                f"Found {_count_line(review.issues)}. "
                f"💬 {inline_count} of them are commented directly on the code."
            )
            parts.append("")
        if listed:
            if output.comment_style == "inline":
                parts.append("**Issues that couldn't be placed on a specific line:**")
            parts += [_format_issue(issue, output) for issue in _sorted(listed)]
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
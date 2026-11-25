from ai_reviewer.diff_utils import DiffResult
from ai_reviewer.formatter import MARKER, format_comment
from ai_reviewer.models import Issue, ReviewResult
from ai_reviewer.review_config import OutputConfig

ISSUE = Issue(
    severity="critical", file="app.py", title="SQL injection",
    details="Unsafe query", fix="Use parameters",
)
REVIEW = ReviewResult(
    summary="Adds a login page", issues=(ISSUE,), verdict="changes_requested",
    input_tokens=100, output_tokens=20,
)


def _format(review=REVIEW, diff=None, output=None, blocked=False):
    return format_comment(
        review, diff or DiffResult(text="x"), model="test-model", max_chars=1000,
        output=output or OutputConfig(), blocked=blocked,
    )


def test_default_comment_has_all_sections():
    comment = _format()
    assert comment.startswith(MARKER)
    for text in ("### Summary", "🔴 Critical", "SQL injection",
                 "**Fix:** Use parameters", "### Verdict", "test-model"):
        assert text in comment


def test_output_settings_hide_sections():
    output = OutputConfig(summary=False, verdict=False, severity_labels=False, show_fixes=False)
    comment = _format(output=output)
    for text in ("### Summary", "### Verdict", "🔴 Critical", "**Fix:**"):
        assert text not in comment


def test_no_issues_message():
    review = ReviewResult(summary="s", issues=(), verdict="approve")
    assert "No issues found" in _format(review=review)


def test_blocked_banner_and_notes():
    diff = DiffResult(text="x", truncated=True, skipped_files=["yarn.lock"])
    comment = _format(diff=diff, blocked=True)
    assert "Merge blocked" in comment
    assert "too large" in comment
    assert "Skipped 1" in comment
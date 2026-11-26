from ai_reviewer.diff.filtering import DiffResult
from ai_reviewer.models import Issue, ReviewResult
from ai_reviewer.output.formatter import MARKER, format_comment, format_inline_comment
from ai_reviewer.review.settings import OutputConfig

ISSUE = Issue(
    severity="critical", file="app.py", title="SQL injection",
    details="Unsafe query", fix="Use parameters", line=3,
)
ISSUE_2 = Issue(
    severity="warning", file="db.py", title="Connection never closed",
    details="Leaks connections", fix="Use a with block", line=5,
)
REVIEW = ReviewResult(
    summary="Adds a login page", issues=(ISSUE,), verdict="changes_requested",
    input_tokens=100, output_tokens=20,
)


def _format(review=REVIEW, diff=None, output=None, blocked=False, **kwargs):
    return format_comment(
        review, diff or DiffResult(text="x"), model="test-model", max_chars=1000,
        output=output or OutputConfig(), blocked=blocked, **kwargs,
    )


def test_default_comment_has_all_sections():
    comment = _format()
    assert comment.startswith(MARKER)
    for text in ("### Summary", "🔴 Critical", "SQL injection", "`app.py:3`",
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


def test_inline_comment_text():
    text = format_inline_comment(ISSUE, OutputConfig())
    assert "🔴 Critical" in text
    assert "SQL injection" in text
    assert "**Fix:** Use parameters" in text
    assert "**Fix:**" not in format_inline_comment(ISSUE, OutputConfig(show_fixes=False))


def test_inline_mode_lists_only_unplaced_issues():
    review = ReviewResult(summary="s", issues=(ISSUE, ISSUE_2), verdict="changes_requested")
    comment = _format(
        review=review,
        output=OutputConfig(comment_style="inline"),
        inline_count=1,
        listed_issues=(ISSUE,),
    )
    assert "commented directly on the code" in comment
    assert "SQL injection" in comment
    assert "Connection never closed" not in comment
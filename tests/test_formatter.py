from ai_reviewer.diff_utils import DiffResult
from ai_reviewer.formatter import MARKER, format_comment
from ai_reviewer.models import ReviewResult

REVIEW = ReviewResult(text="Looks good ✅", input_tokens=100, output_tokens=20)


def test_comment_has_marker_and_review():
    comment = format_comment(REVIEW, DiffResult(text="x"), model="test-model", max_chars=1000)
    assert comment.startswith(MARKER)
    assert "Looks good ✅" in comment
    assert "test-model" in comment


def test_comment_mentions_truncation():
    diff = DiffResult(text="x", truncated=True)
    comment = format_comment(REVIEW, diff, model="m", max_chars=1000)
    assert "too large" in comment


def test_comment_mentions_skipped_files():
    diff = DiffResult(text="x", skipped_files=["yarn.lock", "logo.png"])
    comment = format_comment(REVIEW, diff, model="m", max_chars=1000)
    assert "Skipped 2" in comment
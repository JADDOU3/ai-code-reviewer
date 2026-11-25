from ai_reviewer.diff_utils import prepare_diff

SAMPLE_DIFF = (
    "diff --git a/app.py b/app.py\n"
    "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-print('hi')\n+print('hello')\n"
    "diff --git a/package-lock.json b/package-lock.json\n"
    "--- a/package-lock.json\n+++ b/package-lock.json\n@@ -1 +1 @@\n-{}\n+{\"a\": 1}\n"
)


def test_skips_lock_files():
    result = prepare_diff(SAMPLE_DIFF, max_chars=10_000)
    assert result.skipped_files == ["package-lock.json"]
    assert "app.py" in result.text
    assert "package-lock.json" not in result.text


def test_not_truncated_when_small():
    result = prepare_diff(SAMPLE_DIFF, max_chars=10_000)
    assert result.truncated is False


def test_truncates_large_diff():
    result = prepare_diff(SAMPLE_DIFF, max_chars=20)
    assert result.truncated is True
    assert len(result.text) == 20


def test_empty_when_only_skipped_files():
    lock_only = (
        "diff --git a/yarn.lock b/yarn.lock\n"
        "--- a/yarn.lock\n+++ b/yarn.lock\n@@ -1 +1 @@\n-a\n+b\n"
    )
    result = prepare_diff(lock_only, max_chars=10_000)
    assert result.is_empty
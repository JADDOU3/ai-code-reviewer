from ai_reviewer.models import Issue
from ai_reviewer.output.inline import build_review_comments, split_issues
from ai_reviewer.review.settings import OutputConfig

ALLOWED = {"app.py": {1, 2, 3}}


def _issue(file, line):
    return Issue(severity="warning", file=file, title="t", details="d", fix="f", line=line)


def test_issue_on_diff_line_is_placed():
    placed, unplaced = split_issues([_issue("app.py", 2)], ALLOWED)
    assert len(placed) == 1
    assert not unplaced


def test_issue_outside_diff_is_not_placed():
    issues = [_issue("app.py", 99), _issue("other.py", 1), _issue("app.py", None)]
    placed, unplaced = split_issues(issues, ALLOWED)
    assert not placed
    assert len(unplaced) == 3


def test_path_prefixes_are_cleaned():
    placed, _ = split_issues([_issue("b/app.py", 1), _issue("./app.py", 3)], ALLOWED)
    assert [issue.file for issue in placed] == ["app.py", "app.py"]


def test_build_review_comments():
    comments = build_review_comments([_issue("app.py", 2)], OutputConfig())
    assert comments[0]["path"] == "app.py"
    assert comments[0]["line"] == 2
    assert comments[0]["side"] == "RIGHT"
    assert "🟠 Warning" in comments[0]["body"]
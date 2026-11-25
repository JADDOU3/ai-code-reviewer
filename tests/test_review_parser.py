import pytest

from ai_reviewer.review_parser import ReviewParseError, parse_review


def test_parses_valid_json():
    raw = (
        '{"summary": "Adds login", "issues": [{"severity": "critical", "file": "a.py", '
        '"title": "SQL injection", "details": "d", "fix": "f", "rule_violation": false}], '
        '"verdict": "changes_requested"}'
    )
    review = parse_review(raw)
    assert review.summary == "Adds login"
    assert review.issues[0].severity == "critical"
    assert review.verdict == "changes_requested"


def test_unknown_severity_becomes_suggestion():
    raw = '{"summary": "", "issues": [{"severity": "huge", "title": "x"}], "verdict": "approve"}'
    assert parse_review(raw).issues[0].severity == "suggestion"


def test_missing_verdict_is_inferred():
    raw = '{"summary": "", "issues": [{"severity": "critical", "title": "x"}]}'
    assert parse_review(raw).verdict == "changes_requested"


def test_invalid_json_raises():
    with pytest.raises(ReviewParseError):
        parse_review("not json")
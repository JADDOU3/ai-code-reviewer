from ai_reviewer.gate import should_block
from ai_reviewer.models import Issue, ReviewResult
from ai_reviewer.review_config import GateConfig


def _review(*severities, verdict="approve"):
    issues = tuple(
        Issue(severity=s, file="a.py", title="t", details="d", fix="f") for s in severities
    )
    return ReviewResult(summary="s", issues=issues, verdict=verdict)


def test_never_blocks():
    review = _review("critical", verdict="changes_requested")
    assert not should_block(review, GateConfig("never"))


def test_critical_blocks_only_on_critical():
    gate = GateConfig("critical")
    assert should_block(_review("critical"), gate)
    assert not should_block(_review("warning", "suggestion"), gate)


def test_warning_blocks_on_warning_or_worse():
    gate = GateConfig("warning")
    assert should_block(_review("warning"), gate)
    assert not should_block(_review("suggestion"), gate)


def test_changes_requested_uses_verdict():
    gate = GateConfig("changes_requested")
    assert should_block(_review(verdict="changes_requested"), gate)
    assert not should_block(_review("critical", verdict="approve"), gate)
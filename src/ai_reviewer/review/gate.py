from ..models import ReviewResult
from .settings import GateConfig


def should_block(review: ReviewResult, gate: GateConfig) -> bool:
    """Decide if this review should fail the check (and block merging)."""
    severities = {issue.severity for issue in review.issues}

    if gate.block_on == "critical":
        return "critical" in severities
    if gate.block_on == "warning":
        return bool(severities & {"critical", "warning"})
    if gate.block_on == "changes_requested":
        return review.verdict == "changes_requested"
    return False  # "never"
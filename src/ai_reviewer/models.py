from dataclasses import dataclass


@dataclass(frozen=True)
class PullRequest:
    repo: str
    number: int
    title: str
    body: str
    base_ref: str  # the branch the PR wants to merge into, e.g. "main"
    head_sha: str  # the PR's latest commit, needed to post line comments


@dataclass(frozen=True)
class Issue:
    severity: str  # critical | warning | suggestion
    file: str
    title: str
    details: str
    fix: str
    rule_violation: bool = False  # True if it breaks one of the team's custom rules
    line: int | None = None       # line in the new file, if the AI gave one


@dataclass(frozen=True)
class ReviewResult:
    summary: str
    issues: tuple[Issue, ...]
    verdict: str  # approve | approve_with_suggestions | changes_requested
    input_tokens: int = 0
    output_tokens: int = 0
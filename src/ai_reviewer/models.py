from dataclasses import dataclass


@dataclass(frozen=True)
class PullRequest:
    repo: str
    number: int
    title: str
    body: str


@dataclass(frozen=True)
class ReviewResult:
    text: str
    input_tokens: int
    output_tokens: int
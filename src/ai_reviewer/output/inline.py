from dataclasses import replace

from ..models import Issue
from ..review.settings import OutputConfig
from .formatter import format_inline_comment


def _normalize_path(path: str) -> str:
    """The AI sometimes writes 'b/app.py' or './app.py'. Clean that to 'app.py'."""
    path = path.strip()
    for prefix in ("b/", "./"):
        path = path.removeprefix(prefix)
    return path


def split_issues(
    issues, allowed_lines: dict[str, set[int]]
) -> tuple[list[Issue], list[Issue]]:
    """
    Split issues into:
    - placed: the file and line exist in the diff, so we can comment on that line
    - unplaced: everything else (no line, wrong line, or a file not in the diff)
    """
    placed, unplaced = [], []
    for issue in issues:
        clean = replace(issue, file=_normalize_path(issue.file))
        if clean.line is not None and clean.line in allowed_lines.get(clean.file, set()):
            placed.append(clean)
        else:
            unplaced.append(clean)
    return placed, unplaced


def build_review_comments(issues: list[Issue], output: OutputConfig) -> list[dict]:
    """Turn placed issues into the format GitHub's review API expects."""
    return [
        {
            "path": issue.file,
            "line": issue.line,
            "side": "RIGHT",  # comment on the new version of the code
            "body": format_inline_comment(issue, output),
        }
        for issue in issues
    ]
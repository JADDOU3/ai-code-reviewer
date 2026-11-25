from dataclasses import dataclass, field

# Generated, lock, and binary files: noisy and not worth paying to review
DEFAULT_SKIP_PATTERNS = (
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
    ".min.js", ".min.css", ".svg", ".png", ".jpg", ".jpeg", ".gif", ".ico",
)


@dataclass
class DiffResult:
    text: str
    skipped_files: list[str] = field(default_factory=list)
    truncated: bool = False

    @property
    def is_empty(self) -> bool:
        return not self.text.strip()


def _file_path(chunk: str) -> str:
    # First line of a chunk looks like: "a/path/to/file b/path/to/file"
    return chunk.splitlines()[0].split(" b/")[-1]


def prepare_diff(
    raw_diff: str,
    max_chars: int,
    skip_patterns: tuple[str, ...] = DEFAULT_SKIP_PATTERNS,
) -> DiffResult:
    """Remove files we don't want to review, then trim the diff to max_chars."""
    kept, skipped = [], []
    for chunk in raw_diff.split("diff --git "):
        if not chunk.strip():
            continue
        path = _file_path(chunk)
        if path.endswith(skip_patterns):
            skipped.append(path)
        else:
            kept.append("diff --git " + chunk)

    text = "".join(kept)
    truncated = len(text) > max_chars
    if truncated:
        text = text[:max_chars]

    return DiffResult(text=text, skipped_files=skipped, truncated=truncated)
from .diff_utils import DiffResult
from .models import ReviewResult

MARKER = "<!-- ai-code-review -->"


def format_comment(review: ReviewResult, diff: DiffResult, model: str, max_chars: int) -> str:
    notes = []
    if diff.truncated:
        notes.append(f"⚠️ Diff was too large; only the first {max_chars:,} characters were reviewed.")
    if diff.skipped_files:
        notes.append(f"Skipped {len(diff.skipped_files)} generated/binary file(s).")

    parts = [MARKER, "## AI Code Review", "", review.text, "", "---"]
    parts += [f"_{note}_" for note in notes]
    parts.append(
        f"<sub>Model: {model} · Tokens: {review.input_tokens} in / "
        f"{review.output_tokens} out</sub>"
    )
    return "\n".join(parts)
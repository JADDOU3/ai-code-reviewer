import re

# Finds the "+1" part in a hunk header like "@@ -1,3 +1,4 @@"
HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def _walk_diff(diff_text: str):
    """
    Go through the diff line by line.
    Yields (line, file, new_line_number). new_line_number is None when the line
    doesn't exist in the new version of the file (headers, deleted lines, etc.).
    """
    current_file = None
    line_number = 0
    in_hunk = False

    for line in diff_text.splitlines():
        number = None

        if line.startswith("diff --git"):
            # A new file starts
            current_file = None
            in_hunk = False
        elif not in_hunk and line.startswith("+++ "):
            # "+++ b/app.py" → "app.py"; "+++ /dev/null" means the file was deleted
            path = line[4:].strip()
            current_file = None if path == "/dev/null" else path.removeprefix("b/")
        elif match := HUNK_HEADER.match(line):
            # A new hunk: start counting from the new-file start line
            line_number = int(match.group(1))
            in_hunk = True
        elif in_hunk and current_file and line[:1] in (" ", "+"):
            # Unchanged or added line: it exists in the new file
            number = line_number
            line_number += 1
        # Deleted lines ("-") and other lines get no number

        yield line, current_file, number


def commentable_lines(diff_text: str) -> dict[str, set[int]]:
    """Return {file_path: {line numbers that GitHub allows comments on}}."""
    result: dict[str, set[int]] = {}
    for _, file, number in _walk_diff(diff_text):
        if number is not None:
            result.setdefault(file, set()).add(number)
    return result


def annotate_diff(diff_text: str) -> str:
    """Add 'L<number>: ' in front of every line that exists in the new file."""
    annotated = []
    for line, _, number in _walk_diff(diff_text):
        annotated.append(f"L{number}: {line}" if number is not None else line)
    return "\n".join(annotated)
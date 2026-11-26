from ai_reviewer.diff.lines import annotate_diff, commentable_lines

DIFF = (
    "diff --git a/app.py b/app.py\n"
    "--- a/app.py\n"
    "+++ b/app.py\n"
    "@@ -1,3 +1,4 @@\n"
    " import os\n"
    "-x = 1\n"
    "+x = 2\n"
    "+y = 3\n"
    " print(x)\n"
    "@@ -20,2 +21,2 @@\n"
    " def main():\n"
    "-    pass\n"
    "+    run()\n"
    "diff --git a/new.py b/new.py\n"
    "--- /dev/null\n"
    "+++ b/new.py\n"
    "@@ -0,0 +1,2 @@\n"
    "+a = 1\n"
    "+b = 2\n"
)


def test_commentable_lines_tracks_new_line_numbers():
    assert commentable_lines(DIFF) == {
        "app.py": {1, 2, 3, 4, 21, 22},
        "new.py": {1, 2},
    }


def test_deleted_file_has_no_commentable_lines():
    diff = (
        "diff --git a/old.py b/old.py\n"
        "--- a/old.py\n"
        "+++ /dev/null\n"
        "@@ -1,2 +0,0 @@\n"
        "-a = 1\n"
        "-b = 2\n"
    )
    assert commentable_lines(diff) == {}


def test_annotate_adds_line_numbers_to_new_side():
    annotated = annotate_diff(DIFF)
    assert "L2: +x = 2" in annotated
    assert "L4:  print(x)" in annotated
    assert "L22: +    run()" in annotated
    assert "L1: +a = 1" in annotated


def test_annotate_leaves_removed_lines_and_headers_alone():
    lines = annotate_diff(DIFF).splitlines()
    assert "-x = 1" in lines
    assert lines[2] == "+++ b/app.py"
    assert lines[3] == "@@ -1,3 +1,4 @@"
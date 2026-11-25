from .models import PullRequest
from .review_config import ReviewConfig

FOCUS_DESCRIPTIONS = {
    "bugs": "bugs and logic errors",
    "security": "security problems (secrets in code, injection, unsafe input handling)",
    "performance": "performance problems",
    "readability": "readability and maintainability",
    "tests": "missing or weak tests for the changed code",
    "documentation": "missing or outdated comments and documentation",
}

TONE_INSTRUCTIONS = {
    "friendly": "Be friendly and encouraging, like a helpful senior teammate.",
    "strict": "Be strict and direct. Point out every real problem.",
    "concise": "Be very brief. Keep every explanation to one short sentence.",
}

JSON_FORMAT = """Respond with ONLY a JSON object in exactly this shape:
{
  "summary": "1-2 sentences about what the PR does",
  "issues": [
    {
      "severity": "critical" | "warning" | "suggestion",
      "file": "path/to/file",
      "title": "short title of the problem",
      "details": "what is wrong and why it matters",
      "fix": "how to fix it",
      "rule_violation": true or false
    }
  ],
  "verdict": "approve" | "approve_with_suggestions" | "changes_requested"
}

Severity guide:
- critical: bugs or security holes that must be fixed before merging
- warning: real problems that should be fixed
- suggestion: nice-to-have improvements

Verdict guide:
- changes_requested: there is at least one critical issue
- approve_with_suggestions: only warnings or suggestions
- approve: no issues"""


def build_system_prompt(config: ReviewConfig) -> str:
    focus_lines = "\n".join(f"- {FOCUS_DESCRIPTIONS[f]}" for f in config.focus)

    parts = [
        "You are a senior software engineer reviewing a pull request.",
        "Review ONLY the changes in the diff.",
        "",
        "Focus on:",
        focus_lines,
    ]

    if config.custom_rules:
        rules = "\n".join(f"{i}. {rule}" for i, rule in enumerate(config.custom_rules, 1))
        parts += [
            "",
            (
                "The team has these coding rules. Report every violation in the changed code "
                f'as its own issue with severity "{config.rule_severity}" and rule_violation true:'
            ),
            rules,
        ]

    parts += [
        "",
        "How to review:",
        "- Be specific: name the file and the code you mean.",
        "- Do not nitpick formatting unless a team rule requires it.",
        "- If the code is fine, return an empty issues list.",
        f"- {TONE_INSTRUCTIONS[config.tone]}",
        (
            f"- Write the summary, titles, details, and fixes in {config.language}. "
            "Keep the JSON keys and the severity and verdict values in English."
        ),
        "",
        JSON_FORMAT,
    ]
    return "\n".join(parts)


def build_user_message(pr: PullRequest, diff_text: str) -> str:
    return (
        f"PR title: {pr.title}\n\n"
        f"PR description:\n{pr.body or '(none)'}\n\n"
        f"Diff:\n```diff\n{diff_text}\n```"
    )
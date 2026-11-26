import logging
import sys

import requests

from .ai.reviewer import AIReviewer
from .config import ConfigError, Settings
from .diff.filtering import prepare_diff
from .diff.lines import annotate_diff, commentable_lines
from .github.client import GitHubClient, load_pull_request
from .output.formatter import MARKER, format_comment
from .output.inline import build_review_comments, split_issues
from .review.gate import should_block
from .review.settings import CONFIG_FILE_NAME, parse_review_config

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("ai_reviewer")

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_CONFIG_ERROR = 2
EXIT_BLOCKED = 3

REVIEW_BODY = "🤖 AI Code Review: comments on the changed lines. See the summary comment for the full review."


def run(settings: Settings) -> int:
    github = GitHubClient(settings.github_token)

    if settings.pr_number is not None:
        pr = github.get_pull_request(settings.repository, settings.pr_number)
    else:
        pr = load_pull_request(settings.event_path, settings.repository)

    log.info("Reviewing PR #%s in %s with %s", pr.number, pr.repo, settings.model)

    # Settings come from the base branch, so a PR can't change its own rules
    config_text = github.get_file(pr.repo, CONFIG_FILE_NAME, pr.base_ref)
    review_config = parse_review_config(config_text)
    output = review_config.output
    if config_text:
        log.info("Using %s from branch '%s'", CONFIG_FILE_NAME, pr.base_ref)
    else:
        log.info("No %s found, using default settings", CONFIG_FILE_NAME)
    log.info("Comment style: %s", output.comment_style)

    diff = prepare_diff(
        github.get_diff(pr.repo, pr.number),
        settings.max_diff_chars,
        ignore_paths=review_config.ignore_paths,
    )
    if diff.is_empty:
        log.info("Nothing to review (all changed files were skipped or ignored).")
        return EXIT_OK

    # Send the diff with line numbers so the AI can point to exact lines
    review = AIReviewer(settings.openai_api_key, settings.model).review(
        pr, annotate_diff(diff.text), review_config
    )
    blocked = should_block(review, review_config.gate)

    # Decide which issues go on lines and which stay in the summary
    if output.comment_style == "summary":
        placed, unplaced = [], list(review.issues)
    else:
        placed, unplaced = split_issues(review.issues, commentable_lines(diff.text))
    line_comments = build_review_comments(placed, output)

    def build_summary(inline_count: int = 0, listed_issues=None) -> str:
        return format_comment(
            review, diff, settings.model, settings.max_diff_chars, output, blocked,
            inline_count=inline_count, listed_issues=listed_issues,
        )

    if output.comment_style == "inline":
        comment = build_summary(len(placed), tuple(unplaced))
    else:  # "summary" or "both"
        comment = build_summary(len(placed))

    if settings.dry_run:
        log.info("DRY_RUN is on — printing instead of posting:\n")
        print(comment)
        for c in line_comments:
            print(f"\n----- Line comment on {c['path']}, line {c['line']} -----\n{c['body']}")
    else:
        github.upsert_comment(pr.repo, pr.number, comment, MARKER)
        log.info("Summary comment posted ✅")

        if line_comments:
            try:
                github.create_review(pr.repo, pr.number, pr.head_sha, REVIEW_BODY, line_comments)
                log.info("Posted %s line comment(s) ✅", len(line_comments))
            except requests.HTTPError as e:
                # If GitHub rejects the line comments, don't lose them: put everything in the summary
                details = e.response.text if e.response is not None else str(e)
                log.warning("Couldn't post line comments, adding all issues to the summary: %s", details)
                github.upsert_comment(pr.repo, pr.number, build_summary(), MARKER)

    log.info("Tokens used: %s in / %s out", review.input_tokens, review.output_tokens)

    if blocked:
        log.error("Merge blocked: review matched 'block_on: %s'.", review_config.gate.block_on)
        return EXIT_BLOCKED
    return EXIT_OK


def main() -> int:
    try:
        return run(Settings.from_env())
    except ConfigError as e:
        log.error("Configuration error: %s", e)
        return EXIT_CONFIG_ERROR
    except Exception:
        log.exception("Review failed")
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
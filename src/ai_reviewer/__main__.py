import logging
import sys

from .config import ConfigError, Settings
from .diff_utils import prepare_diff
from .formatter import MARKER, format_comment
from .gate import should_block
from .github_client import GitHubClient, load_pull_request
from .llm import AIReviewer
from .review_config import CONFIG_FILE_NAME, parse_review_config

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("ai_reviewer")

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_CONFIG_ERROR = 2
EXIT_BLOCKED = 3


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
    if config_text:
        log.info("Using %s from branch '%s'", CONFIG_FILE_NAME, pr.base_ref)
    else:
        log.info("No %s found, using default settings", CONFIG_FILE_NAME)

    diff = prepare_diff(
        github.get_diff(pr.repo, pr.number),
        settings.max_diff_chars,
        ignore_paths=review_config.ignore_paths,
    )
    if diff.is_empty:
        log.info("Nothing to review (all changed files were skipped or ignored).")
        return EXIT_OK

    review = AIReviewer(settings.openai_api_key, settings.model).review(
        pr, diff.text, review_config
    )
    blocked = should_block(review, review_config.gate)
    comment = format_comment(
        review, diff, settings.model, settings.max_diff_chars, review_config.output, blocked
    )

    if settings.dry_run:
        log.info("DRY_RUN is on — printing the review instead of posting it:\n")
        print(comment)
    else:
        github.upsert_comment(pr.repo, pr.number, comment, MARKER)
        log.info(
            "Review posted ✅ (%s in / %s out tokens)",
            review.input_tokens, review.output_tokens,
        )

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
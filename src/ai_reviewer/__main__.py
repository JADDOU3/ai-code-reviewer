import logging
import sys

from .config import ConfigError, Settings
from .diff_utils import prepare_diff
from .formatter import MARKER, format_comment
from .github_client import GitHubClient, load_pull_request
from .llm import AIReviewer

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("ai_reviewer")


def run(settings: Settings) -> None:
    github = GitHubClient(settings.github_token)

    if settings.pr_number is not None:
        pr = github.get_pull_request(settings.repository, settings.pr_number)
    else:
        pr = load_pull_request(settings.event_path, settings.repository)

    log.info("Reviewing PR #%s in %s with %s", pr.number, pr.repo, settings.model)

    diff = prepare_diff(github.get_diff(pr.repo, pr.number), settings.max_diff_chars)
    if diff.is_empty:
        log.info("Nothing to review (only skipped files).")
        return

    review = AIReviewer(settings.openai_api_key, settings.model).review(pr, diff.text)
    comment = format_comment(review, diff, settings.model, settings.max_diff_chars)

    if settings.dry_run:
        log.info("DRY_RUN is on — printing the review instead of posting it:\n")
        print(comment)
        return

    github.upsert_comment(pr.repo, pr.number, comment, MARKER)
    log.info("Review posted ✅ (%s in / %s out tokens)", review.input_tokens, review.output_tokens)


def main() -> int:
    try:
        run(Settings.from_env())
    except ConfigError as e:
        log.error("Configuration error: %s", e)
        return 2
    except Exception:
        log.exception("Review failed")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
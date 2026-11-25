import os
from dataclasses import dataclass

DEFAULT_MODEL = "gpt-5.4-mini"
DEFAULT_MAX_DIFF_CHARS = 60_000

REQUIRED_ENV_VARS = ("GITHUB_TOKEN", "OPENAI_API_KEY", "GITHUB_REPOSITORY")


class ConfigError(Exception):
    """Raised when required settings are missing or invalid."""


def _parse_bool(value: str | None) -> bool:
    return (value or "").strip().lower() in ("1", "true", "yes")


@dataclass(frozen=True)
class Settings:
    github_token: str
    openai_api_key: str
    repository: str
    event_path: str | None = None   # set automatically in GitHub Actions
    pr_number: int | None = None    # set manually for local runs
    model: str = DEFAULT_MODEL
    max_diff_chars: int = DEFAULT_MAX_DIFF_CHARS
    dry_run: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
        if missing:
            raise ConfigError(f"Missing environment variables: {', '.join(missing)}")

        event_path = os.getenv("GITHUB_EVENT_PATH")
        pr_number_raw = os.getenv("PR_NUMBER")
        if not event_path and not pr_number_raw:
            raise ConfigError(
                "Set PR_NUMBER (local run) or GITHUB_EVENT_PATH (GitHub Actions)"
            )

        pr_number = None
        if pr_number_raw:
            try:
                pr_number = int(pr_number_raw)
            except ValueError as e:
                raise ConfigError("PR_NUMBER must be a number") from e

        try:
            max_chars = int(os.getenv("MAX_DIFF_CHARS", DEFAULT_MAX_DIFF_CHARS))
        except ValueError as e:
            raise ConfigError("MAX_DIFF_CHARS must be a number") from e

        return cls(
            github_token=os.environ["GITHUB_TOKEN"],
            openai_api_key=os.environ["OPENAI_API_KEY"],
            repository=os.environ["GITHUB_REPOSITORY"],
            event_path=event_path,
            pr_number=pr_number,
            model=os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
            max_diff_chars=max_chars,
            dry_run=_parse_bool(os.getenv("DRY_RUN")),
        )
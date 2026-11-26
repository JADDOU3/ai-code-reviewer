from dataclasses import dataclass, field

import yaml

from ..config import ConfigError

CONFIG_FILE_NAME = ".ai-reviewer.yml"

VALID_FOCUS = ("bugs", "security", "performance", "readability", "tests", "documentation")
VALID_TONES = ("friendly", "strict", "concise")
VALID_SEVERITIES = ("critical", "warning", "suggestion")
VALID_BLOCK_ON = ("never", "critical", "warning", "changes_requested")
VALID_COMMENT_STYLES = ("summary", "inline", "both")

TOP_LEVEL_KEYS = {"review", "output", "gate"}
REVIEW_KEYS = {"focus", "custom_rules", "rule_severity", "ignore_paths", "language", "tone"}
OUTPUT_KEYS = {"summary", "verdict", "severity_labels", "show_fixes", "comment_style"}
GATE_KEYS = {"block_on"}


@dataclass(frozen=True)
class OutputConfig:
    summary: bool = True
    verdict: bool = True
    severity_labels: bool = True
    show_fixes: bool = True
    comment_style: str = "summary"


@dataclass(frozen=True)
class GateConfig:
    block_on: str = "never"


@dataclass(frozen=True)
class ReviewConfig:
    focus: tuple[str, ...] = ("bugs", "security", "performance", "readability")
    custom_rules: tuple[str, ...] = ()
    rule_severity: str = "warning"
    ignore_paths: tuple[str, ...] = ()
    language: str = "English"
    tone: str = "friendly"
    output: OutputConfig = field(default_factory=OutputConfig)
    gate: GateConfig = field(default_factory=GateConfig)


def _check_keys(section: dict, allowed: set[str], where: str) -> None:
    unknown = set(section) - allowed
    if unknown:
        raise ConfigError(
            f"Unknown setting(s) in {where}: {', '.join(sorted(map(str, unknown)))}. "
            f"Allowed: {', '.join(sorted(allowed))}"
        )


def _section(data: dict, key: str) -> dict:
    value = data.get(key) or {}
    if not isinstance(value, dict):
        raise ConfigError(f"'{key}' must be a section of settings (key: value)")
    return value


def _str_list(value, name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise ConfigError(f"'{name}' must be a list of text values")
    return tuple(v.strip() for v in value if v.strip())


def _choice(value, name: str, allowed: tuple[str, ...], default: str) -> str:
    if value is None:
        return default
    if isinstance(value, bool):  # YAML turns yes/no/on/off into true/false
        raise ConfigError(f"'{name}' must be one of: {', '.join(allowed)}")
    value = str(value).strip().lower()
    if value not in allowed:
        raise ConfigError(f"'{name}' must be one of: {', '.join(allowed)} (got '{value}')")
    return value


def _bool(value, name: str, default: bool) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ConfigError(f"'{name}' must be true or false")
    return value


def parse_review_config(text: str | None) -> ReviewConfig:
    """Turn the text of .ai-reviewer.yml into a validated ReviewConfig."""
    if not text or not text.strip():
        return ReviewConfig()

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise ConfigError(f"{CONFIG_FILE_NAME} is not valid YAML: {e}") from e

    if data is None:
        return ReviewConfig()
    if not isinstance(data, dict):
        raise ConfigError(f"{CONFIG_FILE_NAME} must contain sections like review:, output:, gate:")

    _check_keys(data, TOP_LEVEL_KEYS, CONFIG_FILE_NAME)
    review = _section(data, "review")
    output = _section(data, "output")
    gate = _section(data, "gate")
    _check_keys(review, REVIEW_KEYS, "review")
    _check_keys(output, OUTPUT_KEYS, "output")
    _check_keys(gate, GATE_KEYS, "gate")

    defaults = ReviewConfig()

    focus = tuple(f.lower() for f in _str_list(review.get("focus"), "review.focus"))
    focus = focus or defaults.focus
    bad_focus = [f for f in focus if f not in VALID_FOCUS]
    if bad_focus:
        raise ConfigError(
            f"Unknown focus area(s): {', '.join(bad_focus)}. Allowed: {', '.join(VALID_FOCUS)}"
        )

    language = review.get("language", defaults.language)
    if not isinstance(language, str) or not language.strip():
        raise ConfigError("'review.language' must be text, like English or Arabic")

    return ReviewConfig(
        focus=focus,
        custom_rules=_str_list(review.get("custom_rules"), "review.custom_rules"),
        rule_severity=_choice(
            review.get("rule_severity"), "review.rule_severity",
            VALID_SEVERITIES, defaults.rule_severity,
        ),
        ignore_paths=_str_list(review.get("ignore_paths"), "review.ignore_paths"),
        language=language.strip(),
        tone=_choice(review.get("tone"), "review.tone", VALID_TONES, defaults.tone),
        output=OutputConfig(
            summary=_bool(output.get("summary"), "output.summary", True),
            verdict=_bool(output.get("verdict"), "output.verdict", True),
            severity_labels=_bool(output.get("severity_labels"), "output.severity_labels", True),
            show_fixes=_bool(output.get("show_fixes"), "output.show_fixes", True),
            comment_style=_choice(
                output.get("comment_style"), "output.comment_style",
                VALID_COMMENT_STYLES, "summary",
            ),
        ),
        gate=GateConfig(
            block_on=_choice(gate.get("block_on"), "gate.block_on", VALID_BLOCK_ON, "never"),
        ),
    )
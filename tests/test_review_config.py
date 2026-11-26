import pytest

from ai_reviewer.config import ConfigError
from ai_reviewer.review.settings import ReviewConfig, parse_review_config


def test_no_file_gives_defaults():
    assert parse_review_config(None) == ReviewConfig()


def test_parses_full_config():
    text = """
review:
  focus: [security, bugs]
  custom_rules:
    - Use snake_case for function names
  rule_severity: critical
  ignore_paths: ["docs/*"]
  language: Arabic
  tone: strict
output:
  verdict: false
gate:
  block_on: critical
"""
    config = parse_review_config(text)
    assert config.focus == ("security", "bugs")
    assert config.custom_rules == ("Use snake_case for function names",)
    assert config.rule_severity == "critical"
    assert config.ignore_paths == ("docs/*",)
    assert config.language == "Arabic"
    assert config.tone == "strict"
    assert config.output.verdict is False
    assert config.output.summary is True
    assert config.gate.block_on == "critical"


def test_invalid_tone_raises():
    with pytest.raises(ConfigError, match="tone"):
        parse_review_config("review:\n  tone: angry\n")


def test_unknown_setting_raises():
    with pytest.raises(ConfigError, match="Unknown"):
        parse_review_config("review:\n  colour: blue\n")


def test_invalid_yaml_raises():
    with pytest.raises(ConfigError, match="not valid YAML"):
        parse_review_config("review: [unclosed")


def test_comment_style():
    config = parse_review_config("output:\n  comment_style: inline\n")
    assert config.output.comment_style == "inline"
    assert parse_review_config(None).output.comment_style == "summary"
    with pytest.raises(ConfigError, match="comment_style"):
        parse_review_config("output:\n  comment_style: sideways\n")
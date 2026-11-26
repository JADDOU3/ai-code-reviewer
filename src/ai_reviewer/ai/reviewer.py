from openai import OpenAI

from ..models import PullRequest, ReviewResult
from ..review.settings import ReviewConfig
from .parser import parse_review
from .prompts import build_system_prompt, build_user_message


class AIReviewer:
    def __init__(self, api_key: str, model: str):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def review(self, pr: PullRequest, diff_text: str, config: ReviewConfig) -> ReviewResult:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": build_system_prompt(config)},
                {"role": "user", "content": build_user_message(pr, diff_text)},
            ],
            response_format={"type": "json_object"},  # forces a JSON answer
        )
        usage = response.usage
        return parse_review(
            response.choices[0].message.content or "",
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
        )
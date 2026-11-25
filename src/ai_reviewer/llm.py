from openai import OpenAI

from .models import PullRequest, ReviewResult
from .prompts import SYSTEM_PROMPT, build_user_message


class AIReviewer:
    def __init__(self, api_key: str, model: str):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def review(self, pr: PullRequest, diff_text: str) -> ReviewResult:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_message(pr, diff_text)},
            ],
        )
        usage = response.usage
        return ReviewResult(
            text=response.choices[0].message.content or "",
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
        )
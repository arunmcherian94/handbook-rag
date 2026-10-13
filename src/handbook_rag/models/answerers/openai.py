"""OpenAI Chat Completions adapter: translates the SDK's response into the Answerer port."""

from handbook_rag.constants import MAX_COMPLETION_TOKENS, REASONING_EFFORT
from handbook_rag.models.base import Completion


class OpenAIAnswerer:
    def __init__(
        self,
        client,
        model: str,
        effort: str = REASONING_EFFORT,
        max_completion_tokens: int = MAX_COMPLETION_TOKENS,
    ):
        self.client = client  # injected, so tests pass a fake client
        self.model = model
        self.name = f"openai:{model}"
        self.effort = effort
        self.max_completion_tokens = max_completion_tokens

    def answer(self, system: str, user: str) -> Completion:
        # No `tools` are passed: the model cannot call any (AC-6).
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            reasoning_effort=self.effort,
            max_completion_tokens=self.max_completion_tokens,
        )
        choice = resp.choices[0]
        return Completion(
            text=choice.message.content or "",
            input_tokens=resp.usage.prompt_tokens,
            output_tokens=resp.usage.completion_tokens,
            truncated=choice.finish_reason == "length",
        )

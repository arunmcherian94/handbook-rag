"""OpenAI Chat Completions adapter: translates the SDK's response into the ChatModel port."""

from handbook_rag.constants import MAX_COMPLETION_TOKENS, REASONING_EFFORT
from handbook_rag.models.base import ChatStep, ToolCall


class OpenAIChatModel:
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

    def complete(
        self,
        messages: list[dict],
        tools: list[dict],
        tool_choice: str,
        timeout: float | None = None,
    ) -> ChatStep:
        kwargs = {"timeout": timeout} if timeout is not None else {}
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            parallel_tool_calls=False,  # AC-1: one call per step
            reasoning_effort=self.effort,
            max_completion_tokens=self.max_completion_tokens,
            **kwargs,
        )
        choice = resp.choices[0]
        # Arguments stay the raw string: a malformed call is the tool's to reject, not ours.
        calls = tuple(
            ToolCall(c.id, c.function.name, c.function.arguments)
            for c in (choice.message.tool_calls or ())
        )
        return ChatStep(
            text=choice.message.content or "",
            tool_calls=calls,
            input_tokens=resp.usage.prompt_tokens,
            output_tokens=resp.usage.completion_tokens,
            finish_reason=choice.finish_reason,
        )

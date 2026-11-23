"""The agent's only tool: retrieve(query, page) (spec 0013, AC-2 to AC-5).

The Principal is bound when TurnTool is built and closed over; no argument can name a user or
group (AC-5). Chunks come only through ask.retrieve -> ask.search, the verified ACL path (AC-3).
Excerpts are numbered per turn, the first time each chunk is returned (AC-4).
"""

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, replace

import tiktoken

from handbook_rag import ask
from handbook_rag.ask import Retrieved
from handbook_rag.constants import (
    AGENT_MAX_QUERY_TOKENS,
    AGENT_PAGES,
    BASELINE_CONFIG,
    TOKENIZER,
    TOP_K,
)
from handbook_rag.identity import Principal
from handbook_rag.models import Embedder, ToolCall

TOOL_NAME = "retrieve"
EMPTY_PAGE = "No excerpts found."

# The Chat Completions tool definition, strict schema (AC-2). Its sha256 goes in the header.
TOOL: dict = {
    "type": "function",
    "function": {
        "name": TOOL_NAME,
        "description": (
            f"Search the GitLab handbook. Returns {TOP_K} numbered excerpts per page. "
            "Start at page 1. "
            "Ask for the next page only when the results are on-topic but miss the detail you "
            "need; if they are off-topic, reword the query instead. Use one search per part of a "
            "multi-part question. "
            'Example: {"query": "expense report approval by manager", "page": 1}'
        ),
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to look for, as a short natural-language search query.",
                },
                "page": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": AGENT_PAGES,
                    "description": f"Result page, 1 to {AGENT_PAGES}. Start at 1.",
                },
            },
            "required": ["query", "page"],
            "additionalProperties": False,
        },
    },
}
_KEYS = {"query", "page"}


def _format(excerpts: list[Retrieved]) -> str:
    """The excerpt block exactly as ask.build_prompt formats it."""
    return "\n\n".join(f"[{c.n}] {c.url_path} — {c.heading}\n{c.content}" for c in excerpts)


class ToolTimeout(RuntimeError):
    """A retry wait would run past the turn's remaining time (AC-8, review fix)."""


@dataclass(frozen=True)
class ToolResult:
    """What one tool call produced, for the model (content) and the turn record (the rest)."""

    content: str  # the tool message sent to the model: excerpts, EMPTY_PAGE, or an error text
    accepted: bool  # False: rejected before execution (bad JSON, unknown tool, bad args, query)
    error: str | None  # the rejection reason, None when accepted
    numbers: tuple[int, ...]  # per-turn excerpt numbers returned, in order
    chunk_ids: tuple[str, ...]  # their chunk ids, as strings
    latency_ms: float


class TurnTool:
    """The retrieve executor for one turn. Build a new one per turn: numbering restarts (AC-4).

    retrieve is ask.retrieve's signature: (conn, embedder, query, principal, k, config_id=...).
    Injected so unit tests pass a fake; production code passes nothing.
    """

    def __init__(
        self,
        conn,
        embedder: Embedder,
        principal: Principal,
        config_id: str = BASELINE_CONFIG,
        retrieve: Callable[..., list[Retrieved]] = ask.retrieve,
        clock: Callable[[], float] = time.perf_counter,
    ):
        self._conn = conn
        self._embedder = embedder
        self._principal = principal
        self._config_id = config_id
        self._retrieve = retrieve
        self._clock = clock
        self._numbers: dict = {}  # chunk_id -> per-turn number
        self._shown: dict[int, Retrieved] = {}  # n -> excerpt
        self._seen: set[tuple[str, int]] = set()  # accepted (query, page)

    @property
    def excerpts(self) -> list[Retrieved]:
        """Every excerpt shown this turn, n = its per-turn number, ordered by n. Pass to
        ask.parse_citations (AC-15)."""
        return [self._shown[n] for n in sorted(self._shown)]

    def _reject(self, reason: str) -> ToolResult:
        return ToolResult(f"Error: {reason}", False, reason, (), (), 0.0)

    def _validate(self, call: ToolCall) -> tuple[str, int] | str:
        """(query, page) for a valid call, else the rejection reason."""
        if call.name != TOOL_NAME:
            return f"unknown tool {call.name!r}. The only tool is {TOOL_NAME}; call it instead."
        try:
            args = json.loads(call.arguments)
        except ValueError:
            return 'arguments are not valid JSON. Send {"query": "...", "page": 1}.'
        if not isinstance(args, dict):
            return 'arguments must be a JSON object. Send {"query": "...", "page": 1}.'
        extra = sorted(set(args) - _KEYS)
        if extra:
            return (
                f"unexpected argument(s): {', '.join(extra)}. Send only query and page; "
                "the search always runs with your own access."
            )
        missing = sorted(_KEYS - set(args))
        if missing:
            return f"missing argument(s): {', '.join(missing)}. Send both query and page."
        query, page = args["query"], args["page"]
        if not isinstance(query, str):
            return "query must be a string. Send a short text query."
        if not isinstance(page, int) or isinstance(page, bool):
            return f"page must be an integer from 1 to {AGENT_PAGES}. Resend with a valid page."
        if not 1 <= page <= AGENT_PAGES:
            return f"page must be from 1 to {AGENT_PAGES}, got {page}. Resend with a valid page."
        query = query.strip()
        if not query:
            return "query is empty. Send a non-empty search query."
        tokens = len(tiktoken.get_encoding(TOKENIZER).encode(query, disallowed_special=()))
        if tokens > AGENT_MAX_QUERY_TOKENS:
            return (
                f"query is {tokens} tokens, over the limit of {AGENT_MAX_QUERY_TOKENS}. "
                "Resend a shorter query."
            )
        if (query, page) in self._seen:
            return "already shown; use the excerpts above, or reword the query."
        return query, page

    def execute(self, call: ToolCall, time_left: float | None = None) -> ToolResult:
        """Validate, then run one call. Never raises for a malformed call: it returns an error
        ToolResult (AC-11). Errors from the retriever or database propagate.

        time_left: the turn's remaining seconds. The query embed's retry waits may not pass it:
        a wait that would raises ToolTimeout instead of sleeping (AC-8)."""
        checked = self._validate(call)
        if isinstance(checked, str):
            return self._reject(checked)
        query, page = checked
        start = self._clock()
        extra = {}
        if time_left is not None:

            def sleep(seconds: float) -> None:
                if self._clock() - start + seconds >= time_left:
                    raise ToolTimeout(f"a {seconds:.1f} s retry wait would pass the turn's time")
                time.sleep(seconds)

            extra["sleep"] = sleep
        found = self._retrieve(
            self._conn,
            self._embedder,
            query,
            self._principal,
            k=TOP_K * page,
            config_id=self._config_id,
            **extra,
        )
        window = found[TOP_K * (page - 1) : TOP_K * page]
        shown = []
        for r in window:
            n = self._numbers.setdefault(r.chunk_id, len(self._numbers) + 1)
            shown.append(replace(r, n=n))
            self._shown.setdefault(n, shown[-1])
        self._seen.add((query, page))
        latency_ms = (self._clock() - start) * 1000
        content = _format(shown) if shown else EMPTY_PAGE
        return ToolResult(
            content,
            True,
            None,
            tuple(r.n for r in shown),
            tuple(str(r.chunk_id) for r in shown),
            latency_ms,
        )


__all__ = [
    "AGENT_PAGES",
    "EMPTY_PAGE",
    "TOOL",
    "TOOL_NAME",
    "ToolResult",
    "ToolTimeout",
    "TurnTool",
]

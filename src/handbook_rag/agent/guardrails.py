"""Deterministic guardrails for the agent (spec 0014).

One typed, versioned policy (AC-1), guardrail events for the turn record (AC-2), and pure check
functions: input (AC-3, AC-4), excerpt framing helpers (AC-5), the final-answer check and retry
feedback (AC-7, AC-8), links and images (AC-9), PII (AC-10) and record redaction (AC-11).

No I/O and no network client here (AC-13). Old policy versions live in git history; a turn's
`guardrails_sha256` identifies the exact rules that ran (ADR-0025).
"""

import copy
import dataclasses
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from urllib.parse import urlsplit

import tiktoken

from handbook_rag.constants import TOKENIZER

# --- AC-2: events -------------------------------------------------------------------------------

STAGES = ("input", "excerpt", "output", "persist")
ACTIONS = ("pass", "flag", "redact", "retry", "block")

# Every check that can record an event, with its stage.
CHECKS: dict[str, str] = {
    "input_invisible": "input",
    "input_empty": "input",
    "input_length": "input",
    "input_garbage": "input",
    "input_injection": "input",
    "input_pii": "input",  # D4: PII redacted from the question before the model call
    "excerpt_invisible": "excerpt",
    "excerpt_delimiter": "excerpt",
    "excerpt_injection": "excerpt",
    "output_citation": "output",
    "output_image": "output",
    "output_link": "output",
    "output_pii": "output",
    "persist_pii": "persist",
}

# AC-12: the reasons a turn can end guardrail_blocked.
BLOCK_REASONS = ("input_empty", "input_too_long", "input_garbage", "citation_check_failed")
# AC-7: the final-answer failures that trigger a retry (or a block when none is possible).
CITATION_REASONS = ("citation_out_of_range", "citation_missing", "abstention_format")

# AC-4: the injection patterns, (reason, regex source). Matched with re.IGNORECASE against
# detection_view(text). Claimed identity is deliberately not a pattern.
INJECTION_PATTERNS: tuple[tuple[str, str], ...] = (
    (
        "override_instructions",
        r"\b(ignore|disregard|forget|override)\b[^.\n]{0,40}\b(previous|prior|above|earlier|"
        r"preceding|all|your|system)\b[^.\n]{0,20}\b(instructions?|prompts?|rules|directions)\b",
    ),
    (
        "prompt_extraction",
        r"\b(reveal|print|repeat|show|output|display|leak)\b[^.\n]{0,30}\b(your|the)\s+"
        r"(system\s+prompt|instructions|initial\s+prompt|hidden\s+prompt)\b",
    ),
    ("role_switch", r"\byou\s+are\s+now\s+(a|an|the|in|my)\b"),
    ("mode_switch", r"\b(developer|jailbreak|god|dan)\s+mode\b|\bdo\s+anything\s+now\b"),
    ("fake_role_marker", r"(?m)^\s*(system|assistant|developer)\s*:"),
    ("delimiter_marker", r"</?\s*excerpt\b"),
)

# Invisible characters stripped from questions and excerpts (AC-3, AC-5): (first, last) inclusive.
INVISIBLE_RANGES: tuple[tuple[int, int], ...] = (
    (0xE0000, 0xE007F),  # tag block
    (0xFE00, 0xFE0F),  # variation selectors
    (0x200B, 0x200D),  # zero-width space, non-joiner, joiner
    (0x2060, 0x2060),  # word joiner
    (0x200E, 0x200F),  # LRM, RLM
    (0x202A, 0x202E),  # bidi embeddings and overrides
    (0x2066, 0x2069),  # bidi isolates
)

PII_ENTITIES = ("email", "phone", "card", "ssn", "iban")

PATTERN_REASONS = tuple(reason for reason, _ in INJECTION_PATTERNS)
REASONS = (
    *BLOCK_REASONS,
    *CITATION_REASONS,
    *PATTERN_REASONS,
    "invisible_chars",
    "delimiter_in_content",
    "image",
    "link",
    "pii",
)


_INJECTION_RX = tuple((r, re.compile(src, re.IGNORECASE)) for r, src in INJECTION_PATTERNS)
_DELIMITER_RX = re.compile(r"<(/?\s*excerpt)", re.IGNORECASE)
# Bracketed text allowing one level of nested brackets, e.g. ![a [b]](...) (review fix).
_BRACKETED = r"\[(?P<text>(?:[^\[\]]|\[[^\[\]]*\])*)\]"
_IMAGE_RX = re.compile(
    r"!" + _BRACKETED.replace("?P<text>", "?:") + r"\((?P<md>[^)]*)\)|<img\b[^>]*>",
    re.IGNORECASE,
)
# A link target that leaves the handbook: any scheme (https:, mailto:, javascript:, data:),
# protocol-relative //host, or www. Relative /handbook/ paths stay (D7, review fix).
_EXTERNAL = r"(?:[a-z][a-z0-9+.-]*:|//|www\.)"
_MD_LINK_RX = re.compile(_BRACKETED + r"\((?P<url>" + _EXTERNAL + r"[^)]*)\)", re.IGNORECASE)
_BARE_URL_RX = re.compile(
    r"\b(?:https?://|www\.)[^\s<>()\[\]]+|(?<![\w:/])//[\w-]+(?:\.[\w-]+)+[^\s<>()\[\]\"']*",
    re.IGNORECASE,
)
_IMG_SRC_RX = re.compile(r"""src\s*=\s*["']?([^"'\s>]+)""", re.IGNORECASE)


def _is_invisible(c: str) -> bool:
    cp = ord(c)
    return any(lo <= cp <= hi for lo, hi in INVISIBLE_RANGES)


def _encoding() -> tiktoken.Encoding:
    return tiktoken.get_encoding(TOKENIZER)


def _img_src(tag: str) -> str:
    m = _IMG_SRC_RX.search(tag)
    return m[1] if m else ""


def _host(url: str) -> str | None:
    """Lowercase host of an absolute http(s) or www. URL; never the path, query or credentials."""
    url = url.strip()
    if url.lower().startswith("www."):
        url = "http://" + url
    elif url.startswith("//"):
        url = "http:" + url
    if not url.lower().startswith(("http://", "https://")):
        return None
    try:
        return urlsplit(url).hostname
    except ValueError:
        return None


def _removal_event(check: str, reason: str, count: int, hosts: list[str]) -> dict:
    if not count:
        return event(check, "pass")
    return event(check, "redact", reason, count=count, hosts=sorted(set(hosts)))


# --- AC-10: PII detectors -----------------------------------------------------------------------


def _luhn(value: str) -> bool:
    digits = [int(c) for c in value if c.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
    return total % 10 == 0


def _iban(value: str) -> bool:
    s = value.replace(" ", "").upper()
    if not 15 <= len(s) <= 34:
        return False
    rearranged = s[4:] + s[:4]
    number = "".join(str(int(c, 36)) for c in rearranged)
    return int(number) % 97 == 1


def _ssn(value: str) -> bool:
    area, group, serial = value.split("-")
    return (
        area not in ("000", "666")
        and not area.startswith("9")
        and group != "00"
        and (serial != "0000")
    )


def _phone(value: str) -> bool:
    return 9 <= sum(c.isdigit() for c in value) <= 15


# Order matters: IBAN first, since a Luhn-valid digit run can sit inside an IBAN.
_PII_RULES = (
    (
        "iban",
        re.compile(r"\b[A-Za-z]{2}\d{2}(?: ?[A-Za-z0-9]{4}){2,7}(?: ?[A-Za-z0-9]{1,3})?\b"),
        _iban,
    ),
    ("card", re.compile(r"(?<!\d)\d(?:[ -]?\d){12,18}(?!\d)"), _luhn),
    ("ssn", re.compile(r"(?<![\d-])\d{3}-\d{2}-\d{4}(?![\d-])"), _ssn),
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), lambda v: True),
    (
        "phone",
        re.compile(
            r"(?<![\w+])\+\d[\d ().-]{7,}\d(?!\d)"
            r"|(?<![\w.-])\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?![\w-])"
        ),
        _phone,
    ),
)


# --- AC-1: the policy ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GuardrailPolicy:
    """Every guardrail parameter (AC-1). A code constant, recorded per turn, not bound (D8)."""

    version: str
    max_question_tokens: int
    invisible_ranges: tuple[tuple[int, int], ...]
    injection_patterns: tuple[tuple[str, str], ...]
    pii_entities: tuple[str, ...]
    pii_patterns: tuple[tuple[str, str], ...]  # (entity, regex source); validators in code
    link_patterns: tuple[str, ...]  # image, markdown link, bare URL, delimiter regex sources
    max_retries: int
    retry_feedback: str
    link_policy: str  # "none": every URL removed (D7 a)

    def canonical(self) -> str:
        """Canonical JSON: sorted keys, patterns as source strings."""
        return json.dumps(
            dataclasses.asdict(self), sort_keys=True, ensure_ascii=False, separators=(",", ":")
        )

    def sha256(self) -> str:
        return hashlib.sha256(self.canonical().encode()).hexdigest()


def _policy() -> GuardrailPolicy:
    from handbook_rag.prompts import RETRY_FEEDBACK

    return GuardrailPolicy(
        version="guardrails-v1",
        max_question_tokens=500,
        invisible_ranges=INVISIBLE_RANGES,
        injection_patterns=INJECTION_PATTERNS,
        pii_entities=PII_ENTITIES,
        pii_patterns=tuple((entity, rx.pattern) for entity, rx, _ in _PII_RULES),
        link_patterns=tuple(
            rx.pattern for rx in (_IMAGE_RX, _MD_LINK_RX, _BARE_URL_RX, _DELIMITER_RX)
        ),
        max_retries=1,
        retry_feedback=RETRY_FEEDBACK,
        link_policy="none",
    )


POLICY = _policy()


def event(check: str, action: str, reason: str | None = None, **detail) -> dict:
    """One guardrail event (AC-2). stage comes from CHECKS; detail holds counts and types only."""
    assert check in CHECKS, check
    assert action in ACTIONS, action
    if action == "pass":
        assert reason is None, reason
    else:
        assert reason in REASONS, reason
    return {
        "check": check,
        "stage": CHECKS[check],
        "action": action,
        "reason": reason,
        "detail": detail,
    }


def format_events(events: list[dict]) -> str:
    """The CLI line (AC-2): 'guardrails: all passed', or every non-pass event as
    'stage/check action reason ×count', comma-separated."""
    tripped = [e for e in events if e["action"] != "pass"]
    if not tripped:
        return "guardrails: all passed"
    parts = [
        f"{e['stage']}/{e['check']} {e['action']} {e['reason'] or '-'} "
        f"×{e['detail'].get('count', 1)}"
        for e in tripped
    ]
    return "guardrails: " + ", ".join(parts)


# --- AC-3, AC-4: input --------------------------------------------------------------------------


def strip_invisible(text: str) -> tuple[str, int]:
    """Remove every INVISIBLE_RANGES character. Returns (text, number removed)."""
    kept = [c for c in text if not _is_invisible(c)]
    return "".join(kept), len(text) - len(kept)


def decode_tags(text: str) -> str:
    """The ASCII payload hidden in tag-block characters (U+E0020-E007E -> ' '-'~')."""
    return "".join(chr(ord(c) - 0xE0000) for c in text if 0xE0020 <= ord(c) <= 0xE007E)


def detection_view(text: str) -> str:
    """What patterns match against (AC-3): NFKC + casefold of the visible text, then a newline
    and the casefolded decoded tag payload if any. Never sent to the model."""
    view = unicodedata.normalize("NFKC", strip_invisible(text)[0]).casefold()
    payload = decode_tags(text)
    return view + "\n" + payload.casefold() if payload else view


def scan_injection(text: str) -> list[str]:
    """Reasons of the INJECTION_PATTERNS that match detection_view(text), in policy order."""
    view = detection_view(text)
    return [reason for reason, rx in _INJECTION_RX if rx.search(view)]


def check_input(question: str) -> tuple[str, list[dict], str | None]:
    """AC-3 then AC-4 on the raw question. Returns (stripped question, events, block reason or
    None). Order: invisible (redact/pass), empty, too long, garbage (block/pass; stops at the
    first block), injection (flag/pass, one event per matching reason). A pass event for each
    check that ran."""
    events: list[dict] = []
    stripped, removed = strip_invisible(question)
    if removed:
        events.append(event("input_invisible", "redact", "invisible_chars", count=removed))
    else:
        events.append(event("input_invisible", "pass"))

    if not stripped.strip():
        events.append(event("input_empty", "block", "input_empty"))
        return stripped, events, "input_empty"
    events.append(event("input_empty", "pass"))

    tokens = len(_encoding().encode(stripped, disallowed_special=()))
    if tokens > POLICY.max_question_tokens:
        events.append(event("input_length", "block", "input_too_long", tokens=tokens))
        return stripped, events, "input_too_long"
    events.append(event("input_length", "pass"))

    chars = len(stripped)
    odd = sum(1 for c in stripped if not c.isspace() and unicodedata.category(c)[0] == "C")
    no_word = not any(unicodedata.category(c)[0] in "LN" for c in stripped)
    if no_word or odd * 2 > chars:
        events.append(event("input_garbage", "block", "input_garbage"))
        return stripped, events, "input_garbage"
    events.append(event("input_garbage", "pass"))

    reasons = scan_injection(question)
    if reasons:
        events.extend(event("input_injection", "flag", r, count=1) for r in reasons)
    else:
        events.append(event("input_injection", "pass"))
    return stripped, events, None


# --- AC-5: excerpt helpers ----------------------------------------------------------------------


def neutralise_delimiters(text: str) -> tuple[str, int]:
    """Replace '<' with '‹' in every '<excerpt' / '</excerpt' (case-insensitive, any nonce).
    Returns (text, number neutralised)."""
    return _DELIMITER_RX.subn(r"‹\1", text)


# --- AC-7, AC-8: final answer -------------------------------------------------------------------


def final_check(n_valid: int, invalid: list[int], abstained: bool, label: str | None) -> list[str]:
    """The AC-7 reasons this reply fails, in CITATION_REASONS order; [] when it passes."""
    reasons = []
    if invalid:
        reasons.append("citation_out_of_range")
    if not abstained and n_valid == 0:
        reasons.append("citation_missing")
    if label == "abstain+extra":
        reasons.append("abstention_format")
    return reasons


def retry_feedback(reasons: list[str], invalid: list[int], valid_max: int) -> str:
    """The user-role feedback message for a retry (AC-8), built from POLICY.retry_feedback.
    valid_max 0 means no excerpts were shown this turn."""
    problems = {
        "citation_out_of_range": f"citation(s) {sorted(set(invalid))} don't match an excerpt "
        "for this question",
        "citation_missing": "the answer cites no excerpt",
        "abstention_format": "a fixed reply must be sent exactly, with nothing added",
    }
    if valid_max == 0:
        valid = "no excerpts yet: search first"
    elif valid_max == 1:
        valid = "[1]"
    else:
        valid = f"[1]–[{valid_max}]"
    problem = "; ".join(problems[r] for r in reasons)
    return POLICY.retry_feedback.format(problem=problem, valid=valid)


# --- AC-9: links and images ---------------------------------------------------------------------


def strip_links(text: str) -> tuple[str, list[dict]]:
    """Remove images ('[image removed]') and URLs ('[link removed]'; a markdown link keeps its
    text). Relative /handbook/ paths stay. Returns (text, events): one output_image and one
    output_link event, pass or redact with detail {count, hosts}."""
    image_hosts: list[str] = []
    images = 0

    def image(m: re.Match) -> str:
        nonlocal images
        images += 1
        if host := _host(m.group("md") if m.group("md") is not None else _img_src(m[0])):
            image_hosts.append(host)
        return "[image removed]"

    text = _IMAGE_RX.sub(image, text)

    link_hosts: list[str] = []
    links = 0

    def link(m: re.Match) -> str:
        nonlocal links
        links += 1
        if host := _host(m["url"]):
            link_hosts.append(host)
        return f"{m['text']} [link removed]"

    text = _MD_LINK_RX.sub(link, text)

    def bare(m: re.Match) -> str:
        nonlocal links
        url = m[0].rstrip(".,;:!?'\"")
        links += 1
        if host := _host(url):
            link_hosts.append(host)
        return "[link removed]" + m[0][len(url) :]

    text = _BARE_URL_RX.sub(bare, text)
    events = [
        _removal_event("output_image", "image", images, image_hosts),
        _removal_event("output_link", "link", links, link_hosts),
    ]
    return text, events


# --- AC-10, AC-11: PII --------------------------------------------------------------------------


_SEPARATORS = " -.()/"


def _valid_end(view: str, start: int, end: int, rx: re.Pattern, valid) -> int | None:
    """The end of the longest valid candidate in view[start:end]: the whole match, else the
    match cut just before a separator (review fix: '4111 1111 1111 1111 12/25' has a valid card
    inside a longer span that fails Luhn). A candidate must still fully match the rule's regex
    before its validator runs. None if no candidate is valid."""
    ends = [end] + [i for i in range(end - 1, start, -1) if view[i] in _SEPARATORS]
    for e in ends:
        candidate = view[start:e].rstrip(_SEPARATORS)
        if candidate and rx.fullmatch(candidate) and valid(candidate):
            return start + len(candidate)
    return None


def redact_pii(
    text: str, keep: str = "", allow_gitlab_email: bool = False
) -> tuple[str, dict[str, int]]:
    """Replace each PII_ENTITIES match with '[redacted:<entity>]'. A match found verbatim in
    `keep` (this turn's excerpt text) is kept; so are @gitlab.com emails when allow_gitlab_email.
    Card needs Luhn, IBAN needs mod-97. Detection runs on an NFKC copy (AC-3). Returns
    (text, {entity: count}) for redacted values only."""
    # Detection runs on an NFKC view built one character at a time, so every view position maps
    # back to its source character; replacements are made in the original text, which is never
    # normalised (AC-3: quoted figures such as "½" stay as written).
    pieces = [unicodedata.normalize("NFKC", ch) for ch in text]
    view = "".join(pieces)
    origin = [i for i, piece in enumerate(pieces) for _ in piece]
    keeps = (keep, unicodedata.normalize("NFKC", keep))
    counts: dict[str, int] = {}
    claimed: list[tuple[int, int, str | None]] = []  # view spans; entity None = kept

    def free(a: int, b: int) -> bool:
        return all(b <= s or a >= e for s, e, _ in claimed)

    for entity, rx, valid in _PII_RULES:
        if entity not in POLICY.pii_entities:
            continue
        for m in rx.finditer(view):
            end = _valid_end(view, m.start(), m.end(), rx, valid)
            if end is None or not free(m.start(), end):
                continue
            value = view[m.start() : end]
            kept = any(value in k for k in keeps) or (
                entity == "email" and allow_gitlab_email and value.lower().endswith("@gitlab.com")
            )
            claimed.append((m.start(), end, None if kept else entity))
            if not kept:
                counts[entity] = counts.get(entity, 0) + 1
    if not counts:
        return text, counts
    out, pos = [], 0
    for a, b, entity in sorted(claimed):
        if entity is None:
            continue
        start, stop = origin[a], origin[b - 1] + 1
        out += [text[pos:start], f"[redacted:{entity}]"]
        pos = stop
    out.append(text[pos:])
    return "".join(out), counts


def redact_record(record: dict, keep: str) -> dict:
    """A redacted deep copy for save and print (AC-11). No exemption: question, user-role
    message content, tool-call argument strings (messages and steps), error.message. Excerpt
    exemption (`keep`): assistant-role content and answer. Tool-role content untouched (AC-6)."""
    out = copy.deepcopy(record)
    total: dict[str, int] = {}

    def red(container, key: str, exempt: bool = False) -> None:
        value = container.get(key) if isinstance(container, dict) else None
        if not isinstance(value, str):
            return
        container[key], counts = redact_pii(value, keep if exempt else "")
        for entity, n in counts.items():
            total[entity] = total.get(entity, 0) + n

    red(out, "question")
    for msg in out.get("messages") or []:
        role = msg.get("role")
        if role == "user":
            red(msg, "content")
        elif role == "assistant":
            red(msg, "content", exempt=True)
            for call in msg.get("tool_calls") or []:
                red(call.get("function") or {}, "arguments")
    for step in out.get("steps") or []:
        if step.get("kind") == "tool":
            red(step, "arguments")
    if isinstance(out.get("error"), dict):
        red(out["error"], "message")
    red(out, "answer", exempt=True)

    events = [e for e in out.get("guardrail_events") or [] if e.get("check") != "persist_pii"]
    if total:
        events.append(event("persist_pii", "redact", "pii", **total, count=sum(total.values())))
    else:
        events.append(event("persist_pii", "pass"))
    out["guardrail_events"] = events
    return out

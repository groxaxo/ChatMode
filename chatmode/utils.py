from typing import Callable, Dict, List

PLACEHOLDERS = [
    "$SELF_PROMPT",
    "$MEMORY",
    "$STATS",
    "$INVENTORY",
    "$COMMAND_DOCS",
    "$EXAMPLES",
    "$CODE_DOCS",
]


def clean_placeholders(text: str) -> str:
    for placeholder in PLACEHOLDERS:
        text = text.replace(placeholder, "")
    return text


def approximate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, int(len(text) / 4))


def trim_messages_to_context(
    messages: List[Dict[str, str]],
    max_tokens: int,
    token_counter: Callable[[str], int],
) -> List[Dict[str, str]]:
    trimmed = list(messages)
    total_tokens = sum(token_counter(msg.get("content", "")) for msg in trimmed)
    while trimmed and total_tokens > max_tokens:
        removed = trimmed.pop(1 if len(trimmed) > 1 else 0)
        total_tokens -= token_counter(removed.get("content", ""))
    return trimmed

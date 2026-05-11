"""Normalize LaTeX delimiter styles (e.g. ChatGPT / LLM output) for dollarmath."""

from __future__ import annotations

import re

# Split markdown into fenced code blocks (``` ... ```) and everything else.
_FENCE_SPLIT = re.compile(r"(```[\s\S]*?```)")


def normalize_llm_latex_delimiters(markdown: str) -> str:
    """Convert ``\\( \\)`` / ``\\[ \\]`` style math into ``$...$`` / ``$$...$$``.

    Many LLMs (including ChatGPT-style assistants) emit LaTeX with ``\\(...\\)`` for inline and
    ``\\[...\\]`` for display math. Our renderer uses ``mdit-py-plugins`` dollarmath, which parses
    dollar delimiters.

    **Skipped:** triple-backtick fenced code blocks are left untouched so examples like
    ``\\frac{a}{b}`` inside code are not turned into math.

    Multiline ``\\(...\\)`` is treated as display math (converted to ``$$...$$``), since
    dollar-style inline math is normally single-line.
    """
    parts = _FENCE_SPLIT.split(markdown)
    return "".join(part if part.startswith("```") else _convert_brackets(part) for part in parts)


def _convert_brackets(segment: str) -> str:
    # Display math first so nested patterns inside blocks are handled predictably.
    segment = re.sub(
        r"\\\[\s*([\s\S]*?)\\\]",
        lambda m: "$$\n" + m.group(1).strip("\n") + "\n$$",
        segment,
    )
    segment = re.sub(
        r"\\\(\s*([\s\S]*?)\\\)",
        _inline_or_display_replacement,
        segment,
    )
    return segment


def _inline_or_display_replacement(match: re.Match[str]) -> str:
    inner = match.group(1)
    stripped = inner.strip()
    if "\n" in stripped:
        return "$$\n" + stripped + "\n$$"
    return "$" + stripped + "$"

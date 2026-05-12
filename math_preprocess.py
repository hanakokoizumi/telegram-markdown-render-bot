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

    When needed, an extra newline is inserted before ``$$`` so block math starts a new
    CommonMark paragraph (mdit ``math_block`` requires ``$$`` at the beginning of a block).
    """
    parts = _FENCE_SPLIT.split(markdown)
    return "".join(part if part.startswith("```") else _convert_brackets(part) for part in parts)


def _blank_line_before_display_dollar(prefix: str) -> str:
    """Block ``$$`` in mdit-py-plugins must start a new CommonMark block.

    If the previous line is non-empty and only one newline separates it from ``$$``,
    the ``$$`` line is merged into the paragraph: display math is not recognized,
    ``=`` inside math can trigger setext headings, and stray ``$`` may appear next
    to inline math spans.
    """
    if not prefix.strip():
        return ""
    tail = prefix.rstrip(" \t")
    if tail.endswith("\n\n"):
        return ""
    if tail.endswith("\n"):
        return "\n"
    return "\n\n"


def _convert_brackets(segment: str) -> str:
    # Display math first so nested patterns inside blocks are handled predictably.
    def _display_repl(m: re.Match[str]) -> str:
        inner = m.group(1).strip("\n")
        pad = _blank_line_before_display_dollar(segment[: m.start()])
        return pad + "$$\n" + inner + "\n$$"

    segment = re.sub(r"\\\[\s*([\s\S]*?)\\\]", _display_repl, segment)
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
        pad = _blank_line_before_display_dollar(match.string[: match.start()])
        return pad + "$$\n" + stripped + "\n$$"
    return "$" + stripped + "$"

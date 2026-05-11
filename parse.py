"""Parse `/md [width]` commands and extract Markdown source."""

from __future__ import annotations

import re
from dataclasses import dataclass

_MD_CMD_RE = re.compile(r"^/md(?:@\S+)?\s*", re.MULTILINE)


@dataclass(frozen=True)
class ParsedRenderCommand:
    width: int
    """Width in CSS pixels (already clamped)."""

    markdown: str
    """Markdown body; may be empty if caller should fall back to replied message."""


def strip_render_command_prefix(text: str) -> str:
    """Remove leading `/md` or `/md@botname` prefix."""
    if not text:
        return ""
    m = _MD_CMD_RE.match(text)
    return text[m.end() :] if m else text


def clamp_width(
    width: int,
    *,
    min_width: int,
    max_width: int,
) -> int:
    if width < min_width:
        return min_width
    if width > max_width:
        return max_width
    return width


def parse_render_command(
    text: str,
    *,
    default_width: int,
    min_width: int,
    max_width: int,
) -> ParsedRenderCommand:
    """Parse optional width and Markdown from text after the `/md` command."""
    rest = strip_render_command_prefix(text).lstrip()
    if not rest:
        return ParsedRenderCommand(
            width=default_width,
            markdown="",
        )

    lines = rest.split("\n", 1)
    first_line = lines[0].strip()

    if first_line.isdigit():
        w = clamp_width(int(first_line), min_width=min_width, max_width=max_width)
        if len(lines) > 1:
            return ParsedRenderCommand(width=w, markdown=lines[1].lstrip("\n"))
        return ParsedRenderCommand(width=w, markdown="")

    parts = rest.split(None, 1)
    if parts and parts[0].isdigit():
        w = clamp_width(int(parts[0]), min_width=min_width, max_width=max_width)
        body = parts[1] if len(parts) > 1 else ""
        return ParsedRenderCommand(width=w, markdown=body)

    return ParsedRenderCommand(width=default_width, markdown=rest)


def extract_reply_markdown(reply) -> str:
    """Best-effort plain text from a replied-to message."""
    if reply is None:
        return ""
    text = getattr(reply, "text", None) or getattr(reply, "caption", None) or ""
    return text or ""

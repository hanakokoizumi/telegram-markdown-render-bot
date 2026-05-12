"""Parse `/md [options]` commands and extract Markdown source."""

from __future__ import annotations

import re
from dataclasses import dataclass

_MD_CMD_RE = re.compile(r"^/md(?:@\S+)?\s*", re.MULTILINE)

# Playwright device_scale_factor：与首行 `-l` / `-m` / `-h` 对应（档位 1～3）。
RENDER_QUALITY_RATIOS: tuple[float, float, float] = (1.0, 2.0, 3.0)


@dataclass(frozen=True)
class ParsedRenderCommand:
    width: int
    """Width in CSS pixels (already clamped)."""

    markdown: str
    """Markdown body; may be empty if caller should fall back to replied message."""

    send_as_photo: bool
    """True：图片消息（`-p`）；False：文件（`-f`）。默认 True。"""

    render_pixel_ratio: float
    """由 `-l` / `-m` / `-h` 决定，对应 RENDER_QUALITY_RATIOS。"""


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


def _parse_first_line_options(first_line: str) -> tuple[int | None, bool | None, int | None, str]:
    """Parse optional width / flags from the first line; return remainder of that line for markdown."""
    tokens = first_line.split()
    if not tokens:
        return None, None, None, ""

    i = 0
    width: int | None = None
    send_as_photo: bool | None = None
    quality: int | None = None

    while i < len(tokens):
        t = tokens[i]
        if t == "-f":
            send_as_photo = False
            i += 1
        elif t == "-p":
            send_as_photo = True
            i += 1
        elif t == "-l":
            quality = 1
            i += 1
        elif t == "-m":
            quality = 2
            i += 1
        elif t == "-h":
            quality = 3
            i += 1
        elif t.isdigit() and width is None:
            width = int(t)
            i += 1
        else:
            break

    remainder = " ".join(tokens[i:])
    return width, send_as_photo, quality, remainder


def parse_render_command(
    text: str,
    *,
    default_width: int,
    min_width: int,
    max_width: int,
) -> ParsedRenderCommand:
    """Parse optional width、首行参数与 Markdown。"""
    rest = strip_render_command_prefix(text).lstrip()
    if not rest:
        return ParsedRenderCommand(
            width=clamp_width(default_width, min_width=min_width, max_width=max_width),
            markdown="",
            send_as_photo=True,
            render_pixel_ratio=RENDER_QUALITY_RATIOS[0],
        )

    lines = rest.split("\n", 1)
    first_line = lines[0].strip()
    tail = lines[1].lstrip("\n") if len(lines) > 1 else ""

    w_opt, photo_opt, quality_opt, first_remainder = _parse_first_line_options(first_line)

    if first_remainder:
        markdown = first_remainder if not tail else f"{first_remainder}\n{tail}"
    else:
        markdown = tail

    width = clamp_width(
        w_opt if w_opt is not None else default_width,
        min_width=min_width,
        max_width=max_width,
    )
    send_as_photo = True if photo_opt is None else photo_opt
    tier = quality_opt if quality_opt is not None else 1
    ratio = RENDER_QUALITY_RATIOS[tier - 1]

    return ParsedRenderCommand(
        width=width,
        markdown=markdown,
        send_as_photo=send_as_photo,
        render_pixel_ratio=ratio,
    )


def extract_reply_markdown(reply) -> str:
    """Best-effort plain text from a replied-to message."""
    if reply is None:
        return ""
    text = getattr(reply, "text", None) or getattr(reply, "caption", None) or ""
    return text or ""

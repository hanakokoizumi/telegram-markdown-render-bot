"""Unit tests for `/md` parsing helpers."""

from __future__ import annotations

from types import SimpleNamespace

from parse import (
    extract_reply_markdown,
    parse_render_command,
    strip_render_command_prefix,
)


def test_strip_prefix_basic() -> None:
    assert strip_render_command_prefix("/md # hi") == "# hi"
    assert strip_render_command_prefix("/md@SomeBot # hi") == "# hi"


def test_parse_width_first_line_multiline() -> None:
    parsed = parse_render_command(
        "/md\n1200\n# Title\n",
        default_width=500,
        min_width=320,
        max_width=2000,
    )
    assert parsed.width == 1200
    assert parsed.markdown == "# Title\n"


def test_parse_width_first_token_single_line() -> None:
    parsed = parse_render_command(
        "/md 640 ## Hello",
        default_width=500,
        min_width=320,
        max_width=2000,
    )
    assert parsed.width == 640
    assert parsed.markdown == "## Hello"


def test_parse_clamp_width() -> None:
    parsed = parse_render_command(
        "/md 50\nok",
        default_width=500,
        min_width=320,
        max_width=2000,
    )
    assert parsed.width == 320


def test_parse_no_width_uses_default() -> None:
    parsed = parse_render_command(
        "/md # Hello\nworld",
        default_width=500,
        min_width=320,
        max_width=2000,
    )
    assert parsed.width == 500
    assert parsed.markdown == "# Hello\nworld"


def test_extract_reply_markdown() -> None:
    reply = SimpleNamespace(text="from text", caption=None)
    assert extract_reply_markdown(reply) == "from text"

    reply2 = SimpleNamespace(text=None, caption="from caption")
    assert extract_reply_markdown(reply2) == "from caption"

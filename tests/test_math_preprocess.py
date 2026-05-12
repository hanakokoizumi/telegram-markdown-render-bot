"""Tests for ChatGPT / LLM-style LaTeX delimiter normalization."""

from math_preprocess import normalize_llm_latex_delimiters


def test_bracket_display_to_dollars() -> None:
    s = r"See \[ x^2 + y^2 = r^2 \] end."
    out = normalize_llm_latex_delimiters(s)
    assert "$$" in out
    assert "x^2" in out


def test_paren_inline_to_dollars() -> None:
    s = r"Euler \( e^{i\pi}+1=0 \) here."
    out = normalize_llm_latex_delimiters(s)
    assert "Euler $" in out and "+1=0$ here" in out


def test_skips_fenced_code() -> None:
    md = "```\n\\[ a \\]\n```\nouter \\( b \\)"
    out = normalize_llm_latex_delimiters(md)
    assert "\\[ a \\]" in out  # unchanged inside fence
    assert "$b$" in out


def test_multiline_paren_becomes_display() -> None:
    # Real newlines in the text (not the two-char ``\\n`` in a raw string).
    s = "Before \\(\nx +\ny\n\\) after."
    out = normalize_llm_latex_delimiters(s)
    assert "$$" in out
    assert "x +" in out


def test_display_after_text_gets_blank_line_for_block_math() -> None:
    """``$$`` must not sit on the paragraph-continuation line (setext / inline ``$`` bugs)."""
    s = "通常假设：\n\\[\na\n=\nb\n\\]"
    out = normalize_llm_latex_delimiters(s)
    assert "通常假设：\n\n$$" in out


def test_display_after_blank_line_not_double_spaced() -> None:
    s = "Intro\n\n\\[\nx\n\\]"
    out = normalize_llm_latex_delimiters(s)
    assert "Intro\n\n$$" in out
    assert "Intro\n\n\n\n$$" not in out

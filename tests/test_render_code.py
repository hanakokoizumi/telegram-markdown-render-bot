"""Fence blocks: Pygments highlighting + wrapping CSS (see render integration tests via HTML)."""

from __future__ import annotations

from render import markdown_to_html_fragment


def test_fence_python_has_pygments_styles() -> None:
    md = """```python
def x():
    return 1
```
"""
    html = markdown_to_html_fragment(md)
    assert "<pre>" in html and '<code class="language-python">' in html
    assert "style=" in html  # noclasses HtmlFormatter


def test_fence_wrap_css_applies_via_template() -> None:
    """Regression guard: full HTML template includes pre-wrap for code blocks."""
    from render import _build_full_html

    html = _build_full_html("<pre>x</pre>", 400)
    assert "white-space: pre-wrap" in html
    assert "overflow-wrap: anywhere" in html


def test_long_line_wrap_rules_present() -> None:
    from render import _build_full_html

    html = _build_full_html("", 400)
    assert "pre-wrap" in html
    assert "#content pre code" in html

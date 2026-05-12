"""Markdown → HTML (KaTeX-ready) → PNG via Playwright."""

from __future__ import annotations

import json
from typing import Any

from markdown_it import MarkdownIt
from mdit_py_plugins.dollarmath import dollarmath_plugin
from playwright.async_api import Browser, async_playwright
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexer import Lexer
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.util import ClassNotFound

from config import DEFAULT_RENDER_PIXEL_RATIO
from math_preprocess import normalize_llm_latex_delimiters

_KATEX_VERSION = "0.16.11"

# Light-background theme; inline styles so screenshots need no extra Pygments CSS file.
_PYGMENTS_STYLE = "friendly"


def _fence_lexer(code: str, lang_name: str) -> Lexer:
    name = (lang_name or "").strip()
    if name:
        try:
            return get_lexer_by_name(name, stripall=False)
        except ClassNotFound:
            pass
    if not code.strip():
        return get_lexer_by_name("text")
    try:
        return guess_lexer(code)
    except ClassNotFound:
        return get_lexer_by_name("text")


def _pygments_fence_highlight(code: str, lang_name: str, _attrs: str) -> str | None:
    """markdown-it `fence` hook: return highlighted HTML fragment for `<code>` inner HTML."""
    try:
        lexer = _fence_lexer(code, lang_name)
        formatter = HtmlFormatter(
            nowrap=True,
            noclasses=True,
            style=_PYGMENTS_STYLE,
        )
        return highlight(code, lexer, formatter)
    except Exception:
        return None


def _build_markdown_it() -> MarkdownIt:
    md = MarkdownIt(
        "commonmark",
        {
            "breaks": True,
            "html": False,
            "linkify": False,
            "highlight": _pygments_fence_highlight,
        },
    )
    md.enable(["table", "strikethrough"])
    md.use(
        dollarmath_plugin,
        allow_labels=True,
        allow_space=True,
        allow_digits=False,
        allow_blank_lines=True,
    )
    return md


_MD = _build_markdown_it()


def markdown_to_html_fragment(markdown: str) -> str:
    """Render Markdown to an HTML fragment safe to embed in the page body."""
    normalized = normalize_llm_latex_delimiters(markdown)
    return _MD.render(normalized)


def _build_full_html(body_html: str, content_width_px: int) -> str:
    body_json = json.dumps(body_html, ensure_ascii=False)
    width_expr = str(int(content_width_px))
    # After KaTeX renders, `.math` nodes may contain nested elements; we replace each
    # container's text with rendered output.
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link rel="stylesheet"
        href="https://cdn.jsdelivr.net/npm/katex@{_KATEX_VERSION}/dist/katex.min.css" />
  <link rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&amp;display=swap" />
  <style>
    :root {{
      --pad: 16px;
    }}
    html, body {{
      margin: 0;
      padding: 0;
      background: #ffffff;
      color: #111827;
    }}
    #content {{
      box-sizing: border-box;
      width: {width_expr}px;
      max-width: {width_expr}px;
      padding: var(--pad);
      font-family: "Noto Serif SC", "Source Han Serif SC", "Source Han Serif CN",
        ui-sans-serif, system-ui, -apple-system, "PingFang SC", "Microsoft YaHei",
        Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji";
      font-size: 16px;
      line-height: 1.55;
      overflow-wrap: anywhere;
      word-break: break-word;
    }}
    #content h1, #content h2, #content h3 {{
      line-height: 1.25;
      margin: 0.9em 0 0.45em;
    }}
    #content h1 {{ font-size: 1.75rem; }}
    #content h2 {{ font-size: 1.45rem; }}
    #content h3 {{ font-size: 1.2rem; }}
    #content p {{ margin: 0.55em 0; }}
    #content ul, #content ol {{ margin: 0.55em 0 0.55em 1.25rem; padding: 0; }}
    #content blockquote {{
      margin: 0.75em 0;
      padding: 0.25em 0.85em;
      border-left: 4px solid #e5e7eb;
      color: #374151;
      background: #f9fafb;
    }}
    #content code {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono",
        "Courier New", monospace;
      font-size: 0.92em;
      background: #f3f4f6;
      padding: 0.12em 0.35em;
      border-radius: 4px;
    }}
    #content pre {{
      background: #f3f4f6;
      padding: 12px 14px;
      border-radius: 8px;
      margin: 0.75em 0;
      white-space: pre-wrap;
      word-break: break-word;
      overflow-wrap: anywhere;
      overflow-x: hidden;
    }}
    #content pre code {{
      background: transparent;
      padding: 0;
      border-radius: 0;
      white-space: pre-wrap;
      word-break: break-word;
      overflow-wrap: anywhere;
      display: block;
    }}
    #content table {{
      border-collapse: collapse;
      width: 100%;
      margin: 0.75em 0;
      font-size: 0.95em;
    }}
    #content th, #content td {{
      border: 1px solid #e5e7eb;
      padding: 6px 8px;
      vertical-align: top;
    }}
    #content th {{
      background: #f9fafb;
      font-weight: 600;
    }}
    #content img {{
      max-width: 100%;
      height: auto;
    }}
    #content hr {{
      border: none;
      border-top: 1px solid #e5e7eb;
      margin: 1em 0;
    }}
    /* mdit-py-plugins dollarmath output */
    #content .math.block {{
      margin: 0.75em 0;
      overflow-x: auto;
    }}
    #content .mathlabel {{
      float: right;
      opacity: 0.55;
      font-size: 0.85em;
    }}
  </style>
  <script defer src="https://cdn.jsdelivr.net/npm/katex@{_KATEX_VERSION}/dist/katex.min.js"></script>
</head>
<body>
  <div id="content"></div>
  <script>
    const bodyHtml = {body_json};
    document.getElementById("content").innerHTML = bodyHtml;

    function renderAllMath() {{
      if (!window.katex) return;

      const inlineSpans = document.querySelectorAll("#content span.math.inline");
      inlineSpans.forEach((el) => {{
        const tex = el.textContent || "";
        try {{
          katex.render(tex, el, {{ displayMode: false, throwOnError: false }});
        }} catch (e) {{
          el.textContent = tex;
        }}
      }});

      const displayBlocks = document.querySelectorAll("#content div.math.block, #content div.math.inline");
      displayBlocks.forEach((el) => {{
        const tex = el.textContent || "";
        try {{
          katex.render(tex, el, {{ displayMode: true, throwOnError: false }});
        }} catch (e) {{
          el.textContent = tex;
        }}
      }});
    }}

    const waitKatex = () => new Promise((resolve) => {{
      if (window.katex) return resolve();
      const s = document.querySelector('script[src*="katex.min.js"]');
      if (s) s.addEventListener("load", () => resolve());
      else resolve();
    }});

    waitKatex().then(() => {{
      renderAllMath();
      window.__RENDER_DONE__ = true;
    }});
  </script>
</body>
</html>
"""


async def render_markdown_png(
    browser: Browser,
    markdown: str,
    *,
    content_width_px: int,
    pixel_ratio: float = DEFAULT_RENDER_PIXEL_RATIO,
) -> bytes:
    """Render Markdown to a PNG byte string."""
    if content_width_px < 1:
        raise ValueError("content_width_px must be positive")

    fragment = markdown_to_html_fragment(markdown)
    full_html = _build_full_html(fragment, content_width_px)

    page = await browser.new_page(
        device_scale_factor=float(pixel_ratio),
        viewport={
            "width": int(content_width_px + 48),
            "height": 1200,
        },
    )
    try:
        await page.set_content(full_html, wait_until="networkidle")
        await page.wait_for_function("() => window.__RENDER_DONE__ === true")
        # Give fonts/layout a brief moment to settle.
        await page.wait_for_timeout(50)
        element = page.locator("#content")
        png = await element.screenshot(type="png")
        return png
    finally:
        await page.close()


async def create_browser() -> tuple[Any, Browser]:
    """Start Playwright and return (playwright instance, browser). Caller must stop/close."""
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=True)
    return pw, browser


async def shutdown_browser(playwright: Any, browser: Browser) -> None:
    await browser.close()
    await playwright.stop()

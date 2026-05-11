"""Telegram bot wiring (commands, lifecycle)."""

from __future__ import annotations

import logging
from io import BytesIO

from telegram import InputFile, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from config import Settings
from parse import extract_reply_markdown, parse_render_command
from render import create_browser, render_markdown_png, shutdown_browser

logger = logging.getLogger(__name__)


async def _cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None:
        return

    settings: Settings = context.application.bot_data["settings"]
    await message.reply_text(
        "你好！我会把你发来的 Markdown（支持公式与代码高亮）渲染成 PNG 图片。\n\n"
        "用法：\n"
        "• 发送 `/md [宽度]`，在同一条消息里附上正文；或\n"
        "• 先回复某条消息，再发送 `/md [宽度]`，渲染被回复的内容。\n\n"
        f"宽度可选，默认 {settings.default_width}px，范围 {settings.min_width}–{settings.max_width}。\n"
        "单独发送 `/md` 可查看提示。"
    )


async def _cmd_md(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None:
        return

    settings: Settings = context.application.bot_data["settings"]
    browser = context.application.bot_data.get("browser")
    if browser is None:
        logger.error("Browser not initialized")
        await message.reply_text("机器人尚未就绪，请稍后重试。")
        return

    text = message.text or message.caption or ""
    parsed = parse_render_command(
        text,
        default_width=settings.default_width,
        min_width=settings.min_width,
        max_width=settings.max_width,
    )

    markdown = parsed.markdown.strip()
    if not markdown and message.reply_to_message:
        markdown = extract_reply_markdown(message.reply_to_message).strip()

    if not markdown:
        await message.reply_text(
            "用法：\n"
            "• 发送 `/md [宽度]` 并附上 Markdown 正文；或\n"
            "• 回复一条文本消息后发送 `/md [宽度]` 来渲染被回复消息。\n"
            f"宽度可选，默认 {settings.default_width}px，范围 {settings.min_width}–{settings.max_width}。"
        )
        return

    try:
        png_bytes = await render_markdown_png(
            browser,
            markdown,
            content_width_px=parsed.width,
            pixel_ratio=settings.render_pixel_ratio,
        )
    except Exception:
        logger.exception("Render failed")
        await message.reply_text("渲染失败：内部错误（请检查 Markdown/公式语法）。")
        return

    out_file = InputFile(BytesIO(png_bytes), filename="render.png")
    if settings.reply_as_photo:
        await message.reply_photo(photo=out_file)
    else:
        await message.reply_document(document=out_file, filename="render.png")


async def _post_init(application: Application) -> None:
    logging.info("Starting Playwright Chromium…")
    playwright, browser = await create_browser()
    application.bot_data["playwright"] = playwright
    application.bot_data["browser"] = browser
    logging.info("Playwright ready.")


async def _post_shutdown(application: Application) -> None:
    playwright = application.bot_data.get("playwright")
    browser = application.bot_data.get("browser")
    if playwright is not None and browser is not None:
        logging.info("Stopping Playwright…")
        await shutdown_browser(playwright, browser)
    application.bot_data.pop("playwright", None)
    application.bot_data.pop("browser", None)


def build_application(settings: Settings) -> Application:
    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(_post_init)
        .post_shutdown(_post_shutdown)
        .build()
    )
    application.bot_data["settings"] = settings
    application.add_handler(CommandHandler("start", _cmd_start))
    application.add_handler(CommandHandler("md", _cmd_md))
    # `CommandHandler` intentionally ignores captions; support `/md ...` in photo captions.
    application.add_handler(
        MessageHandler(filters.CaptionRegex(r"^/md(?:@\S+)?"), _cmd_md)
    )
    return application

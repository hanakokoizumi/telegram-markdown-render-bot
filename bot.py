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


def _help_text(settings: Settings) -> str:
    return (
        "我会把 Markdown（公式、代码高亮）渲染成 PNG。\n\n"
        "用法：\n"
        "• 发送 `/md …`，同一条消息里写正文；或\n"
        "• 先回复一条消息，再发 `/md …`，渲染被回复的正文。\n\n"
        "首行可写（顺序任意，空格分隔）：\n"
        "• 数字：渲染宽度（CSS 像素），默认 "
        f"{settings.default_width}，范围 {settings.min_width}–{settings.max_width}\n"
        "• `-p`：以图片发送（默认）\n"
        "• `-f`：以文件发送（避免压缩）\n"
        "• `-l` / `-m` / `-h`：清晰度档位 1～3（设备像素比约 1× / 2× / 3×）\n\n"
        "示例：首行写 `800 -f -h` 再换行写正文。\n"
        "也可将一条文本/带说明的媒体**转发**给本机器人，会按上述规则直接渲染正文或说明。\n"
        "命令：`/start` · `/help` · `/md`"
    )


async def _cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None:
        return
    settings: Settings = context.application.bot_data["settings"]
    await message.reply_text(_help_text(settings))


async def _cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None:
        return

    settings: Settings = context.application.bot_data["settings"]
    await message.reply_text("你好！" + _help_text(settings))


async def _render_markdown_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    parse_input_text: str,
    fallback_reply_md: bool = True,
) -> None:
    """用 ``parse_render_command`` 解析 ``parse_input_text``（须含 ``/md`` 前缀语义），并回复渲染结果。"""
    message = update.effective_message
    if message is None:
        return

    settings: Settings = context.application.bot_data["settings"]
    browser = context.application.bot_data.get("browser")
    if browser is None:
        logger.error("Browser not initialized")
        await message.reply_text("机器人尚未就绪，请稍后重试。")
        return

    parsed = parse_render_command(
        parse_input_text,
        default_width=settings.default_width,
        min_width=settings.min_width,
        max_width=settings.max_width,
    )

    markdown = parsed.markdown.strip()
    if not markdown and fallback_reply_md and message.reply_to_message:
        markdown = extract_reply_markdown(message.reply_to_message).strip()

    if not markdown:
        await message.reply_text(
            "当前没有可渲染的正文。发送 `/help` 查看用法，"
            f"或附上 Markdown（默认宽度 {settings.default_width}px）。"
        )
        return

    try:
        png_bytes = await render_markdown_png(
            browser,
            markdown,
            content_width_px=parsed.width,
            pixel_ratio=parsed.render_pixel_ratio,
        )
    except Exception:
        logger.exception("Render failed")
        await message.reply_text("渲染失败：内部错误（请检查 Markdown/公式语法）。")
        return

    out_file = InputFile(BytesIO(png_bytes), filename="render.png")
    if parsed.send_as_photo:
        await message.reply_photo(photo=out_file)
    else:
        await message.reply_document(document=out_file, filename="render.png")


async def _cmd_md(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None:
        return
    text = message.text or message.caption or ""
    await _render_markdown_reply(
        update,
        context,
        parse_input_text=text,
        fallback_reply_md=True,
    )


async def _on_forwarded_markdown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """将转发消息的正文或媒体说明当作 ``/md`` 首行参数 + Markdown 渲染。"""
    message = update.effective_message
    if message is None or message.forward_origin is None:
        return

    raw = message.text or message.caption or ""
    if not raw.strip():
        await message.reply_text("该转发消息没有可渲染的文本或说明。")
        return

    stripped = raw.lstrip()
    parse_input = (
        stripped
        if stripped.startswith("/md") or stripped.startswith("/md@")
        else f"/md\n{raw}"
    )

    await _render_markdown_reply(
        update,
        context,
        parse_input_text=parse_input,
        fallback_reply_md=False,
    )


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
    application.add_handler(CommandHandler("help", _cmd_help))
    # 非转发的 /md 走命令；转发消息由下方 MessageHandler 统一处理，避免重复渲染。
    application.add_handler(CommandHandler("md", _cmd_md, filters=~filters.FORWARDED))
    # `CommandHandler` intentionally ignores captions; support `/md ...` in photo captions.
    application.add_handler(
        MessageHandler(
            filters.CaptionRegex(r"^/md(?:@\S+)?") & ~filters.FORWARDED,
            _cmd_md,
        )
    )
    application.add_handler(
        MessageHandler(filters.FORWARDED & (filters.TEXT | filters.CAPTION), _on_forwarded_markdown)
    )
    return application

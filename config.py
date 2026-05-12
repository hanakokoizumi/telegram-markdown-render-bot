"""Runtime configuration defaults."""

import os
from dataclasses import dataclass


DEFAULT_IMAGE_WIDTH = 500
MIN_IMAGE_WIDTH = 320
MAX_IMAGE_WIDTH = 2000

# `render_markdown_png` 默认设备像素比（调用方未传时使用）。
DEFAULT_RENDER_PIXEL_RATIO = 1.0


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    default_width: int = DEFAULT_IMAGE_WIDTH
    min_width: int = MIN_IMAGE_WIDTH
    max_width: int = MAX_IMAGE_WIDTH


def load_settings() -> Settings:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "Missing TELEGRAM_BOT_TOKEN. Copy .env.example to .env or export the variable."
        )

    return Settings(telegram_bot_token=token)

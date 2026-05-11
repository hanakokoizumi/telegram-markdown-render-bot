"""Runtime configuration defaults."""

import os
from dataclasses import dataclass


DEFAULT_IMAGE_WIDTH = 500
MIN_IMAGE_WIDTH = 320
MAX_IMAGE_WIDTH = 2000

# Playwright：逻辑 CSS 宽度不变，提高 device_scale_factor 可得到更高像素密度的 PNG。
DEFAULT_RENDER_PIXEL_RATIO = 3.0
MIN_RENDER_PIXEL_RATIO = 1.0
MAX_RENDER_PIXEL_RATIO = 4.0


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    default_width: int = DEFAULT_IMAGE_WIDTH
    min_width: int = MIN_IMAGE_WIDTH
    max_width: int = MAX_IMAGE_WIDTH
    render_pixel_ratio: float = DEFAULT_RENDER_PIXEL_RATIO
    # False：以「文件」发送 PNG，避免相册压缩；True：以图片消息发送（客户端预览更好）。
    reply_as_photo: bool = False


def load_settings() -> Settings:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "Missing TELEGRAM_BOT_TOKEN. Copy .env.example to .env or export the variable."
        )

    ratio = _env_float("RENDER_PIXEL_RATIO", DEFAULT_RENDER_PIXEL_RATIO)
    ratio = max(MIN_RENDER_PIXEL_RATIO, min(MAX_RENDER_PIXEL_RATIO, ratio))

    # 默认以文件发送 PNG，避免 sendPhoto 链路压缩；需要相册式预览可设 RENDER_REPLY_AS_PHOTO=1。
    reply_as_photo = _env_bool("RENDER_REPLY_AS_PHOTO", False)

    return Settings(
        telegram_bot_token=token,
        render_pixel_ratio=ratio,
        reply_as_photo=reply_as_photo,
    )

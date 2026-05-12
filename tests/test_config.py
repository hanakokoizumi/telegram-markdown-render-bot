"""Sanity checks for environment-driven settings."""

from __future__ import annotations

import pytest

from config import DEFAULT_IMAGE_WIDTH, load_settings


def test_load_settings_requires_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="TELEGRAM_BOT_TOKEN"):
        load_settings()


def test_load_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "x" * 35)
    s = load_settings()
    assert s.telegram_bot_token == "x" * 35
    assert s.default_width == DEFAULT_IMAGE_WIDTH

"""Sanity checks for environment-driven settings."""

from __future__ import annotations

import os

import pytest

from config import (
    DEFAULT_RENDER_PIXEL_RATIO,
    MAX_RENDER_PIXEL_RATIO,
    MIN_RENDER_PIXEL_RATIO,
    load_settings,
)


def test_render_pixel_ratio_clamped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "x" * 35)
    monkeypatch.setenv("RENDER_PIXEL_RATIO", "99")
    s = load_settings()
    assert s.render_pixel_ratio == MAX_RENDER_PIXEL_RATIO

    monkeypatch.setenv("RENDER_PIXEL_RATIO", "0.1")
    s2 = load_settings()
    assert s2.render_pixel_ratio == MIN_RENDER_PIXEL_RATIO


def test_render_pixel_ratio_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "x" * 35)
    monkeypatch.delenv("RENDER_PIXEL_RATIO", raising=False)
    s = load_settings()
    assert s.render_pixel_ratio == DEFAULT_RENDER_PIXEL_RATIO


def test_reply_as_photo_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "x" * 35)
    monkeypatch.setenv("RENDER_REPLY_AS_PHOTO", "1")
    s = load_settings()
    assert s.reply_as_photo is True

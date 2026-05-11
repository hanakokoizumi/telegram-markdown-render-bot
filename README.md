# telegram-markdown-render-bot

A Telegram bot built with [`python-telegram-bot`](https://github.com/python-telegram-bot/python-telegram-bot) that renders **Markdown** text sent by users (or referenced via reply) into **PNG images**.

## Features

- `/start` — usage overview
- `/md [width]` — render Markdown from the **same message** after the command
- Reply to a text message then send `/md [width]` — render the **replied message** body (`text` or `caption`)
- **Optional width**: clamped to `320..2000`, defaults to `500`
- Supports triggering from **photo captions** starting with `/md`

### Sharpness & delivery

The bot uses Playwright's **device pixel ratio** (`device_scale_factor`) when capturing the PNG; default is **3×**. Adjust it via `RENDER_PIXEL_RATIO` in `.env` (recommended **2–4** — higher is sharper but produces larger files).

PNGs are sent via **`reply_document`** by default, avoiding Telegram's image compression pipeline. Set `RENDER_REPLY_AS_PHOTO=1` to use `reply_photo` if you prefer inline previews at the cost of potential re-compression.

## Quick start (Docker Compose)

### 1) Configure the token

```bash
cp .env.example .env
```

Edit `.env` and fill in your bot token:

```
TELEGRAM_BOT_TOKEN=123456:ABCDEF...
```

Optional settings (see `.env.example`):

```
# RENDER_PIXEL_RATIO=3
# RENDER_REPLY_AS_PHOTO=0
```

### 2) Build and run

```bash
docker compose up -d --build
```

The bot will start in the background. Check logs with:

```bash
docker compose logs -f
```

### 3) Register the bot command (optional)

In BotFather, use `/setcommands` to register **`md`** so it appears in the command panel.

## Development

Set up a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install python-telegram-bot>=21.6 playwright>=1.40 markdown-it-py>=3.0 mdit-py-plugins>=0.4 pygments>=2.17 python-dotenv>=1.0
pip install pytest>=8.0 pytest-asyncio>=0.23
python -m playwright install chromium
```

Run tests:

```bash
pytest
```

## Usage examples

Send:

```text
/md 900
# Heading
$$E=mc^2$$
```

Or send a Markdown message first, then **reply** to it with:

```text
/md 900
```

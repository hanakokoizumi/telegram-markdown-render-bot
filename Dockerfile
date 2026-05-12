FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps first — rarely invalidates later layers.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Only dependency metadata before pip, so editing *.py does not bust this layer.
COPY pyproject.toml ./

RUN pip install --upgrade pip \
    && pip install python-telegram-bot>=21.6 \
                   playwright>=1.40 \
                   markdown-it-py>=3.0 \
                   mdit-py-plugins>=0.4 \
                   pygments>=2.17 \
                   python-dotenv>=1.0

RUN playwright install-deps chromium \
    && playwright install chromium

COPY *.py ./

CMD ["python", "main.py"]

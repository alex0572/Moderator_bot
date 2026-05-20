FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY config/ ./config/
COPY bot/ ./bot/
COPY handlers/ ./handlers/
COPY filters/ ./filters/
COPY logging_config/ ./logging_config/
COPY utils/ ./utils/

RUN mkdir -p /app/logs

CMD ["python", "-m", "bot.main"]

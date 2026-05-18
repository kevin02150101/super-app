# BookFinder production image — Flask + Playwright (Chromium).
FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

# Render injects $PORT
ENV PORT=8000
EXPOSE 8000

CMD gunicorn -w 2 -b 0.0.0.0:${PORT:-8000} --timeout 120 run:app

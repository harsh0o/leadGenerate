FROM python:3.11-slim

WORKDIR /app

# System deps for playwright + curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Fail loudly if browser install fails (LinkedIn channel needs it); do not swallow with || true
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium

# Copy app code explicitly (excludes .env / *.db via .dockerignore)
# NOTE: do NOT COPY leadhunter.db - .dockerignore excludes *.db so the build
# would fail with "COPY failed: file not found". DB is created at runtime by init_db().
COPY app ./app
COPY config.yaml ./

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=20s \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

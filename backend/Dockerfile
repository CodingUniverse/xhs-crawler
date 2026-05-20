FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    apt-get update && \
    apt-get install -y curl && \
    playwright install-deps chromium && \
    playwright install chromium && \
    rm -rf /var/lib/apt/lists/*

COPY app/ ./app/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
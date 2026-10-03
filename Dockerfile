FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/models/huggingface \
    DATA_DIR=/app/data \
    INDEX_DIR=/app/retrieval/index \
    KNOWLEDGE_PATH=/app/data/knowledge/knowledge_base.jsonl \
    UPLOAD_DIR=/app/data/uploads \
    FEATURES_DIR=/app/features \
    RESULTS_DIR=/app/results/runtime

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN python -m pip install --upgrade pip && pip install -r requirements.txt
COPY . .
RUN mkdir -p /app/data/uploads /app/features /app/results/runtime /models/huggingface
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]

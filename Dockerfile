FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    BAIF_MODEL_PROFILE=quality \
    BAIF_ALLOW_MODEL_DOWNLOAD=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg git build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY requirements-full.txt .
RUN python -m pip install --upgrade pip \
    && pip install -r requirements-full.txt

COPY . .

EXPOSE 8501 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8501"]

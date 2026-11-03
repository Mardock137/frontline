# syntax=docker/dockerfile:1

FROM python:3.14-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Dependencies are copied and installed before the rest of the code,
# so Docker reuses this layer on later builds if requirements.txt does not change.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Cloud Run injects the real port through the PORT variable (default 8080).
EXPOSE 8080

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]

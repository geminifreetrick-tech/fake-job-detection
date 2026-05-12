FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
      "fastapi==0.115.5" "uvicorn[standard]==0.32.1" \
      "pydantic==2.9.2" "pydantic-settings==2.6.1" \
      "httpx==0.27.2" "python-multipart==0.0.17" \
      "pyjwt==2.10.0" "websockets==13.1" "email-validator==2.2.0"

COPY mcp-servers/_common /app/_common
COPY backend/app /app/app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

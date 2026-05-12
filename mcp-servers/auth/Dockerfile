FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl build-essential libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY mcp-servers/auth/pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir \
      "fastapi==0.115.5" "uvicorn[standard]==0.32.1" \
      "pydantic==2.9.2" "pydantic-settings==2.6.1" \
      "sqlalchemy==2.0.36" "asyncpg==0.30.0" \
      "passlib[argon2]==1.7.4" "argon2-cffi==23.1.0" \
      "pyjwt==2.10.0" "python-multipart==0.0.17" "email-validator==2.2.0"

COPY mcp-servers/_common /app/_common
COPY mcp-servers/auth/app /app/app

EXPOSE 8700
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8700"]

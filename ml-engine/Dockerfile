FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl tesseract-ocr libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
      "fastapi==0.115.5" "uvicorn[standard]==0.32.1" \
      "pydantic==2.9.2" "pydantic-settings==2.6.1" \
      "numpy==2.1.3" "pandas==2.2.3" "scikit-learn==1.5.2" \
      "xgboost==2.1.2" "shap==0.46.0" "joblib==1.4.2" "regex==2024.11.6" \
      "python-multipart==0.0.17" \
      "PyMuPDF==1.24.13" "pytesseract==0.3.13" "Pillow==11.0.0"

COPY ml-engine/app /app/app
COPY ml-engine/datasets /app/datasets

# Train a model at image-build time so the container is usable without a pre-existing volume.
RUN mkdir -p /app/model_store && \
    python -m app.models.train --data /app/datasets/sample_jobs.csv --out /app/model_store/

EXPOSE 8100
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8100"]

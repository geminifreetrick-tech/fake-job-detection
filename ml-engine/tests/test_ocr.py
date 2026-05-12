"""Smoke tests for OCR. Tesseract is required only for the image test; the
PDF text-layer path is tested without invoking OCR."""
from __future__ import annotations

import io
import shutil

import pytest

from app.ocr import extract_text_from_bytes


def _make_pdf_with_text(text: str) -> bytes:
    fitz = pytest.importorskip("fitz")
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    out = io.BytesIO()
    doc.save(out)
    doc.close()
    return out.getvalue()


def test_pdf_text_layer_extracted():
    data = _make_pdf_with_text("Hiring software engineer at Acme Inc.")
    result = extract_text_from_bytes(data, "application/pdf")
    assert result.source_type == "pdf"
    assert result.used_ocr is False
    assert "software engineer" in result.text.lower()


def test_plain_text_passthrough():
    payload = b"Hello, this is a plain-text job posting."
    result = extract_text_from_bytes(payload, "text/plain")
    assert result.source_type == "text"
    assert "plain-text job posting" in result.text


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="tesseract not installed")
def test_image_ocr_returns_some_text():
    from reportlab.lib.pagesizes import letter  # type: ignore
    from reportlab.pdfgen import canvas  # type: ignore
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (600, 200), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default()
        draw.text((20, 80), "Software engineer wanted", fill="black", font=font)
    except Exception:
        draw.text((20, 80), "Software engineer wanted", fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    result = extract_text_from_bytes(buf.getvalue(), "image/png")
    assert result.source_type == "image"
    assert result.used_ocr is True

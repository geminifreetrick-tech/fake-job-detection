"""OCR helpers for PDFs and images.

PDFs use PyMuPDF for the text layer when present; we fall back to per-page
raster + Tesseract for image-only PDFs. PNG/JPG go straight through Tesseract
via ``pytesseract``.
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Literal

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

SourceType = Literal["text", "pdf", "image"]


@dataclass
class OcrResult:
    text: str
    source_type: SourceType
    pages: int
    used_ocr: bool


def _ocr_image(image: Image.Image) -> str:
    if image.mode not in ("L", "RGB"):
        image = image.convert("RGB")
    return pytesseract.image_to_string(image)


def _from_pdf(data: bytes) -> OcrResult:
    text_parts: list[str] = []
    used_ocr = False
    with fitz.open(stream=data, filetype="pdf") as doc:
        pages = doc.page_count
        for page in doc:
            t = page.get_text("text").strip()
            if t:
                text_parts.append(t)
            else:
                # No text layer → rasterize and OCR.
                pix = page.get_pixmap(dpi=200)
                img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                text_parts.append(_ocr_image(img))
                used_ocr = True
    return OcrResult(
        text="\n\n".join(p for p in text_parts if p),
        source_type="pdf",
        pages=pages,
        used_ocr=used_ocr,
    )


def _from_image(data: bytes) -> OcrResult:
    with Image.open(io.BytesIO(data)) as img:
        text = _ocr_image(img)
    return OcrResult(text=text, source_type="image", pages=1, used_ocr=True)


def extract_text_from_bytes(data: bytes, content_type: str | None) -> OcrResult:
    """Dispatch by Content-Type. Falls back to PDF detection on magic bytes."""
    ct = (content_type or "").lower()
    if ct == "application/pdf" or data[:4] == b"%PDF":
        return _from_pdf(data)
    if ct.startswith("image/") or data[:3] in (b"\xff\xd8\xff", b"\x89PN"):
        return _from_image(data)
    # Unknown — treat as raw UTF-8.
    try:
        return OcrResult(
            text=data.decode("utf-8", errors="replace"),
            source_type="text",
            pages=1,
            used_ocr=False,
        )
    except Exception as exc:  # pragma: no cover
        raise ValueError(f"Unsupported file content type: {content_type!r}") from exc

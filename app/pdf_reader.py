"""PDF text extraction.

Keeps this isolated from the rest of the app so the parsing strategy
can change without touching the API layer or the LLM client.

Extraction order:
1. pypdf — fast, works for PDFs with a text layer.
2. OCR fallback (pymupdf + pytesseract) — for scanned images when
   Tesseract is installed on the system.
"""

from __future__ import annotations

import io
import logging

from pypdf import PdfReader

logger = logging.getLogger(__name__)

MAX_OCR_PAGES = 30


class EmptyPdfError(ValueError):
    """Raised when a PDF has no extractable text (e.g. a scanned image)."""


def _ocr_fallback(pdf_bytes: bytes) -> str:
    """Render PDF pages as images and OCR them via Tesseract."""
    try:
        import fitz  # pymupdf
        import pytesseract
        from PIL import Image
    except ImportError:
        logger.warning(
            "OCR dependencies not installed (pymupdf, pytesseract, Pillow). "
            "Install them and Tesseract to process scanned PDFs."
        )
        return ""

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages = doc[:MAX_OCR_PAGES]

        chunks: list[str] = []
        for page in pages:
            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text = pytesseract.image_to_string(img, lang="rus+eng")
            if text.strip():
                chunks.append(text)

        doc.close()
        return "\n\n".join(chunks).strip()
    except pytesseract.TesseractNotFoundError:
        logger.warning(
            "Tesseract binary not found. Install it: brew install tesseract tesseract-lang"
        )
        return ""


def extract_text(pdf_bytes: bytes, max_pages: int | None = None) -> str:
    """Extract raw text from a PDF file given as bytes.

    Tries pypdf first; if the PDF has no text layer (scanned image),
    falls back to OCR via Tesseract when available.

    Args:
        pdf_bytes: Raw PDF file content.
        max_pages: Optional cap on pages read.

    Raises:
        EmptyPdfError: if no text could be extracted at all.
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages = reader.pages[:max_pages] if max_pages else reader.pages

    chunks: list[str] = []
    for page in pages:
        text = page.extract_text() or ""
        if text.strip():
            chunks.append(text)

    full_text = "\n\n".join(chunks).strip()
    if full_text:
        return full_text

    logger.info("No text layer found, trying OCR fallback")
    full_text = _ocr_fallback(pdf_bytes)
    if full_text:
        return full_text

    raise EmptyPdfError(
        "No extractable text found. The PDF may be a scanned image — "
        "install Tesseract (brew install tesseract tesseract-lang) for OCR "
        "support, or provide a PDF with a text layer."
    )

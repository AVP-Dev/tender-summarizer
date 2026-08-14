"""PDF text extraction.

Keeps this isolated from the rest of the app so the parsing strategy
(pypdf now, possibly OCR fallback later for scanned tenders) can change
without touching the API layer or the LLM client.
"""

from __future__ import annotations

import io

from pypdf import PdfReader


class EmptyPdfError(ValueError):
    """Raised when a PDF has no extractable text (e.g. a scanned image)."""


def extract_text(pdf_bytes: bytes, max_pages: int | None = None) -> str:
    """Extract raw text from a PDF file given as bytes.

    Args:
        pdf_bytes: Raw PDF file content.
        max_pages: Optional cap on pages read, useful for very large tender
            packages where only the first N pages usually contain the
            contract summary, deadlines and requirements.

    Returns:
        Concatenated text of all (or the first max_pages) pages.

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
    if not full_text:
        raise EmptyPdfError(
            "No extractable text found. The PDF may be a scanned image "
            "and would require OCR, which is out of scope for this script."
        )
    return full_text

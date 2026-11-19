from pathlib import Path

import pymupdf
from fastapi import HTTPException

MAX_PAGES = 300


def _clean_text(raw: str) -> str:
    """Remove blank lines and stray whitespace while keeping line breaks."""
    lines = (line.strip() for line in raw.splitlines())
    return "\n".join(line for line in lines if line)


def extract_pages(pdf_path: Path) -> list[dict]:
    """
    Read a PDF and return one entry per page:
    [{"page_number": 1, "text": "..."}, {"page_number": 2, "text": "..."}, ...]
    Page numbers start at 1, matching what a reader sees in a PDF viewer.
    """
    try:
        doc = pymupdf.open(str(pdf_path))
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Could not read the PDF. The file may be corrupted.",
        ) from exc

    try:
        if doc.needs_pass:
            raise HTTPException(status_code=400, detail="Password-protected PDFs are not supported.")
        if doc.page_count == 0:
            raise HTTPException(status_code=400, detail="The PDF has no pages.")
        if doc.page_count > MAX_PAGES:
            raise HTTPException(
                status_code=400,
                detail=f"The PDF has too many pages. Maximum is {MAX_PAGES}.",
            )

        pages = []
        for index in range(doc.page_count):
            page = doc.load_page(index)
            pages.append(
                {
                    "page_number": index + 1,
                    "text": _clean_text(page.get_text("text")),
                }
            )
        return pages
    finally:
        doc.close()
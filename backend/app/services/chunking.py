from dataclasses import dataclass

CHUNK_SIZE = 800       # maximum characters per chunk
CHUNK_OVERLAP = 120    # characters shared between neighbouring chunks


@dataclass(frozen=True)
class Chunk:
    """A piece of document text together with the page it came from."""

    chunk_index: int   # position across the whole document, starting at 0
    page_number: int   # page the text came from, starting at 1
    text: str


def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split one page's text into pieces, preferring to break at whitespace."""
    pieces: list[str] = []
    n = len(text)
    start = 0

    while start < n:
        end = min(start + chunk_size, n)

        # If we're not at the end of the text, try to end the chunk at a space or newline
        # so we don't cut a word in half. Only accept a break in the second half of the window.
        if end < n:
            cut = max(text.rfind(" ", start, end), text.rfind("\n", start, end))
            if cut > start + chunk_size // 2:
                end = cut

        piece = text[start:end].strip()
        if piece:
            pieces.append(piece)

        if end >= n:
            break

        # Step back by the overlap, then move forward to the next whitespace
        # so the next chunk starts at a word boundary.
        next_start = max(end - overlap, start + 1)
        space = text.find(" ", next_start, end)
        if space != -1:
            next_start = space + 1
        start = next_start

    return pieces


def chunk_pages(
    pages: list[dict],
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[Chunk]:
    """
    Turn page dicts ({"page_number": int, "text": str}) into chunks.
    Each chunk belongs to exactly one page.
    """
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks: list[Chunk] = []
    chunk_index = 0

    for page in pages:
        for piece in _split_text(page["text"], chunk_size, overlap):
            chunks.append(
                Chunk(
                    chunk_index=chunk_index,
                    page_number=page["page_number"],
                    text=piece,
                )
            )
            chunk_index += 1

    return chunks
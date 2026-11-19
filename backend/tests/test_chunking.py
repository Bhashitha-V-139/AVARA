from app.services.chunking import chunk_pages


def test_each_chunk_keeps_its_page_number():
    pages = [
        {"page_number": 1, "text": "Text on the first page."},
        {"page_number": 2, "text": "Text on the second page."},
    ]
    chunks = chunk_pages(pages)

    assert [c.page_number for c in chunks] == [1, 2]
    assert [c.chunk_index for c in chunks] == [0, 1]


def test_long_page_is_split_and_overlaps():
    text = " ".join(f"word{i}" for i in range(500))
    chunks = chunk_pages(
        [{"page_number": 3, "text": text}],
        chunk_size=200,
        overlap=40,
    )

    assert len(chunks) > 1
    assert all(c.page_number == 3 for c in chunks)
    assert all(len(c.text) <= 200 for c in chunks)
    # The last word of one chunk should also appear at the start of the next one.
    assert chunks[0].text.split()[-1] in chunks[1].text


def test_empty_page_produces_no_chunks():
    assert chunk_pages([{"page_number": 1, "text": ""}]) == []
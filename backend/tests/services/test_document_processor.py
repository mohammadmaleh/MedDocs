from app.services.document_processor import chunk_text


def test_chunk_text_keeps_real_page_numbers():
    pages = [
        {"text": "A" * 2000, "page_number": 1},
        {"text": "B" * 2000, "page_number": 2},
    ]

    chunks = chunk_text(pages)

    for chunk in chunks:
        if "A" in chunk["text"]:
            assert chunk["page_number"] == 1
        if "B" in chunk["text"]:
            assert chunk["page_number"] == 2

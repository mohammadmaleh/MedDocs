import uuid

import fitz
from app.config import OPENAI_API_KEY, PINECONE_API_KEY
from openai import OpenAI
from pinecone import Pinecone

EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


openai_client = OpenAI(api_key=OPENAI_API_KEY)
pinecone_client = Pinecone(api_key=PINECONE_API_KEY)

pinecone_index = pinecone_client.Index("meddocs")


def extract_text_from_pdf(file_bytes: bytes) -> list[dict]:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text_and_pages_number = [{"text": page.get_text("text"), "page_number": index + 1} for index, page in enumerate(doc)]  # type: ignore
    doc.close()

    return text_and_pages_number


def chunk_text(text_list: list[dict]) -> list[dict]:
    chunks = []

    for page in text_list:
        text = page["text"]
        start = 0
        while start < len(text):
            chunk = text[start : start + CHUNK_SIZE]
            start += CHUNK_SIZE - CHUNK_OVERLAP
            chunks.append({"text": chunk, "page_number": page["page_number"]})
    return chunks


def embed_and_store(doc_id: int, chunks: list[dict], user_id: int) -> None:

    texts = [chunk["text"] for chunk in chunks]

    response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    vectors = []
    for i, embedding_obj in enumerate(response.data):
        vectors.append(
            {
                "id": f"{doc_id}-{i}-{uuid.uuid4().hex[:8]}",
                "values": embedding_obj.embedding,
                "metadata": {
                    "doc_id": doc_id,
                    "chunk_index": i,
                    "text": chunks[i]["text"],
                    "user_id": user_id,
                    "page_number": chunks[i]["page_number"],
                },
            }
        )
    pinecone_index.upsert(vectors=vectors)

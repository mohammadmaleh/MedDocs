import uuid

import fitz
from openai import OpenAI
from pinecone import Pinecone

from app.config import OPENAI_API_KEY, PINECONE_API_KEY

EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


openai_client = OpenAI(api_key=OPENAI_API_KEY)
pinecone_client = Pinecone(api_key=PINECONE_API_KEY)

pinecone_index = pinecone_client.Index("meddocs")


def extract_text_from_pdf(file_bytes: bytes) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""

    for page in doc:
        text += str(page.get_text("text"))
    doc.close()

    return text.strip()


def chunk_text(text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + CHUNK_SIZE])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def embed_and_store(doc_id: int, chunks: list[str]) -> None:
    response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=chunks)
    vectors = []
    for i, embedding_obj in enumerate(response.data):
        vectors.append(
            {
                "id": f"{doc_id}-{i}-{uuid.uuid4().hex[:8]}",
                "values": embedding_obj.embedding,
                "metadata": {"doc_id": doc_id, "chunk_index": i, "text": chunks[i]},
            }
        )
    pinecone_index.upsert(vectors=vectors)

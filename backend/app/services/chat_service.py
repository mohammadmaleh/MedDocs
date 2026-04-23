from groq import Groq
from openai import OpenAI
from pinecone import Pinecone
from sqlalchemy.orm import Session

from app.config import GROQ_API_KEY, OPENAI_API_KEY, PINECONE_API_KEY
from app.models import ChatMessage, ChatSession

EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "llama-3.3-70b-versatile"

openai_client = OpenAI(api_key=OPENAI_API_KEY)
pinecone_client = Pinecone(api_key=PINECONE_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

pinecone_index = pinecone_client.Index("meddocs")


async def handle_message(
    content: str, user_id: int, session_id: int | None, db: Session
):

    embed_response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL, input=[content]
    )
    embedding = embed_response.data[0].embedding

    search_results = pinecone_index.query(
        vector=embedding,
        top_k=5,
        include_metadata=True,
        filter={"user_id": user_id},
    )
    chunks = [match["metadata"]["text"] for match in search_results["matches"]]

    context = "\n\n".join(chunks)
    messages = [
        {
            "role": "system",
            "content": (
                "You are a medical document assistant. "
                "Answer questions using only the document excerpts provided below. "
                "If the answer is not in the excerpts, say so clearly. "
                "Do not make up information.\n\n"
                f"Document excerpts:\n{context}"
            ),
        },
        {"role": "user", "content": content},
    ]

    if session_id is None:
        session = ChatSession(user_id=user_id)
        db.add(session)
        db.commit()
        db.refresh(session)
        session_id = session.id

    user_message = ChatMessage(role="user", content=content, session_id=session_id)
    db.add(user_message)
    db.commit()

    stream = groq_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        stream=True,
    )

    full_reply = ""
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            full_reply += delta
            yield delta

    assistant_message = ChatMessage(
        role="assistant", content=full_reply, session_id=session_id
    )
    db.add(assistant_message)
    db.commit()

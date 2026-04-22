import os

from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set")
    return value


DATABASE_URL = _require("DATABASE_URL")
SECRET_KEY = _require("SECRET_KEY")
OPENAI_API_KEY = _require("OPENAI_API_KEY")
PINECONE_API_KEY = _require("PINECONE_API_KEY")
GROQ_API_KEY = _require("GROQ_API_KEY")

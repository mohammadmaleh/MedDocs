from fastapi import FastAPI

from app.routes import auth, chat, documents

app = FastAPI()
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)
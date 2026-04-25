from fastapi import Depends, FastAPI

from app.auth import get_current_user
from app.models import User
from app.routes import auth, chat, documents

app = FastAPI()
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return {"email": current_user.email, "id": current_user.id}

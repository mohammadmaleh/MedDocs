from fastapi import Depends, FastAPI
from app.routes import auth,documents
from app.models import User
from app.auth import get_current_user

app = FastAPI()
app.include_router(auth.router)
app.include_router(documents.router)
@app.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return {"email": current_user.email, "id": current_user.id}
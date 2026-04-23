from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import ChatSession, User
from app.schemas import ChatMessageCreate
from app.services.chat_service import handle_message

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", status_code=201)
async def send_message(
    body: ChatMessageCreate,
    session_id: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    message_handler = handle_message(
        content=body.content, user_id=user.id, db=db, session_id=session_id
    )
    return StreamingResponse(message_handler, media_type="text/event-stream")


@router.get("/sessions/{id}/messages", status_code=200)
async def get_session_history(
    id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == id, ChatSession.user_id == user.id)
        .first()
    )
    if not session:
        raise HTTPException(404, "Chat Session Not Found")
    return list(session.messages)


@router.get("/sessions", status_code=200)
async def get_sessions_history(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):

    sessions = db.query(ChatSession).filter(ChatSession.user_id == user.id).all()
    return list(sessions)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import create_access_token, hash_password, verify_password
from app.crud import create_user, get_user_by_email
from app.database import get_db
from app.schemas import LoginRequest, RegisterRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
async def register(body: RegisterRequest, db: Session = Depends(get_db)):
    email = body.email
    password = body.password
    user = get_user_by_email(email=email, db=db)
    if user:
        raise HTTPException(400, "Email is Already Registered")
    hashed_password = hash_password(password)
    return create_user(db=db, email=email, hashed_password=hashed_password)


@router.post("/login", status_code=200)
async def login(body: LoginRequest, db: Session = Depends(get_db)):
    email = body.email
    password = body.password
    user = get_user_by_email(email=email, db=db)
    if not user:
        raise HTTPException(401, "Wrong Credentials")
    verified_password = verify_password(plain=password, hashed=user.hashed_password)
    if not verified_password:
        raise HTTPException(401, "Wrong Credentials")
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "Bearer"}

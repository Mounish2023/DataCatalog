from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from typing import List

from app.database import get_db
from app import schemas, auth
from app.models.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

def get_current_user(token: str = Depends(auth.oauth2_scheme), session: Session = Depends(get_db)):
    sub = auth.decode_token(token)
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token")
    user = session.exec(select(User).where(User.email == sub)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

@router.post("/register", response_model=dict)
def register(payload: schemas.UserCreate, session: Session = Depends(get_db)):
    if session.exec(select(User).where(User.email == payload.email)).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    u = User(email=payload.email, name=payload.name, password_hash=auth.hash_password(payload.password))
    session.add(u); session.commit()
    return {"msg": "registered"}

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_db)):
    user = session.exec(select(User).where(User.email == form_data.username)).first()
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect credentials")
    token = auth.create_access_token(user.email)
    return {"access_token": token, "token_type": "bearer"}

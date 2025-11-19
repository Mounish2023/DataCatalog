from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app import schemas, auth
from app.models.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

async def get_current_user(
    token: str = Depends(auth.oauth2_scheme), 
    session: AsyncSession = Depends(get_db)
):
    sub = auth.decode_token(token)
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token")
    
    result = await session.execute(select(User).where(User.email == sub))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

@router.post("/register", response_model=dict)
async def register(
    payload: schemas.UserCreate, 
    session: AsyncSession = Depends(get_db)
):
    # Check if user already exists
    result = await session.execute(select(User).where(User.email == payload.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user = User(
        email=payload.email, 
        name=payload.name, 
        password_hash=auth.hash_password(payload.password)
    )
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    return {"msg": "User registered successfully"}

@router.post("/login", response_model=schemas.Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    session: AsyncSession = Depends(get_db)
):
    # Find user by email
    result = await session.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()
    
    # Verify password
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect credentials")
    
    # Create and return access token
    token = auth.create_access_token(user.email)
    return {"access_token": token, "token_type": "bearer"}

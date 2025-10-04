from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.postgres import get_postgres_db
from app.authentication.jwt import create_access_token
from app.authentication.schemas import UserCreate, UserLogin, TokenResponse
from app.authentication.service import AuthService

router = APIRouter()
auth_service = AuthService()


@router.post("/signup", response_model=TokenResponse, status_code=201)
async def signup(user_data: UserCreate, db: Session = Depends(get_postgres_db)):
    user = auth_service.create_user(user_data, db)
    access_token = create_access_token(data={
        "sub": user.username,
        "role": user.role
    })
    return TokenResponse(access_token=access_token, role=user.role)


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_postgres_db)):
    user = auth_service.authenticate_user(user_data.username, user_data.password, db)
    access_token = create_access_token(data={
        "sub": user.username,
        "role": user.role
    })
    return TokenResponse(access_token=access_token, role=user.role)

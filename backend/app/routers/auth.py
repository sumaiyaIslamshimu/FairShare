from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.db.mongo import get_db
from app.models.user import LoginRequest, RegisterRequest, TokenResponse, UserPublic
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserPublic, status_code=201)
def register(body: RegisterRequest, db=Depends(get_db)):
    return auth_service.register(db, body)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db=Depends(get_db)):
    return auth_service.login(db, body.email, body.password)


@router.get("/me", response_model=UserPublic)
def me(user=Depends(get_current_user), db=Depends(get_db)):
    return auth_service.user_public(db, user)
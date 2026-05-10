from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import timedelta
from app.auth import authenticate_user, create_access_token, get_password_hash, get_current_user
from app.database import get_db
from app import models
from app.config import settings
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["authentication"], redirect_slashes=False)

class RegisterRequest(BaseModel):
    login: str
    email: str
    password: str

@router.get("")
async def login(
    login: str = Query(...),
    password: str = Query(...),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, login, password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect login or password")
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(data={"sub": user.id})
    return {
        "success": True,
        "data": {
            "auth_token": access_token,
            "user": {
                "id": user.id,
                "login": user.login,
                "email": user.email,
                "role": user.role.value
            }
        }
    }

def get_user_by_token(token: str, db: Session):
    from jose import jwt
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = int(payload.get("sub"))
        return db.query(models.User).filter(models.User.id == user_id).first()
    except:
        return None

@router.post("/register")
async def register(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    existing = db.query(models.User).filter(
        (models.User.login == data.login) | (models.User.email == data.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Login or email already exists")
    hashed_password = get_password_hash(data.password)
    new_user = models.User(
        login=data.login,
        email=data.email,
        hashed_password=hashed_password,
        role=models.UserRole.pilot
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(data={"sub": new_user.id})
    return {
        "success": True,
        "data": {
            "auth_token": access_token,
            "user": {
                "id": new_user.id,
                "login": new_user.login,
                "email": new_user.email,
                "role": new_user.role.value
            }
        }
    }

@router.post("/refresh")
async def refresh_token(current_user: models.User = Depends(get_current_user)):
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(data={"sub": current_user.id})
    return {
        "success": True,
        "data": {"auth_token": access_token}
    }
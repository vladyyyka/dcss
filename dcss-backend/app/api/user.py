from fastapi import APIRouter, Depends
from app.auth import get_current_user
from app import models

router = APIRouter(prefix="/user", tags=["user"])

@router.get("/me", response_model=dict)
async def get_me(current_user: models.User = Depends(get_current_user)):
    return {
        "success": True,
        "data": {
            "id": current_user.id,
            "login": current_user.login,
            "email": current_user.email,
            "role": current_user.role.value,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None
        }
    }
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models
from app.auth import get_current_user
from app.config import settings
from app.database import get_db

router = APIRouter(prefix="/server", tags=["server"])


@router.get("/status", response_model=dict)
async def server_status(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Возвращает информацию о состоянии сервера."""
    in_progress = db.query(models.QuestInstance).filter(
        models.QuestInstance.status == models.QuestStatus.running
    ).count()
    all_executed = db.query(models.QuestInstance).count()

    return {
        "success": True,
        "data": {
            "quest_in_progress": in_progress,
            "max_quest": settings.max_quest,
            "all_executed": all_executed,
        },
    }

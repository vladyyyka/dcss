from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app import models
from app.auth import get_current_instructor

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users", response_model=dict)
async def get_all_users(
    skip: int = Query(0, ge=0),
    take: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_instructor)
):
    total = db.query(models.User).count()
    users = db.query(models.User).offset(skip).limit(take).all()
    items = []
    for u in users:
        items.append({
            "id": u.id,
            "login": u.login,
            "email": u.email,
            "role": u.role.value,
            "created_at": u.created_at.isoformat() if u.created_at else None
        })
    return {
        "success": True,
        "data": {
            "skip": skip,
            "take": take,
            "total": total,
            "list": items
        }
    }

@router.get("/users/{user_id}/quests", response_model=dict)
async def get_user_quests(
    user_id: int,
    skip: int = Query(0, ge=0),
    take: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, pattern="^(pending|running|completed|aborted)$"),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_instructor)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    query = db.query(models.QuestInstance).filter(models.QuestInstance.user_id == user_id)
    if status:
        query = query.filter(models.QuestInstance.status == status)
    total = query.count()
    instances = query.offset(skip).limit(take).all()
    items = []
    for inst in instances:
        items.append({
            "guid": inst.guid,
            "type_id": inst.type_id,
            "status": inst.status.value,
            "result": inst.result.value if inst.result else None,
            "started_at": inst.started_at.isoformat() if inst.started_at else None,
            "completed_at": inst.completed_at.isoformat() if inst.completed_at else None,
            "max_time_sec": inst.max_time_sec,
            "elapsed_time_sec": inst.elapsed_time_sec
        })
    return {
        "success": True,
        "data": {
            "user_id": user_id,
            "skip": skip,
            "take": take,
            "total": total,
            "list": items
        }
    }

@router.get("/stats", response_model=dict)
async def get_overall_stats(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_instructor)
):
    total_users = db.query(models.User).count()
    total_quests = db.query(models.QuestInstance).count()
    completed_quests = db.query(models.QuestInstance).filter(models.QuestInstance.status == "completed").count()
    success_quests = db.query(models.QuestInstance).filter(models.QuestInstance.result == "success").count()
    return {
        "success": True,
        "data": {
            "total_users": total_users,
            "total_quests": total_quests,
            "completed_quests": completed_quests,
            "success_quests": success_quests
        }
    }
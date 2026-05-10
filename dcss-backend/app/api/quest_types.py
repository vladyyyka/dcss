from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas, models
from app.database import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/quest", tags=["quest types"])

@router.get("/type", response_model=dict)
def list_quest_types(
    skip: int = Query(0, ge=0),
    take: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Возвращает список доступных типов заданий с пагинацией.
    """
    types = crud.get_quest_types(db, skip=skip, take=take)
    total = db.query(models.QuestType).count()
    return {
        "success": True,
        "data": {
            "skip": skip,
            "take": take,
            "total": total,
            "types": [{"type_id": t.id, "name": t.name, "desc": t.description} for t in types]
        }
    }

@router.get("/type/{type_id}", response_model=dict)
def get_quest_type_detail(type_id: int, db: Session = Depends(get_db),current_user: dict = Depends(get_current_user)):
    quest_type = crud.get_quest_type(db, type_id)
    if not quest_type:
        raise HTTPException(status_code=404, detail="Quest type not found")
    checklist = [schemas.QuestCriterion.model_validate(c) for c in quest_type.criteria] if quest_type.criteria else []
    detail = schemas.QuestTypeDetail(
        type_id=quest_type.id,
        name=quest_type.name,
        desc=quest_type.description,
        max_time_sec=quest_type.max_time_sec,
        markdown=quest_type.markdown,
        checklist=checklist
    )
    return {
        "success": True,
        "data": detail.model_dump()
    }
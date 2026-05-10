from sqlalchemy.orm import Session
from app import models, schemas

def get_quest_types(db: Session, skip: int = 0, take: int = 20):
    return db.query(models.QuestType).offset(skip).limit(take).all()

def get_quest_type(db: Session, type_id: int):
    return db.query(models.QuestType).filter(models.QuestType.id == type_id).first()
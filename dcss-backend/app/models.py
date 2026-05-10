from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
import enum

class QuestStatus(enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    aborted = "aborted"

class QuestResult(enum.Enum):
    success = "success"
    fail = "fail"
    none = "none"

class UserRole(enum.Enum):
    pilot = "pilot"
    instructor = "instructor"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    login = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.pilot)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    quests = relationship("QuestInstance", back_populates="user", cascade="all, delete-orphan")

class QuestType(Base):
    __tablename__ = "quest_types"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    max_time_sec = Column(Integer, nullable=False)
    markdown = Column(Text, nullable=True)
    criteria = Column(JSON, nullable=False)
    instances = relationship("QuestInstance", back_populates="quest_type")

class QuestInstance(Base):
    __tablename__ = "quest_instances"
    guid = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    type_id = Column(Integer, ForeignKey("quest_types.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(Enum(QuestStatus), default=QuestStatus.pending)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    result = Column(Enum(QuestResult), nullable=True)
    max_time_sec = Column(Integer)
    elapsed_time_sec = Column(Integer, nullable=True)
    link = Column(String, nullable=True)
    log_path = Column(String, nullable=True)
    progress_data = Column(JSON, nullable=True)
    quest_type = relationship("QuestType", back_populates="instances")
    user = relationship("User", back_populates="quests")
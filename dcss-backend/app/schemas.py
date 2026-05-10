from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class QuestCriterion(BaseModel):
    check_id: int
    name: str
    desc: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class QuestTypeListItem(BaseModel):
    type_id: int = Field(..., alias="id")          
    name: str
    desc: Optional[str] = Field(None, alias="description")  

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True  
    )

class QuestTypeDetail(QuestTypeListItem):
    max_time_sec: int
    markdown: Optional[str] = None
    checklist: List[QuestCriterion] = []

    model_config = ConfigDict(from_attributes=True)

class QuestStatusEnum(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    aborted = "aborted"

class QuestResultEnum(str, Enum):
    success = "success"
    fail = "fail"
    none = "none"

class QuestStartRequest(BaseModel):
    type_id: int

class QuestStartResponse(BaseModel):
    type_id: int
    name: str
    desc: Optional[str] = None
    quest_guid: str
    link: str

    model_config = ConfigDict(from_attributes=True)

class QuestStatusResponse(BaseModel):
    type_id: int
    quest_guid: str
    link: Optional[str] = None
    status: QuestStatusEnum
    started: Optional[datetime] = None
    completed: Optional[datetime] = None
    result: Optional[QuestResultEnum] = None
    max_time_sec: int
    elapsed_time_sec: Optional[int] = None
    checklist: List[QuestCriterion] = []

    model_config = ConfigDict(from_attributes=True)

class QuestHistoryItem(BaseModel):
    type_id: int
    quest_guid: str
    status: QuestStatusEnum
    started: Optional[datetime] = None
    completed: Optional[datetime] = None
    max_time_sec: int
    elapsed_time_sec: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class QuestHistoryResponse(BaseModel):
    skip: int
    take: int
    filtered: int
    total: int
    list: List[QuestHistoryItem]
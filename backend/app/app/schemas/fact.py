from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Json


# Shared properties
from app.schemas.deck import Deck


class FactBase(BaseModel):
    text: Optional[str] = None
    answer: Optional[str] = None
    category: Optional[str] = None


class KarlFact(FactBase):
    user_id: int
    fact_id: int
    text: str
    answer: str
    label: Optional[str] = None
    history_id: int = None


class InternalFactBase(FactBase):
    deck_id: int = None
    identifier: Optional[str] = None
    answer_lines: List[str] = None
    extra: dict = None


# Properties to receive on fact creation
class FactCreate(InternalFactBase):
    text: str
    answer: str
    deck_id: int
    answer_lines: List[str]


# Properties to receive on fact update
class FactUpdate(InternalFactBase):
    pass


# Properties shared by models stored in DB
class FactInDBBase(InternalFactBase):
    fact_id: int
    deck_id: int
    user_id: int
    text: str
    answer: str
    create_date: datetime
    update_date: datetime
    answer_lines: List[str]
    deck: Deck

    class Config:
        orm_mode = True


# Properties to return to client
class Fact(FactInDBBase):
    rationale: Optional[str] = None


# Additional properties stored in DB
class FactInDB(FactInDBBase):
    pass

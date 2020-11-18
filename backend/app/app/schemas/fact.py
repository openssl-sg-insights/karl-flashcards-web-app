from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.repetition import Repetition
from app.schemas.deck import Deck
# Shared properties
from app.schemas.permission import Permission


class FactBase(BaseModel):
    text: Optional[str] = None
    answer: Optional[str] = None
    category: Optional[str] = None


class KarlFact(FactBase):
    user_id: int
    fact_id: int
    text: str
    answer: str
    deck_name: str
    deck_id: int
    repetition_model: Repetition
    env: str


class KarlFactUpdate(KarlFact):
    elapsed_seconds_text: Optional[int] = None
    elapsed_seconds_answer: Optional[int] = None
    elapsed_milliseconds_text: Optional[int] = None
    elapsed_milliseconds_answer: Optional[int] = None
    history_id: int
    label: bool
    debug_id: str


class InternalFactBase(FactBase):
    deck_id: Optional[int] = None
    identifier: Optional[str] = None
    answer_lines: List[str] = None
    extra: Optional[dict] = None


# Properties to receive on fact creation
class FactCreate(InternalFactBase):
    text: str
    answer: str
    deck_id: int
    answer_lines: List[str]


# Properties to receive on fact update
class FactUpdate(InternalFactBase):
    pass


# Properties to receive on fact report
class FactToReport(InternalFactBase):
    pass


class FactReported(InternalFactBase):
    reporter_id: int
    reporter_username: str
    report_id: int


# Properties to receive on fact search
class FactSearch(InternalFactBase):
    all: Optional[str] = None
    deck_ids: Optional[List[int]] = None
    marked: Optional[bool] = None
    studyable: Optional[bool] = None
    suspended: Optional[bool] = None
    reported: Optional[bool] = None
    skip: Optional[int] = None
    limit: Optional[int] = None
    randomize: bool = False


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
    marked: Optional[bool] = None
    reported: Optional[bool] = None
    suspended: Optional[bool] = None
    permission: Optional[Permission] = None
    reports: Optional[List[FactReported]] = None
    debug_id: Optional[str] = None


# Properties to return to client
class FactBrowse(BaseModel):
    facts: List[Fact]
    total: int


# Additional properties stored in DB
class FactInDB(FactInDBBase):
    pass

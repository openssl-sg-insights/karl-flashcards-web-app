import logging
import time
from datetime import datetime
from typing import Any, List, Optional

from app import crud, models, schemas
from app.api import deps
from app.core.celery_app import celery_app
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from pytz import timezone
from sqlalchemy.orm import Session
from starlette.background import BackgroundTasks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=schemas.FactBrowse)
def read_facts(
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = 100,
        all: Optional[str] = None,
        text: Optional[str] = None,
        answer: Optional[str] = None,
        category: Optional[str] = None,
        identifier: Optional[str] = None,
        deck_ids: Optional[List[int]] = Query(None),
        deck_id: Optional[int] = None,
        marked: Optional[bool] = None,
        suspended: Optional[bool] = None,
        reported: Optional[bool] = None,
        permissions: bool = True,
        current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve facts.
    """
    if suspended and reported:
        studyable = True
    else:
        studyable = False
    search = schemas.FactSearch(all=all,
                                text=text,
                                answer=answer,
                                category=category,
                                identifier=identifier,
                                deck_ids=deck_ids,
                                deck_id=deck_id,
                                marked=marked,
                                suspended=suspended,
                                reported=reported,
                                studyable=studyable,
                                skip=skip,
                                limit=limit
                                )
    query = crud.fact.build_facts_query(db=db, user=current_user, filters=search)
    facts = crud.fact.get_eligible_facts(query=query, skip=skip, limit=limit)
    total = crud.fact.count_eligible_facts(query=query)
    if permissions:
        begin_overall_start = time.time()
        new_facts: List[schemas.Fact] = []
        for fact in facts:
            new_fact = schemas.Fact.from_orm(fact)
            new_fact.permission = fact.permissions(current_user)
            new_fact.marked = True if current_user in fact.markers else False
            suspended = (db.query(models.Suspended)
                         .filter(models.Suspended.user_id == current_user.id)
                         .filter(models.Suspended.fact_id == fact.fact_id)
                         .filter(models.Suspended.suspend_type == schemas.SuspendType.suspend)
                         .first())
            reported = (db.query(models.Suspended)
                        .filter(models.Suspended.user_id == current_user.id)
                        .filter(models.Suspended.fact_id == fact.fact_id)
                        .filter(models.Suspended.suspend_type == schemas.SuspendType.suspend)
                        .first())
            new_fact.suspended = True if suspended or reported else False
            if new_fact.permission is schemas.Permission.viewer:
                new_fact.reported = True if reported else False
            new_facts.append(new_fact)
        fact_browser = schemas.FactBrowse(facts=new_facts, total=total)
        overall_end_time = time.time()
        overall_total_time = overall_end_time - begin_overall_start
        logger.info("permissions: " + str(overall_total_time))
    else:
        fact_browser = schemas.FactBrowse(facts=facts, total=total)
    details = search.dict()
    details["study_system"] = "karl"
    history_in = schemas.HistoryCreate(
        time=datetime.now(timezone('UTC')).isoformat(),
        user_id=current_user.id,
        log_type=schemas.Log.browser,
        details=details
    )
    crud.history.create(db=db, obj_in=history_in)
    return fact_browser


@router.post("/", response_model=schemas.Fact)
def create_fact(
        *,
        db: Session = Depends(deps.get_db),
        fact_in: schemas.FactCreate,
        current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new fact.
    """
    fact = crud.fact.create_with_owner(db=db, obj_in=fact_in, user=current_user)
    return fact


@router.post("/upload/txt", response_model=bool)
def create_facts_txt(
        *,
        db: Session = Depends(deps.get_db),
        upload_file: UploadFile = File(...),
        deck_id: int = Form(...),
        headers: List[schemas.Field] = Query([schemas.Field.text, schemas.Field.answer]),
        delimeter: str = Form("\t"),
        background_tasks: BackgroundTasks,
        current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Upload a txt/tsv/csv file with facts
    """
    if "text/plain" == upload_file.content_type or "text/csv" == upload_file.content_type:
        deck = crud.deck.get(db=db, id=deck_id)
        if not deck:
            raise HTTPException(status_code=404, detail="Deck not found")
        if deck not in current_user.decks:
            raise HTTPException(status_code=401, detail="User does not possess the specified deck")
        props = schemas.FileProps(default_deck=deck, delimeter=delimeter, headers=headers)
        background_tasks.add_task(crud.fact.load_txt_facts, db=db, file=upload_file.file, user=current_user,
                                  props=props)
    else:
        raise HTTPException(status_code=423, detail="This file type is unsupported")

    return True


@router.post("/upload/json", response_model=bool)
def create_facts_json(
        *,
        db: Session = Depends(deps.get_db),
        upload_file: UploadFile = File(...),
        background_tasks: BackgroundTasks,
        current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Upload a json file with facts
    """

    if "application/json" == upload_file.content_type:
        background_tasks.add_task(crud.fact.load_json_facts, db=db, file=upload_file.file, user=current_user)
    else:
        raise HTTPException(status_code=423, detail="This file type is unsupported")

    return True


@router.put("/preloaded", response_model=bool)
def update_preloaded_facts(
        *,
        current_user: models.User = Depends(deps.get_current_active_superuser),  # noqa
) -> Any:
    """
    Update preloaded facts.
    """
    celery_app.send_task("app.worker.clean_up_preloaded_facts")
    return True


@router.put("/{fact_id}", response_model=schemas.Fact)
def update_fact(
        *,
        fact_in: schemas.FactUpdate,
        perms: deps.OwnerFactPerms = Depends(),
) -> Any:
    """
    Update a fact.
    """
    details = {
        "study_system": "karl",
        "old_fact": perms.fact.__dict__,
        "fact_update": fact_in.dict(),
    }

    fact = crud.fact.update(db=perms.db, db_obj=perms.fact, obj_in=fact_in)

    history_in = schemas.HistoryCreate(
        time=datetime.now(timezone('UTC')).isoformat(),
        user_id=perms.current_user.id,
        log_type=schemas.Log.update_fact,
        details=details

    )
    crud.history.create(db=perms.db, obj_in=history_in)
    return fact


@router.get("/{fact_id}", response_model=schemas.Fact)
def read_fact(
        *,
        perms: deps.CheckFactPerms = Depends(),
) -> Any:
    """
    Get fact by ID.
    """
    return perms.fact


@router.delete("/{fact_id}", response_model=schemas.Fact)
def delete_fact(
        *,
        perms: deps.CheckFactPerms = Depends(),
) -> Any:
    """
    Delete a fact.
    """
    if perms.current_user in perms.fact.markers:
        fact = crud.fact.undo_remove(db=perms.db, db_obj=perms.fact, user=perms.current_user)
    else:
        fact = crud.fact.remove(db=perms.db, db_obj=perms.fact, user=perms.current_user)
    return fact


@router.put("/suspend/{fact_id}", response_model=schemas.Fact)
def suspend_fact(
        *,
        perms: deps.CheckFactPerms = Depends(),
) -> Any:
    """
    Suspend a fact.
    """
    if perms.current_user in perms.fact.markers:
        fact = crud.fact.undo_suspend(db=perms.db, db_obj=perms.fact, user=perms.current_user)
    else:
        fact = crud.fact.suspend(db=perms.db, db_obj=perms.fact, user=perms.current_user)
    return fact


@router.put("/report/{fact_id}", response_model=schemas.Fact)
def report_fact(
        *,
        perms: deps.CheckFactPerms = Depends(),
) -> Any:
    """
    Report a fact.
    """
    if perms.current_user in perms.fact.markers:
        fact = crud.fact.undo_report(db=perms.db, db_obj=perms.fact, user=perms.current_user)
    else:
        fact = crud.fact.report(db=perms.db, db_obj=perms.fact, user=perms.current_user)
    return fact


@router.put("/mark/{fact_id}", response_model=schemas.Fact)
def mark_fact(
        *,
        perms: deps.CheckFactPerms = Depends(),
) -> Any:
    """
    Report a fact.
    """
    if perms.current_user in perms.fact.markers:
        fact = crud.fact.undo_mark(db=perms.db, db_obj=perms.fact, user=perms.current_user)
    else:
        fact = crud.fact.mark(db=perms.db, db_obj=perms.fact, user=perms.current_user)
    return fact

    chicken = crud.fact.get_eligible_facts(db=db, user=user, filters=FactSearch(text="apple"))
    assert len(chicken) == 1


@router.put("/status/{fact_id}", response_model=schemas.Fact)
def clear_fact_status(
        *,
        perms: deps.CheckFactPerms = Depends(),
) -> Any:
    """
    Clears a user's reports or supensions of a fact.
    """
    fact = crud.fact.clear_report_or_suspend(db=perms.db, db_obj=perms.fact, user=perms.current_user)
    return fact

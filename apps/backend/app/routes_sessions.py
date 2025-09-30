from __future__ import annotations
import json
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, conint, constr
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .models import SessionRecord, DayProgress, User
from .schemas import ScheduleOutput

router = APIRouter(prefix="/sessions", tags=["sessions"])

# ---------- Schemas ----------

class SaveSessionRequest(BaseModel):
    # who/what
    title: constr(strip_whitespace=True, min_length=3, max_length=200)
    brief: constr(strip_whitespace=True, min_length=10, max_length=1000)
    goals: List[constr(strip_whitespace=True, min_length=2)] = Field(default_factory=list)
    # pacing
    daily_minutes: conint(ge=10, le=180)
    duration_days: conint(ge=1, le=365)
    preferred_time: constr(pattern=r"^\d{2}:\d{2}$")
    timezone: constr(strip_whitespace=True, min_length=2, max_length=64) = "Asia/Manila"
    # the generated plan to persist (day_1..day_N under data)
    plan: ScheduleOutput

class UserPublic(BaseModel):
    id: int
    name: str
    username: str
    email: str

class DayProgressState(BaseModel):
    completed: bool
    completed_at: datetime | None = None

class SessionSaved(BaseModel):
    id: int
    user: UserPublic
    data: ScheduleOutput
    progress: dict[str, DayProgressState] = Field(default_factory=dict)

class SessionSummary(BaseModel):
    id: int
    title: str
    created_at: datetime
    duration_days: int
    daily_minutes: int

class DayDetail(BaseModel):
    session_id: int
    day_key: str
    day_index: int
    title: str
    completed: bool
    data: ScheduleOutput  # contains only the requested day in data{}

class ProgressSummary(BaseModel):
    total_days: int
    completed: int
    not_completed: int
    progress_in_percent: str
    breakdown: dict[str, DayProgressState]
    
class TitleUpdate(BaseModel):
    title: constr(strip_whitespace=True, min_length=3, max_length=200)


# ---------- helpers ----------

def _user_public(u: User) -> UserPublic:
    return UserPublic(id=u.id, name=u.name, username=u.username, email=u.email)

def _progress_map(db: Session, session_id: int) -> dict[str, DayProgressState]:
    rows = db.query(DayProgress).filter(DayProgress.session_id == session_id).all()
    return {
        f"day_{r.day_index}": DayProgressState(completed=r.completed, completed_at=r.completed_at)
        for r in rows
    }

def _saved(rec: SessionRecord, user: User, db: Session) -> SessionSaved:
    return SessionSaved(
        id=rec.id,
        user=_user_public(user),
        data=ScheduleOutput.model_validate_json(rec.plan_json),
        progress=_progress_map(db, rec.id),
    )

# ---------- Endpoints: save / list / get ----------

@router.post("", response_model=SessionSaved, status_code=201)
def save_session(
    body: SaveSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rec = SessionRecord(
        user_id=current_user.id,
        title=body.title,
        brief=body.brief,
        goals_json=json.dumps(body.goals, ensure_ascii=False),
        daily_minutes=body.daily_minutes,
        duration_days=body.duration_days,
        preferred_time=body.preferred_time,
        timezone=body.timezone,
        plan_json=body.plan.model_dump_json(),
        meta_json=json.dumps({"days": len(body.plan.data)}, ensure_ascii=False),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return _saved(rec, current_user, db)

@router.get("", response_model=list[SessionSummary])
def list_sessions(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(SessionRecord)
        .filter(SessionRecord.user_id == current_user.id)
        .order_by(SessionRecord.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        SessionSummary(
            id=r.id,
            title=r.title,
            created_at=r.created_at,
            duration_days=r.duration_days,
            daily_minutes=r.daily_minutes,
        )
        for r in rows
    ]

@router.get("/{session_id}", response_model=SessionSaved)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rec = (
        db.query(SessionRecord)
        .filter(SessionRecord.id == session_id, SessionRecord.user_id == current_user.id)
        .first()
    )
    if not rec:
        raise HTTPException(status_code=404, detail="Session not found")
    return _saved(rec, current_user, db)

# ---------- Day access & progress ----------

@router.get("/{session_id}/day/{day_index}", response_model=DayDetail)
def get_day(
    session_id: int,
    day_index: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rec = (
        db.query(SessionRecord)
        .filter(SessionRecord.id == session_id, SessionRecord.user_id == current_user.id)
        .first()
    )
    if not rec:
        raise HTTPException(status_code=404, detail="Session not found")

    sched = ScheduleOutput.model_validate_json(rec.plan_json)
    key = f"day_{day_index}"
    if key not in sched.data:
        raise HTTPException(status_code=404, detail="Day not found")

    prog = (
        db.query(DayProgress)
        .filter(DayProgress.session_id == rec.id, DayProgress.day_index == day_index)
        .first()
    )
    completed = bool(prog and prog.completed)

    # return only that one day inside data{}
    return DayDetail(
        session_id=rec.id,
        day_key=key,
        day_index=day_index,
        title=rec.title,
        completed=completed,
        data=ScheduleOutput(overview=sched.overview, data={key: sched.data[key]}),
    )

@router.post("/{session_id}/day/{day_index}/complete")
def mark_day_complete(
    session_id: int,
    day_index: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rec = (
        db.query(SessionRecord)
        .filter(SessionRecord.id == session_id, SessionRecord.user_id == current_user.id)
        .first()
    )
    if not rec:
        raise HTTPException(status_code=404, detail="Session not found")

    prog = (
        db.query(DayProgress)
        .filter(DayProgress.session_id == rec.id, DayProgress.day_index == day_index)
        .first()
    )
    if not prog:
        prog = DayProgress(session_id=rec.id, day_index=day_index, completed=True, completed_at=datetime.utcnow())
        db.add(prog)
    else:
        prog.completed = True
        prog.completed_at = datetime.utcnow()
    db.commit()
    return JSONResponse({"ok": True, "session_id": rec.id, "day_index": day_index, "completed": True})

@router.post("/{session_id}/day/{day_index}/undo")
def uncomplete_day(
    session_id: int,
    day_index: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rec = (
        db.query(SessionRecord)
        .filter(SessionRecord.id == session_id, SessionRecord.user_id == current_user.id)
        .first()
    )
    if not rec:
        raise HTTPException(status_code=404, detail="Session not found")

    prog = (
        db.query(DayProgress)
        .filter(DayProgress.session_id == rec.id, DayProgress.day_index == day_index)
        .first()
    )
    if prog:
        prog.completed = False
        prog.completed_at = None
        db.commit()
    return JSONResponse({"ok": True, "session_id": rec.id, "day_index": day_index, "completed": True})

@router.get("/{session_id}/progress", response_model=ProgressSummary)
def get_progress(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rec = (
        db.query(SessionRecord)
        .filter(SessionRecord.id == session_id, SessionRecord.user_id == current_user.id)
        .first()
    )
    if not rec:
        raise HTTPException(status_code=404, detail="Session not found")

    sched = ScheduleOutput.model_validate_json(rec.plan_json)
    total_days = max(rec.duration_days or 0, len(sched.data) or 0)
    if total_days <= 0:
        total_days = 1  # safety

    breakdown = _progress_map(db, rec.id)

    completed = 0
    for i in range(1, total_days + 1):
        key = f"day_{i}"
        state = breakdown.get(key)
        if state and state.completed:
            completed += 1

    not_completed = max(0, total_days - completed)
    pct = int(round((completed / total_days) * 100))

    return ProgressSummary(
        total_days=total_days,
        completed=completed,
        not_completed=not_completed,
        progress_in_percent=f"{pct}%",
        breakdown=breakdown,
    )

@router.patch("/{session_id}/title", response_model=SessionSaved)
def rename_session(
    session_id: int,
    body: TitleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rec = (
        db.query(SessionRecord)
        .filter(SessionRecord.id == session_id, SessionRecord.user_id == current_user.id)
        .first()
    )
    if not rec:
        raise HTTPException(status_code=404, detail="Session not found")
    rec.title = body.title
    rec.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(rec)
    return _saved(rec, current_user, db)

@router.delete("/{session_id}")
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rec = (
        db.query(SessionRecord)
        .filter(SessionRecord.id == session_id, SessionRecord.user_id == current_user.id)
        .first()
    )
    if not rec:
        raise HTTPException(status_code=404, detail="Session not found")

    # Count progress rows (for a friendly response)
    removed_progress = (
        db.query(DayProgress)
        .filter(DayProgress.session_id == rec.id)
        .count()
    )

    db.delete(rec)        # ORM delete; with PRAGMA + FK cascade this wipes DayProgress
    db.commit()

    return {"ok": True, "deleted_id": session_id, "removed_progress": removed_progress}

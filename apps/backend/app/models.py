from __future__ import annotations
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    username = Column(String(60), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # relationship examples (not strictly required for MVP usage)
    sessions = relationship("SessionRecord", back_populates="user", cascade="all,delete")

class SessionRecord(Base):
    __tablename__ = "session_records"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    title = Column(String(200), nullable=False)  # e.g., "Learn Python"
    brief = Column(Text, nullable=False)
    goals_json = Column(Text, nullable=False)  # JSON list as string
    daily_minutes = Column(Integer, nullable=False)
    duration_days = Column(Integer, nullable=False)          # NEW for scheduling
    preferred_time = Column(String(8), nullable=False)       # "HH:MM"
    timezone = Column(String(64), nullable=False)

    plan_json = Column(Text, nullable=False)   # full structured plan (days with resources/videos/exercises)
    meta_json = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="sessions")
    progress = relationship("DayProgress", back_populates="session", cascade="all,delete")

Index("ix_session_user_created", SessionRecord.user_id, SessionRecord.created_at.desc())

class DayProgress(Base):
    __tablename__ = "day_progress"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("session_records.id", ondelete="CASCADE"), nullable=False)
    day_index = Column(Integer, nullable=False)  # 1..N
    completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    session = relationship("SessionRecord", back_populates="progress")
    __table_args__ = (
        UniqueConstraint("session_id", "day_index", name="uq_session_day"),
    )

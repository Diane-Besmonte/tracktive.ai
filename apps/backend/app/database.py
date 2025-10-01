# from __future__ import annotations
# from sqlalchemy import create_engine, event
# from sqlalchemy.orm import sessionmaker, declarative_base
# from .config import settings

# connect_args = {}
# if settings.DATABASE_URL.startswith("sqlite"):
#     connect_args = {"check_same_thread": False}

# engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# # Ensure SQLite enforces ON DELETE CASCADE
# @event.listens_for(engine, "connect")
# def _set_sqlite_pragma(dbapi_connection, connection_record):
#     if settings.DATABASE_URL.startswith("sqlite"):
#         cursor = dbapi_connection.cursor()
#         cursor.execute("PRAGMA foreign_keys=ON")
#         cursor.close()

# # FastAPI dependency
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# ======================

# apps/backend/app/database.py
from __future__ import annotations

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings  # still fine to use your settings wrapper

Base = declarative_base()

def _normalize_db_url(url: str) -> str:
    """
    Normalize DB URL for SQLAlchemy:
    - postgres://... -> postgresql+psycopg://...
    - ensure sslmode=require for Supabase unless already present
    """
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://") and "+psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)

    if url.startswith("postgresql+psycopg://") and "sslmode=" not in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}sslmode=require"
    return url

# Choose the URL:
# - Prefer settings.DATABASE_URL (Vercel → Supabase)
# - Fallback to local SQLite for dev if not set
raw_url = settings.DATABASE_URL or os.getenv("DATABASE_URL")
if not raw_url:
    raw_url = "sqlite:///./app.db"

url = _normalize_db_url(raw_url)

is_sqlite = url.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

# Pre-ping helps recycle dead connections, useful with serverless + pooling
engine = create_engine(
    url,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Ensure SQLite enforces ON DELETE CASCADE (no-op for Postgres)
if is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# FastAPI dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

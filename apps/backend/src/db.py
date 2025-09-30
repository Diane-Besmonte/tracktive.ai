# apps/backend/src/db.py
import os
from sqlalchemy import create_engine

# Turso envs you’ll add in Vercel later
url = os.getenv("TURSO_DATABASE_URL")
token = os.getenv("TURSO_AUTH_TOKEN")

engine = create_engine(
    f"sqlite+{url}?secure=true",
    connect_args={"auth_token": token},
)

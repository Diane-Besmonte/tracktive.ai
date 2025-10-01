# Vercel entrypoint: reuse the FastAPI app configured in app/main.py
from app.main import app  # noqa: F401

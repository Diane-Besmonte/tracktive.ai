from .config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .observability import RequestIdMiddleware, langsmith_status
from .tools.search import build_video_query
from .routes import router as app_router
from .routes_auth import router as auth_router
from .routes_sessions import router as sessions_router
from .database import engine
from .models import Base

app = FastAPI(title="Tracktive AI", version="0.1.0")

# CORS for frontend (dev + add prod later)
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://tracktive-ai-be.vercel.app",  # add on deploy
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,   # using Bearer tokens, not cookies
    allow_methods=["*"],       # lets OPTIONS pass
    allow_headers=["*"],       # Authorization, Content-Type, etc.
)

app.add_middleware(RequestIdMiddleware)
    
# create tables at startup (MVP)
@app.on_event("startup")
def _init_db():
    Base.metadata.create_all(bind=engine)

# routes
app.include_router(auth_router)
app.include_router(app_router)
app.include_router(sessions_router)

@app.get("/healthz")
def healthz():
    provider = "tavily" if settings.TAVILY_API_KEY else ("serpapi" if settings.SERPAPI_API_KEY else "none")
    return {
        "ok": True,
        "env": settings.APP_ENV,
        "tz": settings.TZ,
        "search_provider": provider,
        "sample_video_query": build_video_query("fastapi basics"),
    }

@app.get("/debug/langsmith")
def debug_langsmith(test: bool = True):
    return langsmith_status(test=test)
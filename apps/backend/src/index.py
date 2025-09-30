from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# allow your Vercel frontend later
ALLOWED = os.getenv("ALLOWED_ORIGINS", "").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in ALLOWED if o],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

@app.get("/healthz")
def ok(): return {"ok": True}

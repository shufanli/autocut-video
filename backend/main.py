"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import engine, Base
from auth import router as auth_router
from tasks import router as tasks_router

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AutoCut API",
    description="AI 口播视频自动剪辑 — 后端服务",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(tasks_router)


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


# Standalone quota endpoint (no task context needed)
from fastapi import Depends
from sqlalchemy.orm import Session as DBSession
from database import get_db
from auth import get_current_user
from models import User


@app.get("/api/quota")
def get_user_quota(user: User = Depends(get_current_user), db: DBSession = Depends(get_db)):
    """Get the current user's free quota remaining."""
    return {"free_quota_remaining": user.free_quota_remaining}

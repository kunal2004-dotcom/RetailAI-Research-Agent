from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from backend.app.models.database import get_db, SessionLocal
from backend.app.schemas.research_session import ResearchSessionCreate, ResearchSessionResponse, ResearchSessionDetailResponse
from backend.app.services.research_service import ResearchService

router = APIRouter()

import logging
import os
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

@router.get("/debug")
def debug_config():
    return {
        "os_env": bool(os.environ.get("OPENAI_API_KEY")),
        "settings_key": bool(settings.openai_api_key),
        "settings_val": settings.openai_api_key if settings.openai_api_key in ["dummy", "your_openai_api_key_here"] else ("REAL_KEY_HIDDEN" if settings.openai_api_key else None)
    }

def run_workflow_bg(session_id: int):
    logger.info(f"Background task starting. openai_api_key configured: {bool(settings.openai_api_key)}. Exact length: {len(settings.openai_api_key) if settings.openai_api_key else 0}. Is it 'dummy'? {settings.openai_api_key == 'dummy'}")
    db = SessionLocal()
    try:
        ResearchService.execute_workflow(db, session_id)
    finally:
        db.close()

@router.post("", response_model=ResearchSessionResponse, status_code=201)
def create_research_session(
    session_in: ResearchSessionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    session = ResearchService.create_session(db=db, session_in=session_in)
    background_tasks.add_task(run_workflow_bg, session.id)
    return session

@router.get("/{session_id}", response_model=ResearchSessionDetailResponse)
def get_research_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    session = ResearchService.get_session(db=db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")
    return session

@router.get("", response_model=List[ResearchSessionResponse])
def get_research_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return ResearchService.get_sessions(db=db, skip=skip, limit=limit)

@router.delete("/{session_id}", status_code=204)
def delete_research_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    success = ResearchService.delete_session(db=db, session_id=session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Research session not found")
    return None

"""Session management routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from web.api.models.responses import SessionListResponse, SessionResponse
from web.api.services.session_manager import session_manager

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse)
async def create_session():
    session = session_manager.create_session()
    return SessionResponse(
        session_id=session.session_id,
        output_dir=session.output_dir,
        created_at=session.created_at,
        phases_completed=session.phases_completed,
    )


@router.get("", response_model=SessionListResponse)
async def list_sessions():
    sessions = session_manager.list_sessions()
    return SessionListResponse(
        sessions=[
            SessionResponse(
                session_id=s.session_id,
                output_dir=s.output_dir,
                created_at=s.created_at,
                phases_completed=s.phases_completed,
            )
            for s in sessions
        ]
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(
        session_id=session.session_id,
        output_dir=session.output_dir,
        created_at=session.created_at,
        phases_completed=session.phases_completed,
    )

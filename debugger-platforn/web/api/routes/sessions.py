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


@router.post("/{session_id}/reset-phase/{phase}")
async def reset_phase(session_id: str, phase: str):
    """Reset a phase and all downstream phases so it can be re-run.

    E.g. resetting 'c' also resets 'd', but keeps 'a' and 'b' intact.
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if phase not in ("a", "b", "c", "d", "cert"):
        raise HTTPException(status_code=400, detail="Invalid phase")

    # Don't allow reset if the phase is currently running
    if session.phase_status.get(phase) == "running":
        raise HTTPException(status_code=409, detail=f"Phase {phase} is currently running")

    reset_phases = session_manager.reset_phase(session_id, phase)
    return {"reset_phases": reset_phases, "session_id": session_id}

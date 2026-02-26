"""Session state tracking for pipeline runs."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from web.api.config import OUTPUT_BASE_DIR


class Session:
    """Tracks the state of a single debugging session."""

    def __init__(self, session_id: str | None = None):
        self.session_id = session_id or f"session-{uuid.uuid4().hex[:8]}"
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.output_dir = str(OUTPUT_BASE_DIR / self.session_id)
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        self.phases_completed: list[str] = []
        self.phase_status: dict[str, str] = {"a": "idle", "b": "idle", "c": "idle", "d": "idle"}
        self.phase_results: dict[str, Any] = {}
        self.phase_progress: dict[str, dict[str, Any]] = {}  # phase -> {step, message, pct}
        self.artifacts: dict[str, str] = {}  # type -> file path

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "output_dir": self.output_dir,
            "created_at": self.created_at,
            "phases_completed": self.phases_completed,
            "phase_status": self.phase_status,
            "phase_results": self.phase_results,
        }


class SessionManager:
    """In-memory session store."""

    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def create_session(self) -> Session:
        session = Session()
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[Session]:
        return list(self._sessions.values())

    def set_phase_status(self, session_id: str, phase: str, status: str) -> None:
        session = self._sessions.get(session_id)
        if session:
            session.phase_status[phase] = status
            if status == "completed" and phase not in session.phases_completed:
                session.phases_completed.append(phase)

    def set_phase_result(self, session_id: str, phase: str, result: dict) -> None:
        session = self._sessions.get(session_id)
        if session:
            session.phase_results[phase] = result

    def set_phase_progress(self, session_id: str, phase: str, step: str, message: str, pct: int) -> None:
        session = self._sessions.get(session_id)
        if session:
            session.phase_progress[phase] = {"step": step, "message": message, "pct": pct}

    def set_artifact(self, session_id: str, artifact_type: str, path: str) -> None:
        session = self._sessions.get(session_id)
        if session:
            session.artifacts[artifact_type] = path


# Global singleton
session_manager = SessionManager()

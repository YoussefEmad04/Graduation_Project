"""
Main — FastAPI application for the Smart Academic Advisor.
Provides student chat, history, and admin endpoints.
"""

from typing import Any, Dict, List, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# ── FastAPI App ─────────────────────────────────────────────────────

app = FastAPI(
    title="Smart Academic Advisor",
    description="AI-powered academic advisor for AI and Cybersecurity programs",
    version="1.0.0",
)

# CORS for Flutter app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Lazy initialization ────────────────────────────────────────────
# Services are initialized on first request to avoid slow startup

_chat_controller = None
_elective_service = None


def get_chat_controller():
    """Lazy-load the chat controller."""
    global _chat_controller
    if _chat_controller is None:
        from advisor_ai.chat_controller import ChatController
        _chat_controller = ChatController()
    return _chat_controller


def get_elective_service():
    """Lazy-load the elective service."""
    global _elective_service
    if _elective_service is None:
        from advisor_ai.elective_service import ElectiveService
        _elective_service = ElectiveService()
    return _elective_service


def _dependency_error(error: Exception) -> Dict[str, Any]:
    """Format dependency failures without leaking secrets."""
    return {"connected": False, "last_error": str(error)}


# ── Request / Response Models ───────────────────────────────────────

class ChatRequest(BaseModel):
    student_id: str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    title: Optional[str] = None


class ChatResponse(BaseModel):
    student_id: str
    session_id: str
    response: str


class SessionCreateRequest(BaseModel):
    student_id: str = Field(..., min_length=1)
    title: Optional[str] = None


class SessionCreateResponse(BaseModel):
    student_id: str
    session_id: str
    title: str


class SessionSummary(BaseModel):
    student_id: Optional[str] = None
    session_id: str
    title: Optional[str] = None
    last_message: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TermRequest(BaseModel):
    term: str


class ElectiveTextRequest(BaseModel):
    electives: List[str] = Field(..., min_length=1)


class StatusResponse(BaseModel):
    status: str
    message: str


# ── Student Endpoints ───────────────────────────────────────────────

@app.post("/sessions", response_model=SessionCreateResponse)
def create_session(request: SessionCreateRequest):
    """Create a backend-owned chat session for one student."""
    controller = get_chat_controller()
    session = controller.create_session(request.student_id, title=request.title)
    return SessionCreateResponse(**session)


@app.get("/sessions", response_model=List[SessionSummary])
def list_sessions(student_id: Optional[str] = None):
    """List ChatGPT-style recent sessions as a JSON array."""
    controller = get_chat_controller()
    sessions = controller.list_sessions(student_id)
    return sessions


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Student chat endpoint.
    First message starts the identification flow (level → major).
    Subsequent messages are routed through the advisor graph.
    """
    controller = get_chat_controller()

    if request.message.strip().lower() in ["start", "new", "reset", "/start"]:
        response = controller.start_session(
            request.student_id,
            request.session_id,
            title=request.title,
        )
    else:
        response = controller.handle_message(
            request.student_id,
            request.session_id,
            request.message,
            title=request.title,
        )

    return ChatResponse(
        student_id=request.student_id,
        session_id=request.session_id,
        response=response,
    )


@app.get("/history")
def get_history(student_id: str, session_id: str):
    """Get chat history for a session."""
    controller = get_chat_controller()
    history = controller.get_history(student_id, session_id)
    return {"student_id": student_id, "session_id": session_id, "history": history}


# ── Admin Endpoints ─────────────────────────────────────────────────

@app.post("/admin/upload-electives", response_model=StatusResponse)
def upload_electives(request: ElectiveTextRequest):
    """
    Upload electives from a JSON list.
    """
    service = get_elective_service()
    electives = [elective.strip() for elective in request.electives if elective.strip()]

    if not electives:
        return StatusResponse(status="error", message="No electives provided.")

    service.set_electives(electives)
    return StatusResponse(
        status="success",
        message=f"Uploaded {len(electives)} electives: {', '.join(electives)}",
    )


@app.post("/admin/set-term", response_model=StatusResponse)
def set_term(request: TermRequest):
    """Update the active academic term."""
    service = get_elective_service()
    service.set_term(request.term)
    return StatusResponse(
        status="success",
        message=f"Active term updated to: {request.term}",
    )


@app.get("/admin/kg/status")
def kg_status():
    """Return Neo4j knowledge graph status."""
    try:
        controller = get_chat_controller()
        return controller.graph.kg_service.status()
    except Exception as e:
        return _dependency_error(e)


@app.get("/admin/rag/status")
def rag_status():
    """Return RAG vectorstore and extraction status."""
    try:
        controller = get_chat_controller()
        return controller.graph.rag_service.status()
    except Exception as e:
        return _dependency_error(e)


@app.get("/admin/history/status")
def history_status():
    """Return Supabase chat-history status."""
    try:
        from advisor_ai.supabase_client import supabase_status
        return supabase_status()
    except Exception as e:
        return _dependency_error(e)


# ── Health Check ────────────────────────────────────────────────────

@app.get("/")
def root():
    """Health check endpoint."""
    return {
        "service": "Smart Academic Advisor",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    """Dependency-aware health check endpoint."""
    return {
        "service": "Smart Academic Advisor",
        "status": "running",
        "version": "1.0.0",
        "dependencies": {
            "kg": kg_status(),
            "rag": rag_status(),
            "history": history_status(),
        },
    }


# ── Run Server ──────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("advisor_ai.main:app", host="0.0.0.0", port=8000, reload=True)

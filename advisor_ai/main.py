"""
Main — FastAPI application for the Smart Academic Advisor.
Provides student chat, history, and admin endpoints.
"""

import os
import tempfile
from typing import Any, Dict, Optional
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    response: str


class TermRequest(BaseModel):
    term: str


class ElectiveTextRequest(BaseModel):
    text: str


class StatusResponse(BaseModel):
    status: str
    message: str


# ── Student Endpoints ───────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Student chat endpoint.
    First message starts the identification flow (level → major).
    Subsequent messages are routed through the advisor graph.
    """
    controller = get_chat_controller()

    if request.message.strip().lower() in ["start", "new", "reset", "/start"]:
        response = controller.start_session(request.session_id)
    else:
        response = controller.handle_message(request.session_id, request.message)

    return ChatResponse(session_id=request.session_id, response=response)


@app.get("/history")
def get_history(session_id: str):
    """Get chat history for a session."""
    controller = get_chat_controller()
    history = controller.get_history(session_id)
    return {"session_id": session_id, "history": history}


# ── Admin Endpoints ─────────────────────────────────────────────────

@app.post("/admin/upload-electives", response_model=StatusResponse)
async def upload_electives(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
):
    """
    Upload electives from Excel, PDF, or plain text.
    - Send a file (Excel .xlsx or PDF .pdf)
    - OR send text in the 'text' form field
    """
    service = get_elective_service()

    if file:
        # Save uploaded file to temp location
        if not file.filename:
            return StatusResponse(status="error", message="Filename is missing")
        suffix = os.path.splitext(file.filename)[1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            if suffix in [".xlsx", ".xls"]:
                electives = service.upload_from_excel(tmp_path)
            elif suffix == ".pdf":
                electives = service.upload_from_pdf(tmp_path)
            elif suffix in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]:
                electives = service.upload_from_image(tmp_path)
            else:
                # Try as text
                text_content = content.decode("utf-8", errors="ignore")
                electives = service.upload_from_text(text_content)
        finally:
            os.unlink(tmp_path)

        return StatusResponse(
            status="success",
            message=f"Uploaded {len(electives)} electives: {', '.join(electives)}",
        )

    elif text:
        electives = service.upload_from_text(text)
        return StatusResponse(
            status="success",
            message=f"Uploaded {len(electives)} electives: {', '.join(electives)}",
        )

    return StatusResponse(status="error", message="No file or text provided.")


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

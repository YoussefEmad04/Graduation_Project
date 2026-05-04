"""
Chat Controller — Manages student sessions and chat history.
Persists all data to Supabase (sessions + messages tables).
No forced level/major selection — the system adapts dynamically.
"""

import re
import uuid
import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI

from advisor_ai.graph import AdvisorGraph
from advisor_ai.kg_service import KGService
from advisor_ai.supabase_client import get_supabase
from advisor_ai.constants import GREETINGS, GREETING_RESPONSE, HELP_INTENTS

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ChatController:
    """Manages chat sessions with Supabase persistence."""

    def __init__(self):
        self._graph = None
        self._title_llm = None
        try:
            self.db = get_supabase()
        except Exception as e:
            logger.error(f"Supabase unavailable; chat history will be disabled: {e}")
            self.db = None
        logger.info("Chat Controller initialized (Supabase)")

    @property
    def graph(self) -> AdvisorGraph:
        """Lazy-load the advisor graph only for endpoints that need AI services."""
        if self._graph is None:
            self._graph = AdvisorGraph()
        return self._graph

    # ── Session helpers ─────────────────────────────────────────────

    @property
    def title_llm(self):
        """Lazy-load a small LLM client for chat title generation."""
        if self._title_llm is None and os.getenv("OPENAI_API_KEY"):
            self._title_llm = ChatOpenAI(
                model=os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini"),
                temperature=0.2,
            )
        return self._title_llm

    @staticmethod
    def _now() -> str:
        """Return an ISO timestamp suitable for Supabase timestamptz fields."""
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _title_from_message(message: str) -> str:
        """Build a short recents title from the first useful user message."""
        title = re.sub(r"\s+", " ", message).strip()
        if not title:
            return "New chat"
        return title[:57].rstrip() + "..." if len(title) > 60 else title

    def _generate_session_title(self, message: str) -> str:
        """Generate a short chat title with OpenAI, falling back to message preview."""
        fallback = self._title_from_message(message)
        llm = self.title_llm
        if not llm:
            return fallback

        prompt = (
            "Generate a short chat title for this student advisor conversation.\n"
            "Rules:\n"
            "- Return only the title, with no explanation.\n"
            "- Use 3 to 7 words when possible.\n"
            "- Preserve the user's language if the message is Arabic, English, or Arabizi.\n"
            "- Do not wrap the title in quotes.\n"
            "- Do not include trailing punctuation.\n\n"
            f"Student message: {message}"
        )
        try:
            result = llm.invoke(prompt)
            title = str(getattr(result, "content", "")).strip()
            title = re.sub(r"^(title|chat title)\s*:\s*", "", title, flags=re.IGNORECASE)
            title = title.strip().strip("\"'`“”‘’").strip()
            title = re.sub(r"\s+", " ", title)
            title = title.rstrip(".؟?!،,;:")
            return self._title_from_message(title) if title else fallback
        except Exception as e:
            logger.error(f"Error generating session title: {e}")
            return fallback

    def _get_session(
        self,
        student_id: str,
        session_id: str,
        title: Optional[str] = None,
    ) -> dict:
        """Get or create a session from Supabase."""
        if not self.db:
            return {"student_id": student_id, "session_id": session_id}
        try:
            result = (
                self.db.table("sessions")
                .select("*")
                .eq("student_id", student_id)
                .eq("session_id", session_id)
                .execute()
            )
            if result.data:
                return result.data[0]

            new_session = {
                "student_id": student_id,
                "session_id": session_id,
                "title": title or "New chat",
                "student_level": None,
                "student_major": None,
                "updated_at": self._now(),
            }
            self.db.table("sessions").insert(new_session).execute()
            return new_session
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return {"student_id": student_id, "session_id": session_id}

    def _update_session(self, student_id: str, session_id: str, updates: dict):
        """Update session fields in Supabase."""
        if not self.db:
            return
        try:
            updates.setdefault("updated_at", self._now())
            (
                self.db.table("sessions")
                .update(updates)
                .eq("student_id", student_id)
                .eq("session_id", session_id)
                .execute()
            )
        except Exception as e:
            logger.error(f"Error updating session: {e}")

    def _save_message(self, student_id: str, session_id: str, role: str, content: str):
        """Insert a message into Supabase."""
        if not self.db:
            return
        try:
            self.db.table("messages").insert(
                {
                    "student_id": student_id,
                    "session_id": session_id,
                    "role": role,
                    "content": content,
                }
            ).execute()
            self._update_session(student_id, session_id, {})
        except Exception as e:
            logger.error(f"Error saving message: {e}")

    def _ensure_title(self, session: dict, student_id: str, session_id: str, message: str):
        """Set the recents title from the first real message when no custom title exists."""
        if session.get("title") and session["title"] != "New chat":
            return
        title = self._generate_session_title(message)
        self._update_session(student_id, session_id, {"title": title})
        session["title"] = title

    # ── Level extraction ────────────────────────────────────────────

    def _extract_level(self, message: str):
        """Try to extract a student level (1-4) from a message."""
        m = re.search(
            r"(?:level|lvl|سنة|المستوى|لفل)\s*(\d)", message, re.IGNORECASE
        )
        if m and m.group(1) in "1234":
            return int(m.group(1))
        return None

    # ── Public API ──────────────────────────────────────────────────

    def create_session(self, student_id: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Create a new backend-owned chat session for a student."""
        session_id = str(uuid.uuid4())
        session_title = title or "New chat"
        session = {
            "student_id": student_id,
            "session_id": session_id,
            "title": session_title,
            "student_level": None,
            "student_major": None,
            "updated_at": self._now(),
        }
        if self.db:
            try:
                self.db.table("sessions").insert(session).execute()
            except Exception as e:
                logger.error(f"Error creating session: {e}")
        return {
            "student_id": student_id,
            "session_id": session_id,
            "title": session_title,
        }

    def list_sessions(self, student_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return ChatGPT-style recents, optionally filtered to one student."""
        if not self.db:
            return []
        try:
            query = (
                self.db.table("sessions")
                .select("student_id, session_id, title, created_at, updated_at")
            )
            if student_id:
                query = query.eq("student_id", student_id)
            result = query.order("updated_at", desc=True).execute()
            sessions = result.data if result.data else []
            for session in sessions:
                latest_query = (
                    self.db.table("messages")
                    .select("content")
                    .eq("session_id", session["session_id"])
                )
                if session.get("student_id"):
                    latest_query = latest_query.eq("student_id", session["student_id"])
                latest = latest_query.order("created_at", desc=True).limit(1).execute()
                content = latest.data[0]["content"] if latest.data else ""
                session["last_message"] = self._title_from_message(content) if content else ""
            return sessions
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []

    def get_history(self, student_id: str, session_id: str) -> List[Dict[str, Any]]:
        """Get chat history from Supabase (as dicts)."""
        if not self.db:
            return []
        try:
            result = (
                self.db.table("messages")
                .select("role, content, created_at")
                .eq("student_id", student_id)
                .eq("session_id", session_id)
                .order("created_at")
                .execute()
            )
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error fetching history: {e}")
            return []

    def _get_history_objects(self, student_id: str, session_id: str) -> List[BaseMessage]:
        """Get chat history as LangChain message objects."""
        raw_history = self.get_history(student_id, session_id)
        messages: List[BaseMessage] = []
        session = self._get_session(student_id, session_id)
        memory_summary = self._build_memory_summary(raw_history, session)
        if memory_summary:
            messages.append(SystemMessage(content=memory_summary))
        for msg in raw_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        return messages

    @staticmethod
    def _compact_text(text: str, limit: int = 220) -> str:
        """Compact long history snippets for internal memory context."""
        compact = re.sub(r"\s+", " ", text or "").strip()
        return compact[: limit - 3].rstrip() + "..." if len(compact) > limit else compact

    def _build_memory_summary(self, raw_history: List[Dict[str, Any]], session: dict) -> str:
        """Build a lightweight per-session memory summary from stored history."""
        if not raw_history and not (session.get("student_level") or session.get("student_major")):
            return ""

        lines = ["Session memory summary:"]
        if session.get("student_level"):
            lines.append(f"- Student level: {session['student_level']}")
        if session.get("student_major"):
            lines.append(f"- Student major: {session['student_major']}")

        recent = raw_history[-8:]
        last_user = next((m for m in reversed(recent) if m.get("role") == "user"), None)
        last_assistant = next((m for m in reversed(recent) if m.get("role") == "assistant"), None)

        if last_user:
            lines.append(f"- Last student question: {self._compact_text(last_user.get('content', ''))}")
        if last_assistant:
            lines.append(f"- Last advisor answer: {self._compact_text(last_assistant.get('content', ''))}")

        joined = "\n".join(m.get("content", "") for m in recent)
        course_codes = sorted(set(re.findall(r"\b[A-Z]{2,4}\d{3}\b", joined)))
        if course_codes:
            lines.append(f"- Recently discussed course codes: {', '.join(course_codes[-8:])}")

        topics = []
        normalized = joined.lower()
        topic_markers = {
            "withdrawal": ("withdraw", "withdrawal", "انسحاب", "ينسحب", "اسحب"),
            "transfer": ("transfer", "تحويل", "احول", "التحويل"),
            "admission": ("admission", "قبول", "القبول"),
            "graduation": ("graduation", "تخرج", "التخرج"),
            "cgpa": ("cgpa", "gpa", "معدل", "التراكمي"),
            "attendance": ("attendance", "غياب", "حضور"),
            "prerequisites": ("prerequisite", "متطلب", "متطلبات", "قبلها", "تفتح"),
        }
        for topic, markers in topic_markers.items():
            if any(marker in normalized for marker in markers):
                topics.append(topic)
        if topics:
            lines.append(f"- Recently discussed topics: {', '.join(topics)}")

        return "\n".join(lines)

    @staticmethod
    def _format_response(response: str) -> str:
        """Apply final chatbot formatting rules before storing/returning."""
        return AdvisorGraph._clean_response_format(response)

    def start_session(self, student_id: str, session_id: str, title: Optional[str] = None) -> str:
        """Start or reset a chat session."""
        if not self.db:
            return GREETING_RESPONSE
        try:
            self._get_session(student_id, session_id, title=title)
            self._update_session(student_id, session_id, {
                "student_level": None,
                "student_major": None,
                "title": title or "New chat",
            })
            (
                self.db.table("messages")
                .delete()
                .eq("student_id", student_id)
                .eq("session_id", session_id)
                .execute()
            )

            self._save_message(student_id, session_id, "assistant", GREETING_RESPONSE)
            return GREETING_RESPONSE
        except Exception as e:
            logger.error(f"Error starting session: {e}")
            return "Welcome! (Error resetting session)"

    def handle_message(
        self,
        student_id: str,
        session_id: str,
        message: str,
        title: Optional[str] = None,
    ) -> str:
        """Process a student message."""
        session = self._get_session(student_id, session_id, title=title)
        msg_lower = message.strip().lower()

        # ── Greeting ────────────────────────────────────────────────
        if msg_lower in GREETINGS:
            response = self._format_response(GREETING_RESPONSE)
            self._save_message(student_id, session_id, "user", message)
            self._save_message(student_id, session_id, "assistant", response)
            return response

        if any(intent in msg_lower for intent in HELP_INTENTS):
            response = self._format_response(GREETING_RESPONSE)
            self._save_message(student_id, session_id, "user", message)
            self._save_message(student_id, session_id, "assistant", response)
            return response

        # ── Standalone level selection (just "1", "2", "3", "4") ───
        if msg_lower in ["1", "2", "3", "4"]:
            level = int(msg_lower)
            major = "General" if level <= 2 else None
            self._update_session(student_id, session_id, {
                "student_level": level,
                "student_major": major,
            })
            response = (
                f"Got it, you're in Level {level}.\n"
                f"Ask me anything about courses, prerequisites, regulations, or electives."
            )
            response = self._format_response(response)
            self._save_message(student_id, session_id, "user", message)
            self._save_message(student_id, session_id, "assistant", response)
            return response

        # ── Extract level from natural text if not already known ────
        if not session.get("student_level"):
            level = self._extract_level(message)
            if level:
                major = "General" if level <= 2 else None
                self._update_session(student_id, session_id, {
                    "student_level": level,
                    "student_major": major,
                })
                session["student_level"] = level
                session["student_major"] = major

        # ── Route through advisor graph ─────────────────────────────
        # Convert previous history for context-aware routing before storing this turn.
        self._ensure_title(session, student_id, session_id, message)
        history = self._get_history_objects(student_id, session_id)
        self._save_message(student_id, session_id, "user", message)

        if KGService._looks_like_category_hours_query(message):
            response = self.graph.kg_service.query(message)
            response = self._format_response(response)
            self._save_message(student_id, session_id, "assistant", response)
            return response
        
        try:
            response = self.graph.run(
                question=message,
                history=history,
                student_level=session.get("student_level"),
                student_major=session.get("student_major") or "General",
            )
        except Exception as e:
            logger.error(f"Graph run error: {e}")
            response = (
                "I'm sorry, I encountered an error. "
                "Please try again or rephrase your question."
            )

        response = self._format_response(response)
        self._save_message(student_id, session_id, "assistant", response)
        return response

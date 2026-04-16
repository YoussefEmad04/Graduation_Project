"""
Chat Controller — Manages student sessions and chat history.
Persists all data to Supabase (sessions + messages tables).
No forced level/major selection — the system adapts dynamically.
"""

import re
import logging
from typing import List, Dict, Any

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from advisor_ai.graph import AdvisorGraph
from advisor_ai.supabase_client import get_supabase
from advisor_ai.constants import GREETINGS, GREETING_RESPONSE

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ChatController:
    """Manages chat sessions with Supabase persistence."""

    def __init__(self):
        self._graph = None
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

    def _get_session(self, session_id: str) -> dict:
        """Get or create a session from Supabase."""
        if not self.db:
            return {"session_id": session_id}
        try:
            result = (
                self.db.table("sessions")
                .select("*")
                .eq("session_id", session_id)
                .execute()
            )
            if result.data:
                return result.data[0]

            new_session = {
                "session_id": session_id,
                "student_level": None,
                "student_major": None,
            }
            self.db.table("sessions").insert(new_session).execute()
            return new_session
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return {"session_id": session_id}

    def _update_session(self, session_id: str, updates: dict):
        """Update session fields in Supabase."""
        if not self.db:
            return
        try:
            self.db.table("sessions").update(updates).eq(
                "session_id", session_id
            ).execute()
        except Exception as e:
            logger.error(f"Error updating session: {e}")

    def _save_message(self, session_id: str, role: str, content: str):
        """Insert a message into Supabase."""
        if not self.db:
            return
        try:
            self.db.table("messages").insert(
                {"session_id": session_id, "role": role, "content": content}
            ).execute()
        except Exception as e:
            logger.error(f"Error saving message: {e}")

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

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get chat history from Supabase (as dicts)."""
        if not self.db:
            return []
        try:
            result = (
                self.db.table("messages")
                .select("role, content, created_at")
                .eq("session_id", session_id)
                .order("created_at")
                .execute()
            )
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error fetching history: {e}")
            return []

    def _get_history_objects(self, session_id: str) -> List[BaseMessage]:
        """Get chat history as LangChain message objects."""
        raw_history = self.get_history(session_id)
        messages: List[BaseMessage] = []
        for msg in raw_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        return messages

    def start_session(self, session_id: str) -> str:
        """Start or reset a chat session."""
        if not self.db:
            return GREETING_RESPONSE
        try:
            self.db.table("sessions").upsert(
                {"session_id": session_id, "student_level": None, "student_major": None}
            ).execute()
            self.db.table("messages").delete().eq("session_id", session_id).execute()

            self._save_message(session_id, "assistant", GREETING_RESPONSE)
            return GREETING_RESPONSE
        except Exception as e:
            logger.error(f"Error starting session: {e}")
            return "Welcome! (Error resetting session)"

    def handle_message(self, session_id: str, message: str) -> str:
        """Process a student message."""
        session = self._get_session(session_id)
        msg_lower = message.strip().lower()

        # ── Greeting ────────────────────────────────────────────────
        if msg_lower in GREETINGS:
            response = GREETING_RESPONSE
            self._save_message(session_id, "user", message)
            self._save_message(session_id, "assistant", response)
            return response

        # ── Standalone level selection (just "1", "2", "3", "4") ───
        if msg_lower in ["1", "2", "3", "4"]:
            level = int(msg_lower)
            major = "General" if level <= 2 else None
            self._update_session(session_id, {
                "student_level": level,
                "student_major": major,
            })
            response = (
                f"Got it, you're in Level {level}.\n"
                f"Ask me anything about courses, prerequisites, regulations, or electives."
            )
            self._save_message(session_id, "user", message)
            self._save_message(session_id, "assistant", response)
            return response

        # ── Extract level from natural text if not already known ────
        if not session.get("student_level"):
            level = self._extract_level(message)
            if level:
                major = "General" if level <= 2 else None
                self._update_session(session_id, {
                    "student_level": level,
                    "student_major": major,
                })
                session["student_level"] = level
                session["student_major"] = major

        # ── Route through advisor graph ─────────────────────────────
        # Convert previous history for context-aware routing before storing this turn.
        history = self._get_history_objects(session_id)
        self._save_message(session_id, "user", message)
        
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

        self._save_message(session_id, "assistant", response)
        return response

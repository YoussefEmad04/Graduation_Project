"""
Semantic Router Service.

Uses an LLM to classify the user's intent semantically, rewrite the question
into a cleaner internal form, and expose a confidence score. The graph can
trust this router when confidence is high and fall back to heuristic routing
otherwise.
"""

import logging
import os
from typing import Dict, List, Optional

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class RouterDecision(BaseModel):
    route: str = Field(description="One of: rag, kg, mental, elective, hybrid")
    sub_intent: str = Field(default="", description="More specific meaning such as prerequisite, reverse_prerequisite, regulation, study_path, support, major_guidance")
    rewritten_question: str = Field(default="", description="A cleaner internal version of the student's question that preserves meaning")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Router confidence from 0 to 1")
    entities: Dict[str, str] = Field(default_factory=dict, description="Resolved entities like course, program, level, policy topic")
    reasoning: str = Field(default="", description="Very short rationale for debugging")


ROUTER_SYSTEM_PROMPT = """You route student questions for the Smart Academic Advisor.

Available routes:
- rag: academic regulations, policies, grading, attendance, withdrawal, CGPA rules, semester duration, graduation requirements, study-plan tables from the regulation document
- kg: course prerequisites, what a course opens, course/category/program curriculum structure, level-based course plans from the knowledge graph
- mental: emotional distress, motivation, study support, major selection guidance
- elective: currently available elective offerings for the active term
- hybrid: unclear or mixed question

Rules:
- Understand English, Arabic, Egyptian Arabic, Arabizi, and mixed Arabic/English questions.
- Route by meaning, not by exact wording.
- If the question asks what is needed before a course, use route=kg and sub_intent=prerequisite.
- If the question asks what a course opens after finishing it, use route=kg and sub_intent=reverse_prerequisite.
- If the question asks about official academic rules or regulations, use route=rag.
- If the question asks for emotional or motivational help, use route=mental.
- If the question asks what electives are available this term, use route=elective.
- If the question is vague but conversation history clarifies it, use the history.
- Keep rewritten_question faithful to the student's meaning, but make it clearer and more canonical.
- Use confidence above 0.8 only when the route is clearly supported by the meaning.

Return JSON only.
"""


class RouterService:
    """LLM-powered semantic router with structured output."""

    def __init__(self):
        self.llm = None
        self.parser = JsonOutputParser(pydantic_object=RouterDecision)

        if os.getenv("OPENAI_API_KEY"):
            self.llm = ChatOpenAI(
                model=os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini"),
                temperature=0,
            )
            logger.info("Router Service initialized (LLM-powered)")
        else:
            logger.warning("OPENAI_API_KEY is not configured; Router Service disabled")

    def route_question(
        self,
        question: str,
        history: Optional[List[BaseMessage]] = None,
        student_level: Optional[int] = None,
        student_major: Optional[str] = None,
    ) -> Optional[RouterDecision]:
        """Classify the question semantically and return a router decision."""
        if not self.llm:
            return None

        prompt = ChatPromptTemplate.from_messages([
            ("system", ROUTER_SYSTEM_PROMPT),
            ("user", "Conversation history:\n{history}\n\nCurrent question:\n{question}"),
        ])
        chain = prompt | self.llm | self.parser

        try:
            result = chain.invoke({
                "question": question,
                "history": self._format_history(
                    history,
                    student_level=student_level,
                    student_major=student_major,
                ),
            })
            if isinstance(result, dict):
                return RouterDecision(**result)
            if isinstance(result, RouterDecision):
                return result
            return None
        except Exception as exc:
            logger.error(f"Router classification failed: {exc}")
            return None

    @staticmethod
    def _format_history(
        history: Optional[List[BaseMessage]],
        student_level: Optional[int] = None,
        student_major: Optional[str] = None,
    ) -> str:
        """Render a short history block for the router."""
        lines: List[str] = []
        if student_level is not None:
            lines.append(f"Student level: {student_level}")
        if student_major:
            lines.append(f"Student major: {student_major}")
        if not history:
            lines.append("Conversation: None")
            return "\n".join(lines)

        memory_messages = [message for message in history if isinstance(message, SystemMessage)]
        for message in memory_messages[-1:]:
            lines.append(f"Memory: {message.content}")

        non_memory = [message for message in history if not isinstance(message, SystemMessage)]
        for message in non_memory[-6:]:
            if isinstance(message, HumanMessage):
                role = "Student"
            elif isinstance(message, AIMessage):
                role = "Advisor"
            else:
                role = "Message"
            lines.append(f"{role}: {message.content}")
        return "\n".join(lines)

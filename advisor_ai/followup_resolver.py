"""
Semantic follow-up resolver.

Turns a context-dependent student message into either a standalone question
or a clarification prompt before the graph routes it to a service.
"""

import logging
import os
from typing import Dict, List, Optional

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class FollowupDecision(BaseModel):
    is_followup: bool = Field(description="Whether the current question depends on earlier conversation context")
    needs_clarification: bool = Field(default=False, description="Whether the reference is too ambiguous to answer safely")
    clarification_question: str = Field(default="", description="Short question asking the student what they mean")
    route: str = Field(default="", description="Best route if known: rag, kg, mental, elective, or hybrid")
    sub_intent: str = Field(default="", description="More specific intent such as prerequisite, regulation, support")
    rewritten_question: str = Field(default="", description="Standalone version of the student's question")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Resolver confidence from 0 to 1")
    entities: Dict[str, str] = Field(default_factory=dict, description="Resolved entities like course code, course name, or policy topic")
    reasoning: str = Field(default="", description="Very short rationale for debugging")


FOLLOWUP_SYSTEM_PROMPT = """You resolve follow-up questions for the Smart Academic Advisor.

The current student message may depend on earlier conversation context.

Available routes:
- rag: academic regulations, policies, grading, attendance, withdrawal, CGPA rules, semester duration, graduation requirements, study-plan tables
- kg: course prerequisites, what a course opens, course/category/program curriculum structure, level-based course plans
- mental: emotional distress, motivation, study support, major selection guidance
- elective: currently available elective offerings for the active term
- hybrid: unclear or mixed question

Rules:
- Understand English, Arabic, Egyptian Arabic, Arabizi, and mixed Arabic/English.
- Mark is_followup=true only when the current message clearly depends on previous context.
- If it is a follow-up and the reference is clear, rewrite it as a standalone question.
- If the current message is a new standalone topic, even if it starts with words like "and", "what about", "طيب", "طب", or "also", set is_followup=false.
- For standalone context switches, set route/sub_intent/entities from the current message only and do not let older history influence the route.
- Preserve the student's meaning. Do not invent course names, policies, or student details.
- If more than one prior topic could be the referent, set needs_clarification=true and write a short clarification question.
- If the current message is already standalone, set is_followup=false. You may leave rewritten_question empty or provide a clearer standalone wording of the current message only.
- Language is strict: English-only current messages get English rewritten_question/clarification_question.
- Arabic, Egyptian Arabic, Arabizi, or mixed Arabic-English current messages get Arabic rewritten_question/clarification_question. Preserve course codes, course names, CGPA, W, I, FA, and program names in English when useful.
- Use confidence above 0.8 only when the rewrite or clarification is clearly supported by history.

Examples:
- History is about regular-semester credit load. Current: "طيب ايه متطلبات AI301؟"
  Return is_followup=false, route=kg, sub_intent=prerequisites_for_course, rewritten_question="ايه متطلبات AI301؟".
- History is about AI301 prerequisites. Current: "طيب الحد الأقصى للساعات في الترم العادي كام؟"
  Return is_followup=false, route=rag, sub_intent=regulation, rewritten_question="طيب الحد الأقصى للساعات في الترم العادي كام؟".
- History is about AI301 prerequisites. Current: "طيب بتفتح ايه؟"
  Return is_followup=true, route=kg, sub_intent=courses_unlocked_by_course, rewritten_question="مادة AI301 بتفتح ايه؟".
- History is about summer semester duration. Current: "طيب ايه متطلبات Machine Learning؟"
  Return is_followup=false, route=kg, sub_intent=prerequisites_for_course, rewritten_question="ايه متطلبات Machine Learning؟".

Return JSON only.
"""


class FollowupResolver:
    """LLM-powered follow-up classifier and rewriter."""

    def __init__(self):
        self.llm = None
        self.parser = JsonOutputParser(pydantic_object=FollowupDecision)

        if os.getenv("OPENAI_API_KEY"):
            self.llm = ChatOpenAI(
                model=os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini"),
                temperature=0,
            )
            logger.info("Follow-up Resolver initialized (LLM-powered)")
        else:
            logger.warning("OPENAI_API_KEY is not configured; Follow-up Resolver disabled")

    def resolve(
        self,
        question: str,
        history: Optional[List[BaseMessage]] = None,
        student_level: Optional[int] = None,
        student_major: Optional[str] = None,
    ) -> Optional[FollowupDecision]:
        """Return a semantic follow-up decision, or None if unavailable."""
        if not self.llm or not history:
            return None

        prompt = ChatPromptTemplate.from_messages([
            ("system", FOLLOWUP_SYSTEM_PROMPT),
            ("user", "Conversation history:\n{history}\n\nCurrent student message:\n{question}"),
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
                return self._normalize_decision(FollowupDecision(**result))
            if isinstance(result, FollowupDecision):
                return self._normalize_decision(result)
            return None
        except Exception as exc:
            logger.error(f"Follow-up resolution failed: {exc}")
            return None

    @staticmethod
    def _normalize_decision(decision: FollowupDecision) -> FollowupDecision:
        """Treat omitted confidence on clear structured LLM decisions as usable confidence."""
        has_action = (
            decision.needs_clarification
            or bool(decision.rewritten_question)
            or decision.route in {"rag", "kg", "mental", "elective"}
        )
        if decision.confidence == 0.0 and has_action:
            decision.confidence = 0.8
        return decision

    @staticmethod
    def _format_history(
        history: Optional[List[BaseMessage]],
        student_level: Optional[int] = None,
        student_major: Optional[str] = None,
    ) -> str:
        """Render a compact history block for follow-up resolution."""
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
        for message in non_memory[-8:]:
            if isinstance(message, HumanMessage):
                role = "Student"
            elif isinstance(message, AIMessage):
                role = "Advisor"
            else:
                role = "Message"
            lines.append(f"{role}: {message.content}")
        return "\n".join(lines)

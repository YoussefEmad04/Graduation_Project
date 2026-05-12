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
    sub_intent: str = Field(default="", description="More specific meaning such as prerequisites_for_course, courses_unlocked_by_course, courses_blocked_if_not_completed, prerequisite, reverse_prerequisite, regulation, study_path, support, major_guidance")
    intent: str = Field(default="", description="Semantic intent such as course_prerequisite_query, course_unlock_query, study_plan_query, category_requirement_query, regulation_query, student_record_query, or general_chat")
    rewritten_question: str = Field(default="", description="A cleaner internal version of the student's question that preserves meaning")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Router confidence from 0 to 1")
    entities: Dict[str, str] = Field(default_factory=dict, description="Resolved entities like course, program, level, policy topic")
    reasoning: str = Field(default="", description="Very short rationale for debugging")
    reasoning_summary: str = Field(default="", description="Short explanation of the semantic decision")


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
- Return a semantic intent in the "intent" field. Supported intents:
  course_prerequisite_query, course_unlock_query, study_plan_query,
  category_requirement_query, regulation_query, student_record_query, general_chat.
- If the question asks what is needed before a course, use route=kg and sub_intent=prerequisites_for_course.
- If the question asks for "requirements", "متطلبات", "المتطلبات", or "المطلوب" for a specific course code/name, use route=kg and sub_intent=prerequisites_for_course, not rag.
- If the phrase means "المادة اللي بتفتحها" or "لازم آخد ايه قبلها", use sub_intent=prerequisites_for_course.
- If the phrase means "المادة دي بتفتح ايه", use sub_intent=courses_unlocked_by_course.
- If the phrase means "لو مخدتهاش / لو مسجلتهاش / مش هتفتحلي ايه", use sub_intent=courses_blocked_if_not_completed.
- If the question asks what a course opens after finishing it, use route=kg and sub_intent=courses_unlocked_by_course.
- If the question asks for graduation requirements, credit-hour regulations, GPA rules, attendance rules, withdrawal rules, or semester limits, use route=rag.
- If the question asks about official academic rules or regulations, use route=rag.
- If the question asks for emotional or motivational help, use route=mental.
- If the question asks what electives are available this term, use route=elective.
- If the question is vague but conversation history clarifies it, use the history.
- Keep rewritten_question faithful to the student's meaning, but make it clearer and more canonical.
- Use confidence above 0.8 only when the route is clearly supported by the meaning.

Examples:
- "طيب ايه متطلبات AI301؟" -> intent=course_prerequisite_query, route=kg, sub_intent=prerequisites_for_course, rewritten_question="ايه متطلبات AI301؟", entities={{"course":"AI301"}}
- "What are the requirements for Machine Learning?" -> intent=course_prerequisite_query, route=kg, sub_intent=prerequisites_for_course, entities={{"course":"Machine Learning"}}
- "Machine Learning بتفتح مواد ايه؟" -> intent=course_unlock_query, route=kg, sub_intent=courses_unlocked_by_course, entities={{"course":"Machine Learning"}}
- "لو مخدتش Machine Learning ايه المواد اللي هتقفل؟" -> intent=course_unlock_query, route=kg, sub_intent=courses_blocked_if_not_completed, entities={{"course":"Machine Learning"}}
- "ايه مواد سنة تالته ذكاء اصطناعي؟" -> intent=study_plan_query, route=kg, sub_intent=study_path, entities={{"level":"3","program":"Artificial Intelligence"}}
- "ايه متطلبات الجامعة الاجبارية؟" -> intent=category_requirement_query, route=kg, sub_intent=category_query, entities={{"category":"University Requirements","requirement_type":"compulsory"}}
- "What are the graduation requirements?" -> intent=regulation_query, route=rag, sub_intent=regulation
- "طيب الحد الأقصى للساعات في الترم العادي كام؟" -> route=rag, sub_intent=regulation

Return strict JSON only with:
intent, route, sub_intent, entities, confidence, reasoning_summary, rewritten_question.
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
                return self._normalize_decision(RouterDecision(**result))
            if isinstance(result, RouterDecision):
                return self._normalize_decision(result)
            return None
        except Exception as exc:
            logger.error(f"Router classification failed: {exc}")
            return None

    @staticmethod
    def _normalize_decision(decision: RouterDecision) -> RouterDecision:
        """Treat omitted confidence on clear structured LLM routes as usable confidence."""
        if not decision.reasoning and decision.reasoning_summary:
            decision.reasoning = decision.reasoning_summary
        if not decision.intent:
            decision.intent = RouterService._intent_from_route(decision.route, decision.sub_intent)
        if decision.confidence == 0.0 and decision.route in {"rag", "kg", "mental", "elective"}:
            decision.confidence = 0.8
        return decision

    @staticmethod
    def _intent_from_route(route: str, sub_intent: str) -> str:
        if route == "kg" and sub_intent in {"prerequisite", "prerequisites_for_course"}:
            return "course_prerequisite_query"
        if route == "kg" and sub_intent in {"reverse_prerequisite", "courses_unlocked_by_course", "courses_blocked_if_not_completed"}:
            return "course_unlock_query"
        if route == "kg" and sub_intent in {"study_path", "study_plan"}:
            return "study_plan_query"
        if route == "kg" and sub_intent in {"category_query", "category_required_hours"}:
            return "category_requirement_query"
        if route == "rag":
            return "regulation_query"
        if route == "hybrid":
            return "general_chat"
        return sub_intent or route or "general_chat"

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

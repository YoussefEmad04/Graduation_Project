"""
Advisor Graph — LangGraph workflow for the Smart Academic Advisor.
Routes student queries to the appropriate service node, then combines
results in a hybrid node for the final answer.

Flow: router → rag_node / kg_node / mental_node / elective_node → hybrid_node → text output
NO loops. NO multi-agent system.
"""

import os
import logging
import re
import difflib
from typing import Any, TypedDict, Optional, List, Dict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.graph import StateGraph, END

from advisor_ai.rag_service import RAGService
from advisor_ai.kg_service import KGService
from advisor_ai.mental_service import MentalSupportService
from advisor_ai.elective_service import ElectiveService
from advisor_ai.router_service import RouterService
from advisor_ai.language_utils import contains_arabic, should_respond_arabic, strict_language_instruction
from advisor_ai.constants import (
    RAG_KEYWORDS, KG_KEYWORDS, ELECTIVE_KEYWORDS, MENTAL_KEYWORDS, 
    MAJOR_KEYWORDS, PATH_KEYWORDS, KG_SYNTHESIS_PROMPT
)

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

OUT_OF_SCOPE_EN = "I couldn't find this specific question in our course data or regulation documents."
OUT_OF_SCOPE_AR = "مش لاقي السؤال ده في بيانات المواد أو مستندات اللوايح عندي."

# ── State Definition ────────────────────────────────────────────────

class AdvisorState(TypedDict):
    """State that flows through the graph."""
    question: str
    student_level: Optional[int]
    student_major: Optional[str]
    history: List[BaseMessage]
    route: Optional[str]          # which node to route to
    route_sub_intent: Optional[str]
    rewritten_question: Optional[str]
    route_confidence: Optional[float]
    route_reasoning: Optional[str]
    route_entities: Optional[Dict[str, str]]
    route_missing_entities: Optional[List[str]]
    rag_answer: Optional[str]
    kg_answer: Optional[str]
    mental_answer: Optional[str]
    elective_answer: Optional[str]
    final_answer: Optional[str]


# ── Advisor Graph Class ─────────────────────────────────────────────

class AdvisorGraph:
    """LangGraph-based workflow for the academic advisor."""

    def __init__(self):
        # Initialize services
        self.rag_service = RAGService()
        self.kg_service = KGService()
        self.mental_service = MentalSupportService()
        self.elective_service = ElectiveService()
        self.router_service = RouterService()

        # LLM for hybrid reasoning
        self.llm = None
        if os.getenv("OPENAI_API_KEY"):
            self.llm = ChatOpenAI(
                model=os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini"),
                temperature=0.3,
            )
        else:
            logger.warning("OPENAI_API_KEY is not configured; AdvisorGraph will use non-LLM fallbacks")

        # Cache course names for routing
        self.course_names = self.kg_service.get_all_course_names()

        # Build the graph
        self.graph = self._build_graph()
        logger.info("Advisor Graph initialized")

    def _build_graph(self):
        """Build the LangGraph workflow."""
        workflow = StateGraph(AdvisorState)

        # Add nodes
        workflow.add_node("router", self._router_node)
        workflow.add_node("rag_node", self._rag_node)
        workflow.add_node("kg_node", self._kg_node)
        workflow.add_node("mental_node", self._mental_node)
        workflow.add_node("elective_node", self._elective_node)
        workflow.add_node("hybrid_node", self._hybrid_node)

        # Set entry point
        workflow.set_entry_point("router")

        # Conditional routing from router
        workflow.add_conditional_edges(
            "router",
            self._route_decision,
            {
                "rag": "rag_node",
                "kg": "kg_node",
                "mental": "mental_node",
                "elective": "elective_node",
                "hybrid": "hybrid_node",
            },
        )

        # All service nodes → hybrid_node
        workflow.add_edge("rag_node", "hybrid_node")
        workflow.add_edge("kg_node", "hybrid_node")
        workflow.add_edge("mental_node", "hybrid_node")
        workflow.add_edge("elective_node", "hybrid_node")

        # Hybrid → END
        workflow.add_edge("hybrid_node", END)

        return workflow.compile()

    # ── Node Implementations ────────────────────────────────────────

    def _router_node(self, state: AdvisorState) -> dict:
        """Classify the question and determine the route."""
        question = state["question"]
        routing_history: List[BaseMessage] = []
        normalized = self._normalize_text(question)
        signals = self._deterministic_routing_signals(question)
        router_service = getattr(self, "router_service", None)

        if self._is_unsupported_course_metadata_query(question):
            logger.info("Question returned out of scope (unsupported course metadata)")
            return {
                "route": "hybrid",
                "route_sub_intent": "unsupported_course_metadata",
                "rewritten_question": question,
                "route_confidence": 1.0,
                "route_reasoning": "Unsupported course metadata question.",
                "route_entities": {},
                "route_missing_entities": [],
                "final_answer": self._out_of_scope_answer(question),
            }

        semantic = None
        if router_service:
            semantic = router_service.route_question(
                question,
                history=routing_history,
                student_level=state.get("student_level"),
                student_major=state.get("student_major"),
            )

        if semantic and self._is_valid_route(semantic.route) and semantic.confidence >= 0.75:
            semantic = self._validate_semantic_decision(semantic, signals)
            if semantic.intent == "student_record_query":
                logger.info("Question returned unsupported (student record query)")
                return self._unsupported_student_record_route(question, semantic)
            logger.info(f"Question semantically routed to: {semantic.route} ({semantic.confidence:.2f})")
            return {
                "route": semantic.route,
                "route_sub_intent": semantic.sub_intent,
                "rewritten_question": semantic.rewritten_question or question,
                "route_confidence": semantic.confidence,
                "route_reasoning": semantic.reasoning,
                "route_entities": semantic.entities,
                "route_missing_entities": semantic.missing_entities,
            }

        if self._is_student_record_query(normalized):
            logger.info("Question returned unsupported (student record heuristic)")
            return self._unsupported_student_record_route(question, semantic)

        if self._is_category_hours_query(normalized):
            logger.info("Question force-routed to kg (category required hours fallback)")
            return {
                "route": "kg",
                "route_sub_intent": "category_required_hours",
                "rewritten_question": question,
                "route_confidence": semantic.confidence if semantic else 1.0,
                "route_reasoning": semantic.reasoning if semantic else "Explicit category required-hours question.",
                "route_entities": semantic.entities if semantic else {},
                "route_missing_entities": semantic.missing_entities if semantic else [],
            }
        if self._is_semester_withdrawal_question(normalized):
            logger.info("Question force-routed to rag (semester withdrawal policy fallback)")
            return {
                "route": "rag",
                "route_sub_intent": "regulation",
                "rewritten_question": question,
                "route_confidence": semantic.confidence if semantic else 1.0,
                "route_reasoning": semantic.reasoning if semantic else "Explicit semester withdrawal / freeze policy question.",
                "route_entities": semantic.entities if semantic else {},
                "route_missing_entities": semantic.missing_entities if semantic else [],
            }
        if (
            self._is_high_confidence_regulation_query(normalized)
            and not (
                signals.get("relationship_direction") != "unknown"
                and self._has_course_entity_or_signal(question, {}, signals)
            )
        ):
            logger.info("Question force-routed to rag (high-confidence regulation topic fallback)")
            return {
                "route": "rag",
                "route_sub_intent": "regulation",
                "rewritten_question": question,
                "route_confidence": semantic.confidence if semantic else 1.0,
                "route_reasoning": semantic.reasoning if semantic else "Explicit regulation topic.",
                "route_entities": semantic.entities if semantic else {},
                "route_missing_entities": semantic.missing_entities if semantic else [],
            }
        if KGService._looks_like_course_relationship_followup(question) and not (signals.get("course_code") or signals.get("course")):
            logger.info("Question force-routed to kg (course relationship follow-up fallback)")
            return {
                "route": "kg",
                "route_sub_intent": KGService._classify_prerequisite_direction(question),
                "rewritten_question": question,
                "route_confidence": semantic.confidence if semantic else 1.0,
                "route_reasoning": semantic.reasoning if semantic else "Short course relationship follow-up.",
                "route_entities": semantic.entities if semantic else {},
                "route_missing_entities": semantic.missing_entities if semantic else [],
            }

        prereq_direction = KGService._classify_prerequisite_direction(question)
        if prereq_direction != "unknown" and self._has_course_entity_or_signal(question, semantic.entities if semantic else {}, signals):
            logger.info("Question routed to kg (explicit course prerequisite relationship)")
            return {
                "route": "kg",
                "route_sub_intent": prereq_direction,
                "rewritten_question": question,
                "route_confidence": semantic.confidence if semantic else 0.0,
                "route_reasoning": semantic.reasoning if semantic else "Explicit course prerequisite relationship.",
                "route_entities": semantic.entities if semantic else {},
                "route_missing_entities": semantic.missing_entities if semantic else [],
            }

        heuristic_route = self._heuristic_route(question, routing_history)
        logger.info(f"Question heuristically routed to: {heuristic_route}")
        return {
            "route": heuristic_route,
            "route_sub_intent": semantic.sub_intent if semantic else "",
            "rewritten_question": question,
            "route_confidence": semantic.confidence if semantic else 0.0,
            "route_reasoning": semantic.reasoning if semantic else "",
            "route_entities": semantic.entities if semantic else {},
            "route_missing_entities": semantic.missing_entities if semantic else [],
        }

    def _deterministic_routing_signals(self, question: str) -> Dict[str, Any]:
        """Extract only high-confidence signals used to validate semantic routing."""
        normalized = self._normalize_text(question)
        signals: Dict[str, Any] = {"normalized": normalized}

        code_match = re.search(r"\b[A-Z]{2,4}\d{3}\b", question or "", re.IGNORECASE)
        if code_match:
            signals["course_code"] = code_match.group(0).upper()

        alias_course = self._exact_course_alias_match(normalized)
        if alias_course:
            signals["course"] = alias_course

        level = self._extract_level_signal(normalized)
        if level:
            signals["level"] = str(level)

        program = self._extract_program_signal(normalized)
        if program:
            signals["program"] = program

        requirement_type = self._extract_requirement_type_signal(normalized)
        if requirement_type:
            signals["requirement_type"] = requirement_type

        relationship = KGService._classify_prerequisite_direction(question)
        if relationship != "unknown":
            signals["relationship_direction"] = relationship

        if self._looks_like_study_plan_signal(normalized):
            signals["looks_like_study_plan"] = True
        if self._looks_like_category_requirement_signal(normalized):
            signals["looks_like_category_requirement"] = True

        return signals

    def _exact_course_alias_match(self, normalized: str) -> Optional[str]:
        """Find an exact code/name/known-alias match without fuzzy matching."""
        expanded = KGService._apply_course_aliases(normalized)
        for name in getattr(self, "course_names", []) or []:
            candidate = self._normalize_text(str(name))
            if len(candidate) > 3 and candidate in expanded:
                return str(name)
        alias_tokens = {
            "machine learning": "Machine Learning",
            "deep learning": "Deep Learning",
            "introduction to ai": "Introduction to Artificial Intelligence",
            "intro ai": "Introduction to Artificial Intelligence",
        }
        for alias, course in alias_tokens.items():
            if alias in expanded:
                return course
        return None

    @staticmethod
    def _extract_level_signal(normalized: str) -> Optional[int]:
        level_patterns = (
            (1, ("level 1", "lvl 1", "first year", "سنه اولي", "سنة اولي", "سنه اولى", "سنة اولى", "اولي", "اولى")),
            (2, ("level 2", "lvl 2", "second year", "سنه تانيه", "سنة تانيه", "تانيه", "تانية")),
            (3, ("level 3", "lvl 3", "third year", "سنه تالته", "سنة تالته", "سنه ثالثه", "سنة ثالثه", "سنة ثالثة", "تالته", "تالتة", "ثالثه", "ثالثة")),
            (4, ("level 4", "lvl 4", "fourth year", "سنه رابعه", "سنة رابعه", "رابعه", "رابعة")),
        )
        for level, terms in level_patterns:
            if any(term in normalized for term in terms):
                return level
        return None

    @staticmethod
    def _extract_program_signal(normalized: str) -> Optional[str]:
        if any(term in normalized for term in ("artificial intelligence", "ai program", "ذكاء اصطناعي", "ذكاء", "ai")):
            return "Artificial Intelligence"
        if any(term in normalized for term in ("cybersecurity", "cyber", "سايبر", "امن سيبراني", "الامن السيبراني")):
            return "Cybersecurity"
        if any(term in normalized for term in ("data science", "علوم بيانات")):
            return "Data Science"
        if any(term in normalized for term in ("software engineering", "برمجيات")):
            return "Software Engineering"
        return None

    @staticmethod
    def _extract_requirement_type_signal(normalized: str) -> Optional[str]:
        compulsory_terms = ("اجباري", "اجباريه", "اجبارية", "compulsory", "mandatory", "required")
        elective_terms = ("اختياري", "اختياريه", "اختيارية", "elective", "optional")
        if any(term in normalized for term in compulsory_terms):
            return "compulsory"
        if any(term in normalized for term in elective_terms):
            return "elective"
        return None

    @staticmethod
    def _looks_like_study_plan_signal(normalized: str) -> bool:
        has_courses = any(term in normalized for term in ("مواد", "المواد", "courses", "subjects", "study plan", "study path", "خطة", "خطه"))
        has_level = AdvisorGraph._extract_level_signal(normalized) is not None
        return has_courses and has_level

    @staticmethod
    def _looks_like_category_requirement_signal(normalized: str) -> bool:
        has_requirement_group = any(
            term in normalized
            for term in (
                "university requirements", "متطلبات الجامعه", "متطلبات الجامعة",
                "basic computer science", "math and basic science", "math & basic science",
                "مواد الجامعة", "المواد الاختياريه في الجامعه", "المواد الاختيارية في الجامعة",
            )
        )
        has_requirement_type = AdvisorGraph._extract_requirement_type_signal(normalized) is not None
        return has_requirement_group or has_requirement_type

    def _validate_semantic_decision(self, decision, signals: Dict[str, Any]):
        """Enrich high-confidence semantic routing with exact deterministic signals."""
        entities = dict(decision.entities or {})

        if decision.route == "mental":
            return decision

        if signals.get("course_code"):
            entities.setdefault("course", signals["course_code"])
        elif signals.get("course"):
            entities.setdefault("course", signals["course"])
        if signals.get("level"):
            entities["level"] = signals["level"]
        if signals.get("program"):
            entities["program"] = signals["program"]
            entities.setdefault("major", signals["program"])
        if signals.get("requirement_type"):
            entities["requirement_type"] = signals["requirement_type"]

        relationship = signals.get("relationship_direction")
        has_course = bool(entities.get("course") or signals.get("course_code") or signals.get("course"))
        if relationship == "prerequisites_for_course" and has_course and decision.route != "mental":
            decision.intent = "course_prerequisite_query"
            decision.route = "kg"
            decision.sub_intent = "prerequisites_for_course"
        elif relationship in {"courses_unlocked_by_course", "courses_blocked_if_not_completed"} and has_course and decision.route != "mental":
            decision.intent = "course_unlock_query"
            decision.route = "kg"
            decision.sub_intent = relationship

        decision.entities = entities
        if not decision.reasoning and getattr(decision, "reasoning_summary", ""):
            decision.reasoning = decision.reasoning_summary
        return decision

    @staticmethod
    def _validate_followup_decision(decision, question: str, signals: Dict[str, Any]):
        """Keep the current follow-up wording in control of course relationship direction."""
        relationship = signals.get("relationship_direction")
        if (
            decision.route != "mental"
            and relationship in {
                "prerequisites_for_course",
                "courses_unlocked_by_course",
                "courses_blocked_if_not_completed",
            }
            and KGService._looks_like_course_relationship_followup(question)
        ):
            entities = dict(decision.entities or {})
            if signals.get("course_code"):
                entities.setdefault("course", signals["course_code"])
            elif signals.get("course"):
                entities.setdefault("course", signals["course"])

            decision.route = "kg"
            decision.sub_intent = relationship
            decision.entities = entities

            rewritten_direction = KGService._classify_prerequisite_direction(
                decision.rewritten_question or ""
            )
            if rewritten_direction != relationship:
                decision.rewritten_question = question

            if not decision.reasoning:
                decision.reasoning = "Course follow-up direction was validated from the current message."
        return decision

    def _has_course_entity_or_signal(self, question: str, entities: Optional[Dict[str, str]], signals: Dict[str, Any]) -> bool:
        if signals.get("course_code") or signals.get("course"):
            return True
        if entities and entities.get("course"):
            return True
        return self._is_course_query(question)

    def _is_category_hours_query(self, question: str) -> bool:
        """Detect explicit category/group required-hour questions for KG."""
        return KGService._looks_like_category_hours_query(question)

    @staticmethod
    def _is_semester_withdrawal_question(question: str) -> bool:
        """Detect full-semester withdrawal/freeze questions for RAG."""
        freeze_terms = (
            "ايقاف القيد", "ايقاف قيد", "إيقاف القيد", "تجميد القيد",
            "اوقف قيدي", "اوقف القيد", "اجمد القيد",
        )
        semester_terms = (
            "الفصل الدراسي", "الترم", "الفصل", "سمستر", "semester",
        )
        withdrawal_terms = (
            "الانسحاب", "انسحاب", "انسحب", "اسحب", "اسيب", "اتسحب",
            "withdraw", "withdrawal",
        )
        return (
            any(term in question for term in freeze_terms)
            or (
                any(term in question for term in withdrawal_terms)
                and any(term in question for term in semester_terms)
            )
        )

    def _heuristic_route(self, question: str, history: List[BaseMessage]) -> str:
        """Fallback routing logic used when semantic routing is unavailable or low-confidence."""
        normalized = self._normalize_text(question)
        history_route = self._route_from_history_if_followup(normalized, history)

        if history_route:
            return history_route
        if KGService._looks_like_course_relationship_followup(question):
            return "kg"
        if self._matches_keywords(normalized, MENTAL_KEYWORDS):
            return "mental"
        if self._is_curriculum_semester_query(normalized):
            return "rag"
        if self._looks_like_regulation_query(normalized):
            return "rag"
        if self._matches_keywords(normalized, MAJOR_KEYWORDS):
            return "mental"
        if self._is_general_study_path_query(normalized):
            return "kg"
        if self._is_kg_category_query(normalized):
            return "kg"
        if self._is_course_query(normalized):
            return "kg"
        if self._is_policy_topic(normalized):
            return "rag"
        if self._matches_keywords(normalized, ELECTIVE_KEYWORDS):
            return "elective"
        if self._matches_keywords(normalized, KG_KEYWORDS):
            return "kg"
        if self._matches_keywords(normalized, RAG_KEYWORDS):
            return "rag"
        return "hybrid"

    @staticmethod
    def _is_valid_route(route: str) -> bool:
        """Validate semantic router route values."""
        return route in {"rag", "kg", "mental", "elective", "hybrid"}

    def _current_only_semantic_route(
        self,
        question: str,
        router_service,
        student_level: Optional[int],
        student_major: Optional[str],
        competing_route: Optional[str] = None,
    ) -> Optional[dict]:
        """Use the semantic router without history to detect standalone context switches."""
        if not router_service:
            return None
        current_only = router_service.route_question(
            question,
            history=[],
            student_level=student_level,
            student_major=student_major,
        )
        if not (
            current_only
            and self._is_valid_route(current_only.route)
            and current_only.route != "hybrid"
            and current_only.confidence >= 0.75
        ):
            return None
        if competing_route and current_only.route == competing_route:
            return None
        if not self._semantic_decision_has_current_entity(current_only):
            return None

        logger.info(f"Question semantically routed to standalone current route: {current_only.route}")
        return {
            "route": current_only.route,
            "route_sub_intent": current_only.sub_intent or "standalone_context_switch",
            "rewritten_question": current_only.rewritten_question or question,
            "route_confidence": current_only.confidence,
            "route_reasoning": current_only.reasoning,
            "route_entities": current_only.entities,
            "route_missing_entities": current_only.missing_entities,
        }

    @staticmethod
    def _semantic_decision_has_current_entity(decision) -> bool:
        """Require the current-only semantic route to resolve a concrete current topic."""
        entities = decision.entities or {}
        if decision.route == "kg":
            return any(entities.get(key) for key in ("course", "category", "program", "level"))
        if decision.route == "rag":
            return bool(entities.get("policy_topic") or decision.sub_intent)
        return bool(entities or decision.sub_intent)

    def _route_from_history_if_followup(self, question: str, history: List[BaseMessage]) -> Optional[str]:
        """Route short follow-ups using the last substantive user question."""
        if not history or not self._looks_like_followup(question):
            return None

        for message in reversed(history):
            if not isinstance(message, HumanMessage):
                continue
            previous = self._normalize_text(str(message.content))
            if previous == question or self._looks_like_followup(previous):
                if self._is_policy_topic(previous):
                    return "rag"
                continue
            if self._matches_keywords(previous, MENTAL_KEYWORDS + MAJOR_KEYWORDS):
                return "mental"
            if self._is_policy_topic(previous) or self._looks_like_regulation_query(previous):
                return "rag"
            if self._is_course_query(previous) or self._matches_keywords(previous, KG_KEYWORDS):
                return "kg"
            if self._matches_keywords(previous, ELECTIVE_KEYWORDS):
                return "elective"
            return None
        return None

    @staticmethod
    def _looks_like_followup(question: str) -> bool:
        """Detect vague continuation messages that need previous context."""
        words = question.split()
        word_tokens = set(words)
        pronoun_words = {
            "ده", "دا", "دي", "هو", "هي", "it", "this", "that",
            "مدته", "مدتو", "مدتها", "مدتة", "مده", "مدة", "details", "تفاصيل",
        }
        pronoun_phrases = (
            "كام اسبوع", "كام أسبوع", "قد ايه", "قد اية", "الصيفي", "الفصل الصيفي",
            "المطلوب كام", "كام", "قد ايه المطلوب", "قد اية المطلوب",
        )
        if len(words) <= 6 and ((word_tokens & pronoun_words) or any(token in question for token in pronoun_phrases)):
            return True
        followup_phrases = (
            "اه", "ايوه", "اه ده", "اه داه", "ده اللي", "دا اللي",
            "قول", "وضح", "عايز اعرف", "محتاج اعرف", "yes", "yeah",
            "that's what", "that is what", "tell me", "explain",
            "what about", "how long", "how many weeks", "and what",
            "and for", "is this", "who teaches", "مين الدكتور", "طيب و",
            "طب", "طب و", "طيب", "والمطلوب", "و المطلوب",
        )
        return len(words) <= 8 and any(phrase in question for phrase in followup_phrases)

    @staticmethod
    def _is_policy_topic(question: str) -> bool:
        """Detect short regulation topics that are meaningful only in policy/RAG context."""
        return any(topic in question for topic in ("الفصل الصيفي", "الصيفي", "فصل صيفي", "الترم الصيفي"))

    @staticmethod
    def _is_high_confidence_regulation_query(question: str) -> bool:
        """Detect specific policy questions that should not be offered to KG."""
        phrases = (
            "regular semester", "summer semester", "credit hours does a student need to graduate",
            "credit hours اللازمة للتخرج", "ساعه معتمده يجب اجتيازها للتخرج",
            "ساعات معتمده يجب اجتيازها للتخرج", "register for courses",
            "withdraw from a course", "withdrawal", "الحذف والاضافه", "الحذف والاضافة",
            "الانسحاب من مقرر", "انسحاب من مقرر",
            "minimum passing grade", "minimum للنجاح", "grade distributed",
            "theoretical course", "minimum required from the final", "attendance percentage",
            "academic warning", "honor graduation", "honor degree", "مرتبه الشرف",
            "مرتبة الشرف", "dismissal conditions", "يتفصل من الكليه", "يتفصل من الكلية",
            "new students in first semester", "رسبت في مقرر واعدته", "اسجل مشروع التخرج",
            "الفصل الصيفي اجباري", "summer semester اجباري", "summer semester mandatory",
        )
        if any(phrase in question for phrase in phrases):
            return True
        if "cgpa" in question and any(term in question for term in ("warning", "انذار", "اعلى من 3", "اقل من 2")):
            return True
        if "final" in question and any(term in question for term in ("excuse", "بعذر", "attendance", "غياب")):
            return True
        return False

    @staticmethod
    def _matches_keywords(question: str, keywords: List[str]) -> bool:
        """Match keywords conservatively to avoid accidental substring hits."""
        for keyword in keywords:
            keyword = AdvisorGraph._normalize_text(keyword)
            if " " in keyword or "-" in keyword:
                if keyword in question:
                    return True
                continue
            if re.search(r"(?<!\w)" + re.escape(keyword) + r"(?!\w)", question):
                return True
        return False

    def _looks_like_regulation_query(self, question: str) -> bool:
        """Detect regulation and policy questions beyond the static keyword list."""
        if self._matches_keywords(question, RAG_KEYWORDS):
            return True

        extra_phrases = (
            "maximum number of credit hours", "maximum credit load",
            "regular semester", "summer semester", "passing grade",
            "withdraw from a course", "add/drop",
            "repeat a course", "improve my gpa", "graduating students",
            "الحد الاقصى", "الحد الأقصى", "الترم العادي", "الفصل العادي",
            "المعدل التراكمي", "اكثر من 25", "اكتر من 25", "المحاضرات",
            "اسحب ماده", "اسحب مادة", "الحذف والاضافه", "الحذف والاضافة",
            "اعيد ماده", "اعيد مادة", "احسن المجموع", "احسن المعدل",
            "خريجين الترم", "جبت مقبول", "اعلى من 3.5",
            "ماشيه باي نظام", "ماشيه باي نظام", "بنظام الساعات",
            "مدة الفصل الدراسي النظامي", "مده الفصل الدراسي النظامي",
            "التسجيل في المقررات", "شرط التسجيل", "راي المرشد", "المرشد الاكاديمي",
            "ينسحب من مقرر", "انسحب في الميعاد", "عذر قهري",
            "الدرجه النهائيه", "اقل درجه", "الامتحان النهائي التحريري",
            "نسبه الحضور", "الامتحان النهائي", "تجاوزت 25", "تقدير غير مكتمل",
            "الفصل من الكليه", "الفصل من الكلية", "حالات الفصل", "انذار اكاديمي",
            "انذار اكادمى", "تظلم", "التظلمات", "نتيجه ماده", "نتيجة ماده",
            "نتيجه الامتحان", "نتيجة الامتحان", "التقدير العام", "نظام التقديرات",
            "جدول التقديرات", "a+", "b+", "a-", "b-", "c+", "c-", "d+", "d-", "abs", "con",
            "فرصه اخيره", "فرصة اخيرة", "فرصه اخيرة", "فرصه اضافيه", "فرصة اضافية",
            "80 من الساعات", "80% من الساعات", "cgpa 3.2", "شروط التخرج",
            "مقررات النجاح والرسوب", "مقررات النجاح و الرسوب", "النجاح والرسوب", "النجاح و الرسوب", "نظام تقديرات الكلية",
            "نظم تقديرات الكلية", "نظام تقديرات المواد", "المعدل التراكمي بيتحسب",
            "المعدل التراقمي", "بيتحسب ازاي",
            "شروط التحويل", "التحويل لكليه", "التحويل لكلية", "احول لكليه", "احول لكلية",
            "شروط القبول", "القبول بالكليه", "القبول بالكلية", "ادخل ذكاء اصطناعي",
            "قسم شؤون الخريجين", "قسم شئون الخريجين", "خدمات الخريجين", "شهادات التخرج",
            "مواصفات خريج", "مواصفات الخريج", "خريج كليه الذكاء", "خريج كلية الذكاء",
        )
        if any(phrase in question for phrase in extra_phrases):
            return True
        if "25" in question and self._matches_keywords(question, ["lecture", "lectures", "محاضرات"]):
            return True
        if "cgpa" in question and any(term in question for term in ("التقدير العام", "ممتاز", "جيد جدا", "جيد", "مقبول", "ضعيف")):
            return True
        if any(symbol in question for symbol in ("a+", "b+", "a-", "b-", "c+", "c-", "d+", "d-", "abs", "con")):
            return True
        if any(term in question for term in ("شروط التخرج", "مقررات النجاح والرسوب", "النجاح والرسوب", "نظام تقديرات الكلية", "نظام تقديرات المواد", "المعدل التراقمي", "المعدل التراكمي")):
            return True
        return False

    @staticmethod
    def _is_kg_category_query(question: str) -> bool:
        """Detect category questions that belong to the KG, not the term elective service."""
        category_phrases = (
            "math electives", "ai elective courses", "ai electives",
            "cybersecurity elective courses", "cyber electives",
            "university requirements", "basic computer science",
            "math & basic science", "متطلبات الجامعه", "متطلبات الجامعة",
            "مواد العلوم الاساسيه", "مواد العلوم الأساسية", "مواد ai الاختياريه",
            "مواد cyber الاختياريه", "مواد السايبر الاختياريه", "مواد الرياضه الاختياريه",
        )
        return any(phrase in question for phrase in category_phrases)

    @staticmethod
    def _is_curriculum_semester_query(question: str) -> bool:
        """Detect study-plan table queries that need semester/program context from RAG."""
        has_course_list_intent = any(term in question for term in (
            "مواد", "المواد", "courses", "subjects", "course list",
        ))
        has_semester = any(term in question for term in (
            "ترم", "الترم", "سمستر", "semester", "term",
        ))
        has_level = any(term in question for term in (
            "سنه", "سنة", "تالته", "تالتة", "ثالثه", "ثالثة",
            "رابعه", "رابعة", "تانيه", "تانية", "اولى", "اولي",
            "level 1", "level 2", "level 3", "level 4",
        ))
        has_program = any(term in question for term in (
            "ذكاء", "اصطناعي", "artificial intelligence", "ai program",
            "data science", "علوم بيانات", "cyber", "سايبر",
            "software", "برمجيات",
        ))
        return has_course_list_intent and has_semester and (has_level or has_program)

    @staticmethod
    def _is_general_study_path_query(question: str) -> bool:
        """Detect broad level/program study-plan requests that should come from KG."""
        has_path_intent = any(term in question for term in (
            "الخطه", "الخطة", "خطه", "materials", "courses", "subjects",
            "study path", "study plan", "plan", "roadmap", "المواد",
        ))
        has_level = any(term in question for term in (
            "الفرقه الاولي", "الفرقة الاولى", "الفرقة الأولى", "الفرقه الأولى",
            "الفرقه التانيه", "الفرقة الثانية", "الفرقه الثالثه", "الفرقة الثالثة",
            "الفرقه الرابعه", "الفرقة الرابعة", "first year", "second year",
            "third year", "fourth year", "level 1", "level 2", "level 3", "level 4",
            "اولي", "اولى", "تانيه", "تانية", "ثالثه", "ثالثة", "رابعه", "رابعة",
        ))
        has_semester = any(term in question for term in ("ترم", "الترم", "سمستر", "semester", "term"))
        return has_path_intent and has_level and not has_semester

    def _is_course_query(self, question: str) -> bool:
        """Check if query mentions a specific course name."""
        q_clean = self._normalize_text(question)
        stop_words = {
            "course", "courses", "subject", "subjects", "program", "level",
            "graduation", "project", "requirement", "requirements", "credit",
            "credits", "hour", "hours", "take", "need", "what", "which",
            "register", "failed", "core", "elective", "term", "semester",
            "opens", "open", "material", "ماده", "مواد", "كورس", "كورسات",
            "تخرج", "مشروع", "مقرر", "مقررات", "تسجيل", "انسحاب", "انسحب",
            "درجه", "الدرجه", "نجاح", "امتحان", "الامتحان", "نهائي",
            "حضور", "غياب", "مرشد", "اكاديمي", "اكاديمي",
        }
        # Handle known phrasing expansions if needed, but simple contains check is usually enough
        
        # Direct substring match
        for c_name in self.course_names:
            cn_lower = self._normalize_text(c_name)
            if len(cn_lower) > 3 and (cn_lower in q_clean or q_clean in cn_lower):
                return True
        
        # Word overlap
        q_words = set(w for w in q_clean.split() if len(w) >= 3 and w not in stop_words)
        for c_name in self.course_names:
            c_words = set(
                w for w in self._normalize_text(c_name).split()
                if len(w) >= 3 and w not in stop_words
            )
            # Intersection check
            overlap = c_words & q_words
            if overlap and (len(c_words) == 1 or len(overlap) >= 2):
                return True
            fuzzy_matches = 0
            for c_word in c_words:
                if any(difflib.SequenceMatcher(None, q_word, c_word).ratio() >= 0.82 for q_word in q_words):
                    fuzzy_matches += 1
            if len(c_words) == 1 and fuzzy_matches >= 1:
                return True
            if len(c_words) > 1 and fuzzy_matches >= 2:
                return True
        return False

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize Arabic and common Arabizi forms for routing."""
        text = text.lower().strip()
        replacements = {
            "أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه",
            "zakaa": "ذكاء", "zeka": "ذكاء", "zaka": "ذكاء",
            "saiber": "سايبر", "cyber security": "cybersecurity",
            "mawade": "مواد", "mawad": "مواد", "madda": "ماده", "mada": "ماده",
            "kors": "course", "prereq": "prerequisite", "pre req": "prerequisite",
            "prequesits": "prerequisite", "prequesites": "prerequisite",
            "prequisite": "prerequisite", "prerequisits": "prerequisite",
            "prerequsite": "prerequisite", "pre-req": "prerequisite",
            "btfta7": "تفتح", "betfta7": "تفتح", "bt2fel": "تقفل", "bet2fel": "تقفل",
            "khota": "خطة", "kam sa3a": "كام ساعة", "kam saa": "كام ساعة",
            "ta5arog": "تخرج", "takharog": "تخرج", "lawaye7": "لائحة",
            "lawe7a": "لائحة", "a5tar": "اختار", "akhtar": "اختار",
            "التراقمي": "التراكمي",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        text = re.sub(r"(.)\1{2,}", r"\1\1", text)
        text = re.sub(r"[^\w\s\u0600-\u06FF-]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def _route_decision(self, state: AdvisorState) -> str:
        """Return the route string for conditional edges."""
        return state.get("route", "hybrid") or "hybrid"

    def _rag_node(self, state: AdvisorState) -> dict:
        """Query regulations via RAG."""
        question = state.get("rewritten_question") or state["question"]
        service_question = self._question_with_language_source(question, state["question"])
        answer = self.rag_service.query(service_question)
        return {"rag_answer": answer}

    def _kg_node(self, state: AdvisorState) -> dict:
        """Query Knowledge Graph for course information."""
        question = state["question"]
        rewritten_question = state.get("rewritten_question") or question
        student_level = state.get("student_level")
        student_major = state.get("student_major")
        service_question = self._question_with_language_source(rewritten_question, question)

        if self._is_unsupported_course_metadata_query(service_question):
            return {"kg_answer": self._out_of_scope_answer(question)}

        # Check if question is about study path/schedule
        is_path_query = any(kw in service_question.lower() for kw in PATH_KEYWORDS)
        
        # If specific course mentioned, prioritize specific Q&A over generic list
        has_specific_course = self._is_course_query(service_question)

        if student_level and student_major and is_path_query and not has_specific_course:
            answer = self.kg_service.get_study_path(student_level, student_major)
        else:
            answer = self.kg_service.query(service_question, history=None)

        should_try_rag_fallback = self._kg_unavailable(answer) or (
            is_path_query and not has_specific_course and self._should_use_scope_fallback(answer)
        )
        if should_try_rag_fallback:
            rag_fallback = self.rag_service.query(service_question)
            if not self._rag_not_found(rag_fallback):
                return {"kg_answer": rag_fallback}
        if self._should_use_scope_fallback(answer):
            return {"kg_answer": self._out_of_scope_answer(question)}

        return {"kg_answer": answer}

    @staticmethod
    def _question_with_language_source(resolved_question: str, original_question: str) -> str:
        """Keep semantic rewrites useful while preserving the original response language."""
        if should_respond_arabic(original_question) and not should_respond_arabic(resolved_question):
            return (
                f"{resolved_question}\n\n"
                f"Original student question: {original_question}\n"
                "Response language requirement: answer in Arabic only."
            )
        return resolved_question

    def _contextualize_followup(self, question: str, history: List[BaseMessage]) -> str:
        """Attach the previous user question when the current message is vague."""
        normalized = self._normalize_text(question)
        if not self._looks_like_followup(normalized):
            return question

        for message in reversed(history):
            if isinstance(message, HumanMessage):
                previous = str(message.content)
                if self._normalize_text(previous) != normalized:
                    alternate_topic = self._extract_followup_topic(question)
                    if alternate_topic and self._asks_duration(previous):
                        return f"ما مدة {alternate_topic} كام أسبوع؟"
                    if self._asks_duration(normalized):
                        topic = self._extract_followup_topic(previous)
                        if topic:
                            return f"ما مدة {topic} كام أسبوع؟"
                        current_topic = self._extract_followup_topic(question)
                        if current_topic:
                            return f"ما مدة {current_topic} كام أسبوع؟"
                    return f"Previous question: {previous}\nCurrent follow-up: {question}"
        return question

    @staticmethod
    def _asks_duration(question: str) -> bool:
        """Detect follow-ups asking about duration."""
        return any(term in question for term in ("مدته", "مدتو", "مدتها", "مده", "مدة", "كام اسبوع", "كام أسبوع", "how long"))

    @staticmethod
    def _extract_followup_topic(previous_question: str) -> Optional[str]:
        """Extract a simple policy topic from the previous message."""
        normalized = AdvisorGraph._normalize_text(previous_question)
        if "الفصل الصيفي" in normalized or "الصيفي" in normalized:
            return "الفصل الصيفي"
        if "الفصل الدراسي" in normalized:
            return "الفصل الدراسي"
        if "امتحان" in normalized or "فاينال" in normalized:
            return "الامتحان"
        return None

    def _mental_node(self, state: AdvisorState) -> dict:
        """Generate mental support or major recommendation response."""
        question = state.get("rewritten_question") or state["question"]
        student_level = state.get("student_level")
        
        if self.mental_service.is_major_query(question):
            answer = self.mental_service.get_major_recommendation(question)
        else:
            answer = self.mental_service.get_response(question, student_level=student_level)
            
        return {"mental_answer": answer}

    def _elective_node(self, state: AdvisorState) -> dict:
        """Handle elective-related queries."""
        question = state.get("rewritten_question") or state["question"]
        original_question = state["question"]
        if (
            self._is_category_hours_query(self._normalize_text(question))
            or self._is_category_hours_query(self._normalize_text(original_question))
        ):
            return {"elective_answer": self.kg_service.query(original_question)}

        answer = self.elective_service.query(question) 
        # Note: Original code had complex specific elective logic. 
        # If ElectiveService.query is robust, we can delegate. 
        # But to keep EXACT behavior including KG enrichment, I should preserve it or move it to service.
        # Given "Do NOT split into microservices", I'll keep the orchestration here but simplified?
        # Actually, original code logic was heavy here. I will try to support it by calling service methods.
        # But ElectiveService.query(question) in original code handled list. 
        # The specific logic was inside the node. I'll preserve the logic but cleaned up.
        
        # Re-adding specific elective logic to maintain behavior
        electives = self.elective_service.get_electives()
        mentioned = None
        
        q_lower = question.lower()
        for e in electives:
            e_name = e if isinstance(e, str) else e.get("name", "")
            if e_name.lower() in q_lower:
                mentioned = e_name
                break
        
        if mentioned:
            kg_info = self.kg_service.query(f"What are the prerequisites and credit hours for {mentioned}?")
            if self.llm:
                prompt = (
                    f"Student asks about elective: {mentioned}\n"
                    f"KG Info: {kg_info}\n"
                    "Provide a helpful answer about this elective's academic details."
                )
                resp = self.llm.invoke(prompt)
                answer = resp.content
            else:
                answer = f"{mentioned}\n\n{kg_info}"
        else:
             answer = self.elective_service.query(question)

        return {"elective_answer": answer}

    def _hybrid_node(self, state: AdvisorState) -> dict:
        """Combine answers into a final response."""
        if state.get("final_answer"):
            return {"final_answer": state["final_answer"]}

        answers = {}
        if state.get("rag_answer"): answers["Regulations"] = state["rag_answer"]
        if state.get("kg_answer"): answers["Course Information"] = state["kg_answer"]
        if state.get("mental_answer"): answers["Support"] = state["mental_answer"]
        if state.get("elective_answer"): answers["Electives"] = state["elective_answer"]

        if len(answers) == 1:
            return {"final_answer": list(answers.values())[0]}

        if not answers:
            return {"final_answer": self._out_of_scope_answer(state["question"])}

        # Synthesize multiple sources
        context = "\n\n".join(f"[{k}]:\n{v}" for k, v in answers.items())
        prompt = (
            f"Synthesize a unified answer for the student.\n"
            f"{strict_language_instruction(state['question'])}\n"
            f"Formatting rules: use plain paragraphs and bullet points with '-' only. "
            f"Use plain text labels like 'Required credits:' without Markdown bold. "
            f"Do not use Markdown heading markers like #, ##, ###, numbered section headings, tables, emojis, or decorative symbols.\n"
            f"Question: {state['question']}\n\n"
            f"Information:\n{context}"
        )
        if not self.llm:
            return {"final_answer": context}
        response = self.llm.invoke(prompt)
        return {"final_answer": response.content}

    def _general_chat(self, question: str, level: Optional[int], major: Optional[str]) -> str:
        """Fallback LLM chat."""
        if not self.llm:
            return (
                "OpenAI is not configured, so I can only answer from local services right now. "
                "Set OPENAI_API_KEY in your .env file to enable full advisor responses."
            )

        prompt = (
            "You are a friendly academic advisor. Answer the student's question helpfully. "
            f"{strict_language_instruction(question)} "
            "Be clear when a question needs official regulations or course data. "
            "Use plain paragraphs and bullet points with '-' only. "
            "Use plain text labels like 'Required credits:' without Markdown bold. "
            "Do not use Markdown heading markers like #, ##, ###, numbered section headings, tables, emojis, or decorative symbols.\n"
            f"Level: {level}, Major: {major}\n"
            f"Question: {question}"
        )
        return self.llm.invoke(prompt).content

    @staticmethod
    def _contains_arabic(text: str) -> bool:
        """Return True when the input contains Arabic-script characters."""
        return contains_arabic(text)

    def _out_of_scope_answer(self, question: str) -> str:
        """Return a consistent fallback when the question is outside supported KG/RAG scope."""
        return OUT_OF_SCOPE_AR if should_respond_arabic(question) else OUT_OF_SCOPE_EN

    def _unsupported_student_record_route(self, question: str, decision=None) -> dict:
        """Return a safe response for personal record questions without guessing."""
        return {
            "route": "hybrid",
            "route_sub_intent": "unsupported_student_record",
            "rewritten_question": getattr(decision, "rewritten_question", "") or question,
            "route_confidence": getattr(decision, "confidence", 1.0) if decision else 1.0,
            "route_reasoning": getattr(decision, "reasoning", "") or "Student-record data is not available.",
            "route_entities": getattr(decision, "entities", {}) or {},
            "route_missing_entities": getattr(decision, "missing_entities", []) or [],
            "final_answer": self._unsupported_student_record_answer(question),
        }

    @staticmethod
    def _unsupported_student_record_answer(question: str) -> str:
        if should_respond_arabic(question):
            return (
                "مش قادر أوصل لبياناتك الشخصية زي CGPA أو الدرجات أو الساعات المجتازة "
                "أو المواد اللي خلصتها من هنا. أقدر أشرح القواعد العامة من اللائحة، "
                "لكن مش هقدر أخمن بياناتك."
            )
        return (
            "I can’t access student-specific records such as your CGPA, grades, earned hours, "
            "or completed courses from here. I can explain the general regulations, but I won’t "
            "guess your personal data."
        )

    @staticmethod
    def _is_student_record_query(question: str) -> bool:
        """Detect personal transcript/record requests, not general regulation questions."""
        personal_terms = (
            "my ", "i ", "me ", "mine", "بتاعي", "بتاعتي", "درجاتي", "معدلي",
            "ساعاتي", "خلصتها", "اللي خلصتها", "اللي عديتها", "موادي",
        )
        record_terms = (
            "my cgpa", "cgpa بتاعي", "cgpa بتاعتي", "grades", "درجاتي",
            "الدرجات بتاعتي", "الدرجات بتاعي",
            "earned hours", "completed hours", "completed courses", "courses completed",
            "الساعات اللي خلصتها", "الساعات المجتازه", "الساعات المجتازة",
            "المواد اللي خلصتها", "المواد اللي عديتها", "transcript",
        )
        rule_terms = (
            "calculated", "calculate", "بيتحسب", "حساب", "warning", "انذار",
            "academic warning", "allowed", "يسجل", "اسجل", "credit load",
        )
        has_record = any(term in question for term in record_terms)
        if not has_record:
            return False
        if any(term in question for term in rule_terms):
            return False
        return any(term in question for term in personal_terms) or has_record

    @staticmethod
    def _is_unsupported_course_metadata_query(question: str) -> bool:
        """Detect course metadata questions the current backend does not support."""
        normalized = question.lower()
        return any(
            phrase in normalized
            for phrase in (
                "who teaches", "who teach", "teacher", "teaches it", "instructor",
                "lecturer", "doctor", "professor", "section", "lab section",
                "مين الدكتور", "مين الدكتوره", "مين بيدرس", "مين المدرس",
                "مين المعيد", "مين بيشرح", "الدكتور بتاعها", "السكشن",
            )
        )

    @staticmethod
    def _should_use_scope_fallback(answer: Optional[str]) -> bool:
        """Convert internal not-found replies into the user-facing scope fallback."""
        if not answer:
            return True
        normalized = answer.lower()
        return any(
            phrase in normalized
            for phrase in (
                "could not find a course matching",
                "no courses found matching your query",
                "could not find a category matching",
                "no courses found in category",
            )
        )

    @staticmethod
    def _kg_unavailable(answer: Optional[str]) -> bool:
        """Detect transient KG availability failures that can be retried through RAG."""
        if not answer:
            return False
        normalized = answer.lower()
        return any(
            phrase in normalized
            for phrase in (
                "knowledge graph is currently unavailable",
                "knowledge graph is unavailable",
                "error retrieving study path",
            )
        )

    @staticmethod
    def _rag_not_found(answer: Optional[str]) -> bool:
        """Recognize explicit RAG misses so we can keep the final fallback consistent."""
        if not answer:
            return True
        normalized = answer.lower()
        return any(
            phrase in normalized
            for phrase in (
                "i couldn't find this specific regulation in the document",
                "مش لاقي المعلومة دي في اللائحة",
                "error querying regulations",
                "openai_vector_store_id is not configured",
                "openai_api_key is not configured",
            )
        )

    @staticmethod
    def _clean_response_format(answer: str) -> str:
        """Restrict final chatbot output to plain text and bullets."""
        if not answer:
            return answer

        replacements = {
            "•": "-",
            "➤": "-",
            "–": "-",
            "—": "-",
            "🌟": "",
            "💪": "",
            "📚": "",
            "⚠": "",
            "💡": "",
            "🔗": "",
            "🔓": "",
            "🎓": "",
            "📂": "",
        }

        cleaned_lines = []
        for raw_line in answer.splitlines():
            line = raw_line
            for old, new in replacements.items():
                line = line.replace(old, new)
            line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
            line = re.sub(r"__(.*?)__", r"\1", line)
            line = re.sub(r"^\s{0,3}#{1,6}\s*", "", line)
            line = re.sub(r"^\s*(?:\d+[\.)])\s+", "- ", line)
            line = re.sub(r"^\s*[-]\s*", "- ", line)
            line = re.sub(r"\s{2,}", " ", line).strip()
            cleaned_lines.append(line)

        cleaned = "\n".join(cleaned_lines)
        return re.sub(r"\n{3,}", "\n\n", cleaned).strip()

    # ── Public Interface ────────────────────────────────────────────

    def run(self, question: str, history: Optional[List[BaseMessage]] = None, student_level: Optional[int] = None, student_major: Optional[str] = None) -> str:
        """
        Run the advisor graph.
        """
        initial_state = {
            "question": question,
            "student_level": student_level,
            "student_major": student_major,
            "history": history or [],
            "route": None,
            "route_sub_intent": None,
            "rewritten_question": question,
            "route_confidence": None,
            "route_reasoning": None,
            "route_entities": None,
            "rag_answer": None,
            "kg_answer": None,
            "mental_answer": None,
            "elective_answer": None,
            "final_answer": None,
        }

        try:
            result = self.graph.invoke(initial_state)
            answer = result.get("final_answer", "I'm sorry, I couldn't process your question.")
            return self._clean_response_format(answer)
        except Exception as e:
            logger.error(f"Graph execution error: {e}")
            return "An error occurred while processing your request."

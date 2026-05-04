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
from typing import TypedDict, Optional, List, Dict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.graph import StateGraph, END

from advisor_ai.rag_service import RAGService
from advisor_ai.kg_service import KGService
from advisor_ai.mental_service import MentalSupportService
from advisor_ai.elective_service import ElectiveService
from advisor_ai.router_service import RouterService
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
        history = state.get("history", [])
        normalized = self._normalize_text(question)

        if self._is_category_hours_query(normalized):
            logger.info("Question force-routed to kg (category required hours)")
            return {
                "route": "kg",
                "route_sub_intent": "category_required_hours",
                "rewritten_question": question,
                "route_confidence": 1.0,
                "route_reasoning": "Explicit category required-hours question.",
                "route_entities": {},
            }
        if self._is_semester_withdrawal_question(normalized):
            logger.info("Question force-routed to rag (semester withdrawal policy)")
            return {
                "route": "rag",
                "route_sub_intent": "regulation",
                "rewritten_question": question,
                "route_confidence": 1.0,
                "route_reasoning": "Explicit semester withdrawal / freeze policy question.",
                "route_entities": {},
            }

        history_route = self._route_from_history_if_followup(normalized, history)
        if history_route:
            logger.info(f"Question force-routed to {history_route} (contextual follow-up)")
            return {
                "route": history_route,
                "route_sub_intent": "contextual_followup",
                "rewritten_question": question,
                "route_confidence": 1.0,
                "route_reasoning": "Short follow-up reused the previous conversation topic.",
                "route_entities": {},
            }

        semantic = None
        router_service = getattr(self, "router_service", None)
        if router_service:
            semantic = router_service.route_question(
                question,
                history=history,
                student_level=state.get("student_level"),
                student_major=state.get("student_major"),
            )

        if semantic and self._is_valid_route(semantic.route) and semantic.confidence >= 0.75:
            logger.info(f"Question semantically routed to: {semantic.route} ({semantic.confidence:.2f})")
            return {
                "route": semantic.route,
                "route_sub_intent": semantic.sub_intent,
                "rewritten_question": semantic.rewritten_question or question,
                "route_confidence": semantic.confidence,
                "route_reasoning": semantic.reasoning,
                "route_entities": semantic.entities,
            }

        heuristic_route = self._heuristic_route(question, history)
        logger.info(f"Question heuristically routed to: {heuristic_route}")
        return {
            "route": heuristic_route,
            "route_sub_intent": semantic.sub_intent if semantic else "",
            "rewritten_question": question,
            "route_confidence": semantic.confidence if semantic else 0.0,
            "route_reasoning": semantic.reasoning if semantic else "",
            "route_entities": semantic.entities if semantic else {},
        }

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
        base_question = state.get("rewritten_question") or state["question"]
        question = self._contextualize_followup(base_question, state.get("history", []))
        answer = self.rag_service.query(question)
        return {"rag_answer": answer}

    def _kg_node(self, state: AdvisorState) -> dict:
        """Query Knowledge Graph for course information."""
        question = state["question"]
        rewritten_question = state.get("rewritten_question") or question
        student_level = state.get("student_level")
        student_major = state.get("student_major")
        history = state.get("history", [])
        contextual_question = self._contextualize_followup(rewritten_question, history)

        if self._is_unsupported_course_metadata_query(contextual_question):
            return {"kg_answer": self._out_of_scope_answer(question)}

        # Check if question is about study path/schedule
        is_path_query = any(kw in contextual_question.lower() for kw in PATH_KEYWORDS)
        
        # If specific course mentioned, prioritize specific Q&A over generic list
        has_specific_course = self._is_course_query(contextual_question)

        if student_level and student_major and is_path_query and not has_specific_course:
            answer = self.kg_service.get_study_path(student_level, student_major)
        else:
            answer = self.kg_service.query(contextual_question, history=history)

        should_try_rag_fallback = self._kg_unavailable(answer) or (
            is_path_query and not has_specific_course and self._should_use_scope_fallback(answer)
        )
        if should_try_rag_fallback:
            rag_fallback = self.rag_service.query(contextual_question)
            if not self._rag_not_found(rag_fallback):
                return {"kg_answer": rag_fallback}
        if self._should_use_scope_fallback(answer):
            return {"kg_answer": self._out_of_scope_answer(question)}

        # Synthesize conversational response
        if answer and self.llm and "Knowledge Graph is currently unavailable" not in answer:
            prompt_text = KG_SYNTHESIS_PROMPT.format(context=answer, question=contextual_question)
            try:
                response = self.llm.invoke([HumanMessage(content=prompt_text)])
                answer = response.content
            except Exception as e:
                logger.error(f"Synthesis error: {e}")

        return {"kg_answer": answer}

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
            "Match the student's language; if they use Arabizi, answer in friendly Egyptian Arabic. "
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
        return bool(re.search(r"[\u0600-\u06FF]", text))

    def _out_of_scope_answer(self, question: str) -> str:
        """Return a consistent fallback when the question is outside supported KG/RAG scope."""
        return OUT_OF_SCOPE_AR if self._contains_arabic(question) else OUT_OF_SCOPE_EN

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

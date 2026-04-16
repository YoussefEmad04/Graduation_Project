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
from typing import TypedDict, Optional, List, Dict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.graph import StateGraph, END

from advisor_ai.rag_service import RAGService
from advisor_ai.kg_service import KGService
from advisor_ai.mental_service import MentalSupportService
from advisor_ai.elective_service import ElectiveService
from advisor_ai.constants import (
    RAG_KEYWORDS, KG_KEYWORDS, ELECTIVE_KEYWORDS, MENTAL_KEYWORDS, 
    MAJOR_KEYWORDS, PATH_KEYWORDS, KG_SYNTHESIS_PROMPT
)

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ── State Definition ────────────────────────────────────────────────

class AdvisorState(TypedDict):
    """State that flows through the graph."""
    question: str
    student_level: Optional[int]
    student_major: Optional[str]
    history: List[BaseMessage]
    route: Optional[str]          # which node to route to
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
        question = self._normalize_text(state["question"])
        history_route = self._route_from_history_if_followup(question, state.get("history", []))
        
        route = "hybrid" # default

        if history_route:
            route = history_route

        # 1. Mental support (High priority)
        elif any(kw in question for kw in MENTAL_KEYWORDS):
            route = "mental"
        
        # 2. Specific Course Mention (Promoted)
        else:
            if self._is_curriculum_semester_query(question):
                route = "rag"
            elif self._is_course_query(question):
                route = "kg"
            elif self._is_policy_topic(question):
                route = "rag"
            elif any(kw in question for kw in MAJOR_KEYWORDS):
                route = "mental"
            elif any(kw in question for kw in ELECTIVE_KEYWORDS):
                route = "elective"
            elif any(kw in question for kw in KG_KEYWORDS):
                route = "kg"
            elif any(kw in question for kw in RAG_KEYWORDS):
                route = "rag"
            else:
                route = "hybrid"

        logger.info(f"Question routed to: {route}")
        return {"route": route}

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
            if self._is_course_query(previous) or any(kw in previous for kw in KG_KEYWORDS):
                return "kg"
            if self._is_policy_topic(previous) or any(kw in previous for kw in RAG_KEYWORDS):
                return "rag"
            if any(kw in previous for kw in ELECTIVE_KEYWORDS):
                return "elective"
            if any(kw in previous for kw in MENTAL_KEYWORDS + MAJOR_KEYWORDS):
                return "mental"
            return None
        return None

    @staticmethod
    def _looks_like_followup(question: str) -> bool:
        """Detect vague continuation messages that need previous context."""
        words = question.split()
        pronoun_tokens = (
            "ده", "دا", "دي", "هو", "هي", "it", "this", "that",
            "مدته", "مدتو", "مدتها", "مدتة", "مده", "مدة",
            "كام اسبوع", "كام أسبوع", "قد ايه", "قد اية",
            "الصيفي", "الفصل الصيفي",
            "details", "تفاصيل",
        )
        if len(words) <= 6 and any(token in question for token in pronoun_tokens):
            return True
        followup_phrases = (
            "اه", "ايوه", "اه ده", "اه داه", "ده اللي", "دا اللي",
            "قول", "وضح", "عايز اعرف", "محتاج اعرف", "yes", "yeah",
            "that's what", "that is what", "tell me", "explain",
            "what about", "how long", "how many weeks", "طيب و",
        )
        return len(words) <= 8 and any(phrase in question for phrase in followup_phrases)

    @staticmethod
    def _is_policy_topic(question: str) -> bool:
        """Detect short regulation topics that are meaningful only in policy/RAG context."""
        return any(topic in question for topic in ("الفصل الصيفي", "الصيفي", "فصل صيفي", "الترم الصيفي"))

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

    def _is_course_query(self, question: str) -> bool:
        """Check if query mentions a specific course name."""
        q_clean = self._normalize_text(question)
        stop_words = {
            "course", "courses", "subject", "subjects", "program", "level",
            "graduation", "project", "requirement", "requirements", "credit",
            "credits", "hour", "hours", "take", "need", "what", "which",
            "material", "ماده", "مواد", "كورس", "كورسات", "تخرج", "مشروع",
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
            "btfta7": "تفتح", "betfta7": "تفتح", "bt2fel": "تقفل", "bet2fel": "تقفل",
            "khota": "خطة", "kam sa3a": "كام ساعة", "kam saa": "كام ساعة",
            "ta5arog": "تخرج", "takharog": "تخرج", "lawaye7": "لائحة",
            "lawe7a": "لائحة", "a5tar": "اختار", "akhtar": "اختار",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        text = re.sub(r"(.)\1{2,}", r"\1\1", text)
        return re.sub(r"\s+", " ", text)

    def _route_decision(self, state: AdvisorState) -> str:
        """Return the route string for conditional edges."""
        return state.get("route", "hybrid") or "hybrid"

    def _rag_node(self, state: AdvisorState) -> dict:
        """Query regulations via RAG."""
        question = self._contextualize_followup(state["question"], state.get("history", []))
        answer = self.rag_service.query(question)
        return {"rag_answer": answer}

    def _kg_node(self, state: AdvisorState) -> dict:
        """Query Knowledge Graph for course information."""
        question = state["question"]
        student_level = state.get("student_level")
        student_major = state.get("student_major")
        history = state.get("history", [])
        contextual_question = self._contextualize_followup(question, history)

        # Check if question is about study path/schedule
        is_path_query = any(kw in contextual_question.lower() for kw in PATH_KEYWORDS)
        
        # If specific course mentioned, prioritize specific Q&A over generic list
        has_specific_course = self._is_course_query(contextual_question)

        if student_level and student_major and is_path_query and not has_specific_course:
            answer = self.kg_service.get_study_path(student_level, student_major)
        else:
            answer = self.kg_service.query(contextual_question, history=history)

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
        question = state["question"]
        student_level = state.get("student_level")
        
        if self.mental_service.is_major_query(question):
            answer = self.mental_service.get_major_recommendation(question)
        else:
            answer = self.mental_service.get_response(question, student_level=student_level)
            
        return {"mental_answer": answer}

    def _elective_node(self, state: AdvisorState) -> dict:
        """Handle elective-related queries."""
        question = state["question"]
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
            # Fallback to general chat
            return {"final_answer": self._general_chat(state["question"], state.get("student_level"), state.get("student_major"))}

        # Synthesize multiple sources
        context = "\n\n".join(f"[{k}]:\n{v}" for k, v in answers.items())
        prompt = (
            f"Synthesize a unified answer for the student.\n"
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
            "Be clear when a question needs official regulations or course data.\n"
            f"Level: {level}, Major: {major}\n"
            f"Question: {question}"
        )
        return self.llm.invoke(prompt).content

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
            "rag_answer": None,
            "kg_answer": None,
            "mental_answer": None,
            "elective_answer": None,
            "final_answer": None,
        }

        try:
            result = self.graph.invoke(initial_state)
            return result.get("final_answer", "I'm sorry, I couldn't process your question.")
        except Exception as e:
            logger.error(f"Graph execution error: {e}")
            return "An error occurred while processing your request."

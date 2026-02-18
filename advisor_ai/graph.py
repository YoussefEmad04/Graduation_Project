"""
Advisor Graph — LangGraph workflow for the Smart Academic Advisor.
Routes student queries to the appropriate service node, then combines
results in a hybrid node for the final answer.

Flow: router → rag_node / kg_node / mental_node / elective_node → hybrid_node → text output
NO loops. NO multi-agent system.
"""

import os
import logging
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
        self.llm = ChatOpenAI(
            model=os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini"),
            temperature=0.3,
        )

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
        question = state["question"].lower()
        
        route = "hybrid" # default

        # 1. Mental support (High priority)
        if any(kw in question for kw in MENTAL_KEYWORDS):
            route = "mental"
        
        # 2. Specific Course Mention (Promoted)
        else:
            if self._is_course_query(question):
                route = "kg"
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

    def _is_course_query(self, question: str) -> bool:
        """Check if query mentions a specific course name."""
        q_clean = question.lower()
        # Handle known phrasing expansions if needed, but simple contains check is usually enough
        
        # Direct substring match
        for c_name in self.course_names:
            cn_lower = c_name.lower()
            if len(cn_lower) > 3 and (cn_lower in q_clean or q_clean in cn_lower):
                return True
        
        # Word overlap
        q_words = set(w for w in q_clean.split() if len(w) >= 3)
        for c_name in self.course_names:
            c_words = set(w for w in c_name.lower().split() if len(w) >= 3)
            # Intersection check
            if not c_words.isdisjoint(q_words):
                return True
        return False

    def _route_decision(self, state: AdvisorState) -> str:
        """Return the route string for conditional edges."""
        return state.get("route", "hybrid") or "hybrid"

    def _rag_node(self, state: AdvisorState) -> dict:
        """Query regulations via RAG."""
        answer = self.rag_service.query(state["question"])
        return {"rag_answer": answer}

    def _kg_node(self, state: AdvisorState) -> dict:
        """Query Knowledge Graph for course information."""
        question = state["question"]
        student_level = state.get("student_level")
        student_major = state.get("student_major")
        history = state.get("history", [])

        # Check if question is about study path/schedule
        is_path_query = any(kw in question.lower() for kw in PATH_KEYWORDS)
        
        # If specific course mentioned, prioritize specific Q&A over generic list
        has_specific_course = self._is_course_query(question)

        if student_level and student_major and is_path_query and not has_specific_course:
            answer = self.kg_service.get_study_path(student_level, student_major)
        else:
            answer = self.kg_service.query(question, history=history)

        # Synthesize conversational response
        if answer and "Knowledge Graph is currently unavailable" not in answer:
            prompt_text = KG_SYNTHESIS_PROMPT.format(context=answer, question=question)
            try:
                response = self.llm.invoke([HumanMessage(content=prompt_text)])
                answer = response.content
            except Exception as e:
                logger.error(f"Synthesis error: {e}")

        return {"kg_answer": answer}

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
            # We can use a simple prompt here
            prompt = (
                f"Student asks about elective: {mentioned}\n"
                f"KG Info: {kg_info}\n"
                "Provide a helpful answer about this elective's academic details."
            )
            resp = self.llm.invoke(prompt)
            answer = resp.content
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
        response = self.llm.invoke(prompt)
        return {"final_answer": response.content}

    def _general_chat(self, question: str, level: Optional[int], major: Optional[str]) -> str:
        """Fallback LLM chat."""
        prompt = (
            "You are an academic advisor. Answer the student's question helpfuly.\n"
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

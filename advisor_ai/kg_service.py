"""
Knowledge Graph Service — Neo4j integration for course data.
Handles queries about courses, prerequisites, study paths for AI and Cybersecurity programs.
Gracefully handles Neo4j unavailability.
LangSmith tracing enabled via @traceable decorator.
"""

import os
import re
import logging
import difflib
from typing import Optional, Dict, List, Any

from dotenv import load_dotenv
from langsmith import traceable
from neo4j import GraphDatabase

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from pydantic import BaseModel, Field

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ── Constants ───────────────────────────────────────────────────────

ABBREVIATIONS = {
    "ai": "artificial intelligence",
    "cs": "computer science",
    "is": "information systems",
    "it": "information technology",
    "ds": "data science",
    "ml": "machine learning",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "cv": "computer vision",
}

ARABIC_ORDINALS = {
    1: ["اولى", "أولى", "الاولى", "الأولى", "اولي"],
    2: ["تانية", "تانيه", "ثانية", "التانية", "الثانية"],
    3: ["تالتة", "تالته", "ثالثة", "التالتة", "الثالثة"],
    4: ["رابعة", "رابعه", "الرابعة", "الرابعه"],
}

PRONOUNS_TO_RESOLVE = {"ها", "هيه", "دي", "it", "this", "unknown", "none"}


# ── Models ──────────────────────────────────────────────────────────

class KGIntent(BaseModel):
    intent: str = Field(description="One of: prerequisite, reverse_prerequisite, study_path, course_info, category_query, unknown")
    course: str = Field(description="Target course name if specific, else empty")
    category: str = Field(description="Target category name (e.g. 'Math Electives', 'University Requirements') if specific, else empty")
    level: str = Field(description="Target level (1-4) if specific, else empty")
    program: str = Field(description="Target program (AI, Cybersecurity) if specific, else empty")


# ── Service ─────────────────────────────────────────────────────────

class KGService:
    """Handles Knowledge Graph queries via Neo4j."""

    def __init__(self):
        self.driver = None
        self.connected = False
        
        # Initialize LLM for intent extraction
        self.llm = ChatOpenAI(
            model=os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini"),
            temperature=0,  # Strict output
        )
        self.parser = JsonOutputParser(pydantic_object=KGIntent)
        
        self._connect()

    def _connect(self):
        """Attempt to connect to Neo4j. Gracefully handle failure."""
        try:
            uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            user = os.getenv("NEO4J_USER", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "password")

            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            self.connected = True
            logger.info("Connected to Neo4j successfully")
        except Exception as e:
            logger.error(f"Neo4j not available: {e}")
            logger.warning("KG queries will return fallback responses")
            self.connected = False

    def close(self):
        """Close the Neo4j driver connection."""
        if self.driver:
            self.driver.close()

    def get_all_course_names(self) -> List[str]:
        """Get a list of all course names and codes for routing."""
        if not self.connected:
            return []
        try:
            with self.driver.session() as session:
                result = session.run("MATCH (c:Course) RETURN c.name AS name, c.code AS code")
                records = list(result)
                return [r["name"] for r in records] + [r["code"] for r in records]
        except Exception as e:
            logger.error(f"Error fetching course names: {e}")
            return []

    @traceable(name="KG Query", run_type="chain")
    def query(self, question: str, history: Optional[List[Any]] = None) -> str:
        """
        Synthesize an answer using extracted intent and graph queries.
        Accepts optional history for context-aware classification.
        """
        if not self.connected:
            return "Knowledge Graph is currently unavailable."

        try:
            # 1. Classify intent and extracted entities
            extraction = self._classify_intent(question, history)
            intent = extraction.get("intent", "unknown")
            course = extraction.get("course")
            category = extraction.get("category")
            level = extraction.get("level")
            program = extraction.get("program")

            logger.info(f"Intent: {intent}, Course: {course}, Cat: {category}, Lvl: {level}, Prog: {program}")

            if intent == "prerequisite":
                return self._get_prereqs_forward(course if course else question)

            elif intent == "reverse_prerequisite":
                return self._get_prereqs_reverse(course if course else question)

            elif intent == "study_path":
                return self._handle_study_path(question, level or "", program or "")

            elif intent == "course_info":
                return self._query_courses(course if course else question)

            elif intent == "category_query" or (intent == "unknown" and category):
                return self._get_courses_in_category(category if category else question)
            
            else:
                return self._query_courses(question)

        except Exception as e:
            logger.error(f"Query error: {e}")
            return self._query_courses(question)

    def _classify_intent(self, question: str, history: Optional[List[Any]] = None) -> dict:
        """Detect intent using LLM (CoT/JSON). Handles follow-ups via history."""
        history_str = self._format_history(history)
        
        system_prompt = (
            "You are an academic advisor AI helper. Resolve intents using the 'Current Question' and context from 'History'.\n\n"
            "Intent Categories:\n"
            '1. "prerequisite": Asks what is needed BEFORE a course (requirements, how to unlock/open it).\n'
            '2. "reverse_prerequisite": Asks what a course leads to AFTER (what it opens, what closes if failed).\n'
            '3. "study_path": Asks for full plans, schedules, or level-based lists.\n'
            '4. "course_info": General details (credits, description).\n'
            '5. "category_query": Asks about a specific GROUP of courses (e.g. "Math Electives", "University Requirements", "Basic Science").\n\n'
            "CRITICAL RULES for Context & Pronouns:\n"
            "- If the question uses pronouns like 'it', 'this subject', 'the course', 'ها', 'هيه', 'المادة دي' -> YOU MUST extract the course name from the LAST 'Student' or 'Advisor' message in History.\n"
            "- NEVER return 'ها', 'هيه', 'دي', 'it' as the course name. If you see them, replace them with the actual course from history.\n"
            "- If the user says 'And X?' (e.g., 'And Math 2?'), copy the PREVIOUS intent but change the course to X.\n"
            "- 'بتقفل ايه' (closes what) or 'بتفتح ايه' (opens what) = reverse_prerequisite.\n"
            "- 'تتفتح بايه' (opened by what) = prerequisite.\n\n"
            "Extraction:\n"
            '- Extract "course" name (translate Arabic names to English, e.g. "خوارزميات"->"Algorithms").\n'
            '- Extract "category" name if the user asks about a group (e.g. "Math Electives") -> English Name.\n'
            '- IF users asks about "it" and you can\'t find a course in the current question, LOOK IN HISTORY.\n\n'
            "Result Format:\nJSON only."
        )

        examples = (
            "\nFew-Shot Examples:\n"
            'History: "User: Tell me about CS101." ... "User: What does it open?"\n'
            '-> {{"intent": "reverse_prerequisite", "course": "CS101"}}\n'
            'Question: "What are the Math Electives?"\n'
            '-> {{"intent": "category_query", "category": "Math & Basic Science (Elective)"}}\n'
            'Question: "ايه هي مواد العلوم الاساسية؟"\n'
            '-> {{"intent": "category_query", "category": "Math & Basic Science"}}\n'
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt + examples),
            ("user", "### History:\n{history}\n\n### Current Question:\n{question}"),
        ])
        
        chain = prompt | self.llm | self.parser
        
        try:
            result = chain.invoke({
                "question": question, 
                "history": history_str if history_str else "None"
            })
            return self._validate_and_resolve_pronouns(result, history_str)
        except Exception as e:
            logger.error(f"Intent extraction failed: {e}")
            return {"intent": "unknown"}

    @traceable(name="KG Category Query", run_type="retriever")
    def _get_courses_in_category(self, query: str) -> str:
        """List all courses in a specific category."""
        if not self.connected:
            return "Knowledge Graph is unavailable."

        # Find best matching category
        cat_node = self._find_category_node(query)
        if not cat_node:
            return f"Could not find a category matching '{query}'."

        cat_name = cat_node["name"]
        
        with self.driver.session() as session:
            # Get category details
            cat_res = session.run(
                "MATCH (cat:Category {name: $name}) RETURN cat.required_hours AS req, cat.type AS type",
                name=cat_name
            )
            cat_info = cat_res.single()
            req_hours = cat_info["req"] if cat_info else "?"
            cat_type = cat_info["type"] if cat_info else "unknown"

            # Get courses
            res = session.run(
                """
                MATCH (c:Course)-[:BELONGS_TO]->(cat:Category {name: $name})
                RETURN c.code AS code, c.name AS name, c.credit_hours AS ch, c.level AS level
                ORDER BY c.code
                """,
                name=cat_name
            )
            courses = [dict(r) for r in res]

        if not courses:
            return f"No courses found in category '{cat_name}'."

        lines = [f"📂 Category: {cat_name}"]
        lines.append(f"   • Type: {cat_type.capitalize()}")
        lines.append(f"   • Required Hours: {req_hours}")
        lines.append(f"   • Available Courses ({len(courses)}):")
        
        for c in courses:
            lines.append(f"     - [{c['code']}] {c['name']} ({c['ch']} CH)")
        
        return "\n".join(lines)

    def _find_category_node(self, query: str) -> Optional[dict]:
        """Find best-matching category node using fuzzy matching."""
        if not self.connected:
            return None

        clean_query = self._expand_abbreviations(query.lower())
        
        with self.driver.session() as session:
            result = session.run("MATCH (cat:Category) RETURN cat.name AS name")
            categories = [r["name"] for r in result]

        if not categories:
            return None

        # Exact match
        for cat in categories:
            if cat.lower() == clean_query:
                return {"name": cat}

        # Fuzzy match
        matches = difflib.get_close_matches(query, categories, n=1, cutoff=0.4)
        if matches:
            return {"name": matches[0]}
            
        # Keyword match
        query_words = set(clean_query.split())
        best_cat = None
        max_overlap = 0
        
        for cat in categories:
            cat_words = set(cat.lower().split())
            overlap = len(query_words & cat_words)
            if overlap > max_overlap:
                max_overlap = overlap
                best_cat = cat
        
        if max_overlap > 0:
            return {"name": best_cat}
            
        return None

    def _format_history(self, history: Optional[List[Any]]) -> str:
        """Format history list into a string block."""
        if not history:
            return ""
        context_msgs = history[-6:] # Last 3 rounds
        lines = []
        for m in context_msgs:
            role = "Student" if isinstance(m, HumanMessage) else "Advisor"
            lines.append(f"{role}: {m.content}")
        return "\n".join(lines)

    def _validate_and_resolve_pronouns(self, result: dict, history_str: str) -> dict:
        """Check for pronoun placeholders and resolve them programmatically if needed."""
        course = result.get("course", "").strip().lower()
        if course in PRONOUNS_TO_RESOLVE and history_str:
            logger.info(f"Detected pronoun '{course}', resolving from history...")
            resolved_course = self._resolve_course_from_history(history_str)
            if resolved_course:
                result["course"] = resolved_course
                logger.info(f"Resolved to '{resolved_course}'")
        return result

    def _resolve_course_from_history(self, history_str: str) -> Optional[str]:
        """Fallback: Extract the last discussed course from history."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Identify the academic course being discussed in the following conversation history. Return ONLY the course name in English. If none, return 'None'."),
            ("user", "{history}")
        ])
        chain = prompt | self.llm | StrOutputParser()
        try:
            return chain.invoke({"history": history_str}).strip()
        except:
            return None

    def _find_course_node(self, query: str) -> Optional[dict]:
        """Find best-matching course node using fuzzy matching (difflib)."""
        if not self.connected:
            return None

        clean_query = self._expand_abbreviations(query.lower())
        
        # strip non-alphanumeric (keep spaces)
        clean_query = re.sub(r'[^\w\s]', ' ', clean_query)
        
        # get all courses
        with self.driver.session() as session:
            result = session.run("MATCH (c:Course) RETURN c.code AS code, c.name AS name")
            courses = [dict(r) for r in result]

        if not courses:
            return None

        # 1. Exact match (code or name)
        for c in courses:
            if c['code'].lower() in clean_query or c['name'].lower() in clean_query:
                return c

        # 2. Fuzzy match
        # Create a map of "candidate string" -> course dict
        candidates = {}
        for c in courses:
            candidates[c['name'].lower()] = c
            candidates[c['code'].lower()] = c
        
        matches = difflib.get_close_matches(clean_query, candidates.keys(), n=1, cutoff=0.6)
        if matches:
            return candidates[matches[0]]
            
        # 3. Partial word match (fallback for multi-word queries)
        q_words = set(clean_query.split())
        best_c = None
        max_overlap = 0
        
        for c in courses:
            c_words = set(c['name'].lower().split())
            overlap = len(q_words & c_words)
            if overlap > max_overlap:
                max_overlap = overlap
                best_c = c
        
        if max_overlap >= 1: # Require at least 1 word match
            return best_c

        return None

    def _expand_abbreviations(self, text: str) -> str:
        """Replace known abbreviations with full terms."""
        for abbr, expanded in ABBREVIATIONS.items():
            pattern = r'\b' + abbr + r'\b'
            text = re.sub(pattern, expanded, text)
        return text

    @traceable(name="KG Prereqs Forward", run_type="retriever")
    def _get_prereqs_forward(self, query: str) -> str:
        """What do I need BEFORE this course?"""
        course = self._find_course_node(query)
        if not course:
            return f"Could not find a course matching '{query}'."

        code, name = course["code"], course["name"]
        
        with self.driver.session() as session:
            # Direct prerequisites
            res = session.run(
                "MATCH (c:Course {code: $code})-[:REQUIRES]->(p:Course) RETURN p.code AS code, p.name AS name",
                code=code
            )
            direct = [dict(r) for r in res]

            if not direct:
                return f"The course [{code}] {name} has no prerequisites. You can take it directly!"

            wants_full = any(kw in query.lower() for kw in ["all", "full", "chain", "everything", "كل", "بالكامل"])
            
            lines = [f"📚 Prerequisites for [{code}] {name}:"]
            direct_text = ", ".join(f"{p['name']} [{p['code']}]" for p in direct)
            lines.append(f"  ➤ Core Requirements: {direct_text}")

            if wants_full:
                chain_res = session.run(
                    "MATCH (c:Course {code: $code})-[:REQUIRES*]->(p:Course) RETURN DISTINCT p.code AS code, p.name AS name, p.level AS level ORDER BY p.level",
                    code=code
                )
                chain = [dict(r) for r in chain_res]
                if len(chain) > len(direct):
                    lines.append(f"\n  🔗 Full Prerequisite Chain ({len(chain)} total):")
                    for p in chain:
                        lines.append(f"    • Level {p['level']}: [{p['code']}] {p['name']}")
            else:
                lines.append("\n💡 Hint: Ask for the 'full chain' to see all dependencies.")
            
            return "\n".join(lines)

    @traceable(name="KG Prereqs Reverse", run_type="retriever")
    def _get_prereqs_reverse(self, query: str) -> str:
        """What does this course OPEN?"""
        course = self._find_course_node(query)
        if not course:
            return f"Could not find a course matching '{query}'."

        code, name = course["code"], course["name"]

        with self.driver.session() as session:
            result = session.run(
                "MATCH (f:Course)-[:REQUIRES]->(c:Course {code: $code}) RETURN f.name AS name, f.code AS code",
                code=code
            )
            futures = [dict(r) for r in result]

            if not futures:
                return f"The course [{code}] {name} is not a prerequisite for any future courses."

            lines = [f"🔓 [{code}] {name} is a prerequisite for:"]
            for f in futures:
                lines.append(f"  ➤ [{f['code']}] {f['name']}")
            return "\n".join(lines)

    def _handle_study_path(self, question: str, level: str, program: str) -> str:
        """Route study path queries."""
        if level and program:
            return self.get_study_path(int(level), program)
        elif level:
            return self.get_study_path(int(level), "General")
        else:
            return self._query_courses(question)

    @traceable(name="KG Get Study Path", run_type="retriever")
    def get_study_path(self, level: int, major: str) -> str:
        """Get recommended study path."""
        if not self.connected:
            return "Knowledge Graph is unavailable."

        try:
            with self.driver.session() as session:
                query = """
                    MATCH (p:Program)-[:OFFERS]->(c:Course)
                    WHERE c.level = $level
                    AND ($major = "General" OR p.name = $major)
                    OPTIONAL MATCH (c)-[:REQUIRES]->(prereq:Course)
                    RETURN DISTINCT c.name AS course, c.code AS code,
                           c.credit_hours AS credits,
                           collect(DISTINCT prereq.name) AS prerequisites
                    ORDER BY c.name
                """
                result = session.run(query, major=major, level=level)
                courses = [dict(r) for r in result]

            if not courses:
                return f"No courses found for {major} at Level {level}."

            lines = [f"📚 Recommended courses for {major} — Level {level}:\n"]
            for c in courses:
                prereqs = [p for p in c.get("prerequisites", []) if p]
                prereq_text = f" (Prerequisites: {', '.join(prereqs)})" if prereqs else ""
                lines.append(f"  • {c['course']} [{c.get('code', '')}] — {c.get('credits', '?')} credits{prereq_text}")
            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Error getting study path: {e}")
            return f"Error retrieving study path: {str(e)}"

    def _query_courses(self, question: str) -> str:
        """Handle course listing queries."""
        try:
            question_lower = question.lower()
            
            # 1. Try specific course
            best_match = self._find_course_node(question)
            
            # Detect program/level
            target_prog = "Cybersecurity" if any(w in question_lower for w in ["cyber", "سايبر"]) else \
                          "Artificial Intelligence" if any(w in question_lower for w in ["ai", "artificial", "ذكاء"]) else None

            target_level = None
            for lvl, keywords in ARABIC_ORDINALS.items():
                if any(w in question_lower for w in keywords + [f"level {lvl}", f"lvl {lvl}", f"سنة {lvl}"]):
                    target_level = lvl
                    break

            # If specific match and no broad intent, return details
            if (not target_prog and not target_level) and best_match:
                c = best_match
                return (
                    f"📚 Course Info: [{c['code']}] {c['name']}\n"
                    f"   • Credits: {c.get('credits', '?')}\n"
                    f"   • Level: {c.get('level', '?')}\n"
                    f"   • Description: Standard core course." # Placeholder description
                )

            # Query list
            with self.driver.session() as session:
                cypher = "MATCH (p:Program)-[:OFFERS]->(c:Course) WHERE 1=1"
                params: Dict[str, Any] = {}
                if target_prog:
                    cypher += " AND p.name = $prog"
                    params["prog"] = target_prog
                if target_level:
                    cypher += " AND c.level = $level"
                    params["level"] = int(target_level)

                cypher += " RETURN p.name AS program, c.name AS course, c.code AS code, c.credit_hours AS credits, c.level AS level ORDER BY p.name, c.level"
                result = session.run(cypher, **params)
                records = [dict(r) for r in result]

            if not records:
                return "No courses found matching your query."

            # Simplify output logic (use helper if complex)
            return self._format_course_list(records, target_prog or "", int(target_level) if target_level else 0)

        except Exception as e:
            logger.error(f"Error querying courses: {e}")
            return f"Error querying courses: {str(e)}"

    def _format_course_list(self, records: List[dict], target_prog: str, target_level: int) -> str:
        """Format the course list output."""
        if target_level or target_prog:
            # Detailed list
            lines = ["📚 Courses:\n"]
            current_prog = ""
            for r in records:
                if r["program"] != current_prog:
                    lines.append(f"\n🎓 {r['program']}:")
                    current_prog = r["program"]
                lines.append(f"  • [{r['code']}] {r['course']} — {r['credits']} credits")
            return "\n".join(lines)
        else:
            # Summary
            summary: Dict[str, Dict[Any, int]] = {}
            for r in records:
                prog = r["program"]
                lvl = r["level"]
                if prog not in summary: summary[prog] = {}
                if lvl not in summary[prog]: summary[prog][lvl] = 0
                summary[prog][lvl] += 1
            
            lines = ["📚 Course Summary:\n"]
            for prog, levels in summary.items():
                lines.append(f"🎓 {prog}:")
                for lvl in sorted(levels.keys()):
                    lines.append(f"  Level {lvl}: {levels[lvl]} courses")
            return "\n".join(lines)

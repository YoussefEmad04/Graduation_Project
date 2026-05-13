import unittest
from datetime import datetime, timedelta, timezone
from uuid import UUID
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from advisor_ai.chat_controller import ChatController
from advisor_ai.graph import AdvisorGraph
from advisor_ai.kg_service import KGService, get_neo4j_config
from advisor_ai.rag_service import REGULATIONS_CLEAN_EXCERPTS, RAGService
from advisor_ai.followup_resolver import FollowupDecision
from advisor_ai.router_service import RouterDecision


class _FakeResult:
    def __init__(self, data=None):
        self.data = data or []


class _FakeQuery:
    def __init__(self, db, table_name):
        self.db = db
        self.table_name = table_name
        self.filters = []
        self.insert_rows = None
        self.update_values = None
        self.delete_rows = False
        self.order_field = None
        self.order_desc = False
        self.row_limit = None

    def select(self, *_args):
        return self

    def insert(self, rows):
        self.insert_rows = rows if isinstance(rows, list) else [rows]
        return self

    def update(self, values):
        self.update_values = values
        return self

    def delete(self):
        self.delete_rows = True
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def order(self, field, desc=False):
        self.order_field = field
        self.order_desc = desc
        return self

    def limit(self, count):
        self.row_limit = count
        return self

    def _matches(self, row):
        return all(row.get(field) == value for field, value in self.filters)

    def execute(self):
        table = self.db.tables[self.table_name]
        if self.insert_rows is not None:
            for row in self.insert_rows:
                row = dict(row)
                timestamp = self.db.next_timestamp()
                row.setdefault("created_at", timestamp)
                row.setdefault("updated_at", timestamp)
                table.append(row)
            return _FakeResult(self.insert_rows)

        if self.update_values is not None:
            for row in table:
                if self._matches(row):
                    row.update(self.update_values)
            return _FakeResult([])

        if self.delete_rows:
            self.db.tables[self.table_name] = [
                row for row in table if not self._matches(row)
            ]
            return _FakeResult([])

        data = [dict(row) for row in table if self._matches(row)]
        if self.order_field:
            data.sort(
                key=lambda row: row.get(self.order_field) or "",
                reverse=self.order_desc,
            )
        if self.row_limit is not None:
            data = data[: self.row_limit]
        return _FakeResult(data)


class _FakeSupabase:
    def __init__(self):
        self.tables = {"sessions": [], "messages": []}
        self._clock = datetime(2026, 4, 17, tzinfo=timezone.utc)

    def table(self, table_name):
        return _FakeQuery(self, table_name)

    def next_timestamp(self):
        self._clock += timedelta(seconds=1)
        return self._clock.isoformat()


class _FakeGraph:
    def run(self, **_kwargs):
        return "answer"


class _CapturingGraph:
    def __init__(self):
        self.calls = []

    def run(self, **kwargs):
        self.calls.append(kwargs)
        return "answer"


class _FakeElectiveService:
    def __init__(self):
        self.electives = []

    def set_electives(self, electives):
        self.electives = electives


class _TaggedRagService:
    def query(self, question):
        return f"RAG::{question}"


class _TaggedKgService:
    def query(self, question, history=None):
        return f"KG::{question}"

    def get_study_path(self, student_level, student_major):
        return f"KG-STUDY::{student_level}::{student_major}"


class _MissingKgService:
    def query(self, question, history=None):
        return f"Could not find a course matching '{question}'."

    def get_study_path(self, student_level, student_major):
        return f"No courses found for {student_major} at Level {student_level}."


class _UnavailableKgService:
    def query(self, question, history=None):
        return "Knowledge Graph is currently unavailable."

    def get_study_path(self, student_level, student_major):
        return "Knowledge Graph is unavailable."


class _TaggedMentalService:
    def is_major_query(self, question):
        normalized = question.lower()
        return any(
            phrase in normalized
            for phrase in (
                "which major", "choose major", "ai or cyber", "cyber or ai",
                "اختار ai ولا cyber", "اختار تخصص", "ذكاء ولا سايبر", "سايبر ولا ذكاء",
            )
        )

    def get_response(self, question, student_level=None):
        return f"MENTAL::{question}::{student_level}"

    def get_major_recommendation(self, question):
        return f"MAJOR::{question}"


class _TaggedElectiveService:
    def __init__(self):
        self._electives = []

    def query(self, question):
        return f"ELECTIVE::{question}"

    def get_electives(self):
        return self._electives


class _FakeNeo4jSession:
    courses = [
        {"code": "CS102", "name": "Programming 2", "credits": 3, "level": 1},
        {"code": "CS201", "name": "Object Oriented Programming", "credits": 3, "level": 2},
        {"code": "SW201", "name": "Software Engineering", "credits": 3, "level": 2},
        {"code": "SW303", "name": "User Interface Design", "credits": 3, "level": 3},
        {"code": "SW401", "name": "Software Testing & Quality Assurance", "credits": 3, "level": 4},
        {"code": "AI301", "name": "Machine Learning", "credits": 3, "level": 3},
        {"code": "AI201", "name": "Introduction to Artificial Intelligence", "credits": 3, "level": 2},
        {"code": "MTH104", "name": "Probability and Statistics 1", "credits": 3, "level": 1},
        {"code": "AI302", "name": "Natural Language Processing", "credits": 3, "level": 3},
        {"code": "AI304", "name": "Computer Vision", "credits": 3, "level": 3},
        {"code": "AI305", "name": "Pattern Recognition", "credits": 3, "level": 3},
        {"code": "AI401", "name": "Intelligent Algorithms", "credits": 3, "level": 4},
        {"code": "AI403", "name": "Deep Learning", "credits": 3, "level": 4},
        {"code": "AI404", "name": "Graduation Project 1", "credits": 3, "level": 4},
        {"code": "AI405", "name": "Multi Agent Systems", "credits": 3, "level": 4},
        {"code": "AI307", "name": "Computational Learning Theory", "credits": 3, "level": 3},
        {"code": "AI408", "name": "Cognitive Modeling", "credits": 3, "level": 4},
        {"code": "AI413", "name": "AI for Robotics", "credits": 3, "level": 4},
    ]
    prereqs = {
        "CS201": [
            {"code": "CS102", "name": "Programming 2"},
        ],
        "SW201": [
            {"code": "CS201", "name": "Object Oriented Programming"},
        ],
        "AI301": [
            {"code": "AI201", "name": "Introduction to Artificial Intelligence"},
            {"code": "MTH104", "name": "Probability and Statistics 1"},
        ],
    }
    unlocked = {
        "CS201": [
            {"code": "SW201", "name": "Software Engineering"},
        ],
        "SW201": [
            {"code": "SW303", "name": "User Interface Design"},
            {"code": "SW401", "name": "Software Testing & Quality Assurance"},
        ],
        "AI301": [
            {"code": "AI302", "name": "Natural Language Processing"},
            {"code": "AI304", "name": "Computer Vision"},
            {"code": "AI305", "name": "Pattern Recognition"},
            {"code": "AI401", "name": "Intelligent Algorithms"},
            {"code": "AI403", "name": "Deep Learning"},
            {"code": "AI404", "name": "Graduation Project 1"},
            {"code": "AI405", "name": "Multi Agent Systems"},
            {"code": "AI307", "name": "Computational Learning Theory"},
            {"code": "AI408", "name": "Cognitive Modeling"},
            {"code": "AI413", "name": "AI for Robotics"},
        ],
    }

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def run(self, query, **params):
        if "MATCH (c:Course) RETURN c.code AS code" in query:
            return list(self.courses)
        if "MATCH (c:Course {code: $code})-[:REQUIRES]->(p:Course)" in query:
            return list(self.prereqs.get(params["code"], []))
        if "MATCH (f:Course)-[:REQUIRES]->(c:Course {code: $code})" in query:
            return list(self.unlocked.get(params["code"], []))
        return []


class _InMemoryPrereqKG(KGService):
    def __init__(self):
        self.connected = True
        self.driver = object()
        self.config = {}
        self.llm = None

    def _ensure_connected(self):
        return True

    def _session(self):
        return _FakeNeo4jSession()


class _FakeRouterService:
    def __init__(self, decision=None):
        self.decision = decision
        self.calls = []

    def route_question(self, question, history=None, student_level=None, student_major=None):
        self.calls.append(
            {
                "question": question,
                "history": history,
                "student_level": student_level,
                "student_major": student_major,
            }
        )
        return self.decision


class _FakeFollowupResolver:
    def __init__(self, decision=None):
        self.decision = decision
        self.calls = []

    def resolve(self, question, history=None, student_level=None, student_major=None):
        self.calls.append(
            {
                "question": question,
                "history": history,
                "student_level": student_level,
                "student_major": student_major,
            }
        )
        return self.decision


class RoutingSmokeTests(unittest.TestCase):
    def setUp(self):
        self.graph = AdvisorGraph.__new__(AdvisorGraph)
        self.graph.course_names = ["Machine Learning", "Graduation Project 1"]

    def test_semantic_router_high_confidence_overrides_heuristics(self):
        self.graph.router_service = _FakeRouterService(
            RouterDecision(
                route="mental",
                sub_intent="support",
                rewritten_question="I am overwhelmed and need study support.",
                confidence=0.91,
                entities={},
                reasoning="Clear distress phrasing.",
            )
        )
        state = {"question": "Machine Learning prerequisites are stressing me out"}

        routed = self.graph._router_node(state)

        self.assertEqual(routed["route"], "mental")
        self.assertEqual(routed["route_sub_intent"], "support")
        self.assertEqual(routed["rewritten_question"], "I am overwhelmed and need study support.")
        self.assertEqual(routed["route_entities"], {})

    def test_semantic_router_low_confidence_falls_back_to_heuristics(self):
        self.graph.router_service = _FakeRouterService(
            RouterDecision(
                route="mental",
                sub_intent="support",
                rewritten_question="Need emotional help.",
                confidence=0.42,
                entities={},
                reasoning="Weak guess.",
            )
        )
        state = {"question": "What are the prerequisites for Machine Learning?"}

        routed = self.graph._router_node(state)

        self.assertEqual(routed["route"], "kg")
        self.assertEqual(routed["rewritten_question"], "What are the prerequisites for Machine Learning?")
        self.assertEqual(routed["route_confidence"], 0.42)

    def test_semantic_router_receives_student_context(self):
        self.graph.router_service = _FakeRouterService(
            RouterDecision(
                route="kg",
                sub_intent="study_path",
                rewritten_question="What are the level 3 AI courses?",
                confidence=0.84,
                entities={"level": "3", "major": "AI"},
                reasoning="Clear study-path request.",
            )
        )
        history = [HumanMessage(content="I am in level 3")]

        self.graph._router_node(
            {
                "question": "What courses should I take?",
                "history": history,
                "student_level": 3,
                "student_major": "AI",
            }
        )

        self.assertEqual(len(self.graph.router_service.calls), 1)
        call = self.graph.router_service.calls[0]
        self.assertEqual(call["student_level"], 3)
        self.assertEqual(call["student_major"], "AI")
        self.assertEqual(call["history"], [])

    def test_semantic_validation_corrects_course_relationship_intents(self):
        cases = [
            (
                "Machine Learning بتفتح ايه؟",
                "courses_unlocked_by_course",
                {"course": "Machine Learning"},
            ),
            (
                "لو خدت machine learning بعدها اخد ايه؟",
                "courses_unlocked_by_course",
                {"course": "Machine Learning"},
            ),
            (
                "what does AI301 unlock?",
                "courses_unlocked_by_course",
                {"course": "AI301"},
            ),
            (
                "AI301 prerequisite",
                "prerequisites_for_course",
                {"course": "AI301"},
            ),
            (
                "ايه prerequisite بتاع AI301؟",
                "prerequisites_for_course",
                {"course": "AI301"},
            ),
            (
                "لو مخدتش AI301 ايه اللي هيتقفل؟",
                "courses_blocked_if_not_completed",
                {"course": "AI301"},
            ),
        ]
        for question, expected_sub_intent, expected_entities in cases:
            with self.subTest(question=question):
                self.graph.router_service = _FakeRouterService(
                    RouterDecision(
                        route="rag",
                        sub_intent="regulation",
                        intent="regulation_query",
                        rewritten_question=question,
                        confidence=0.91,
                        entities={},
                        reasoning="Wrong broad semantic route.",
                    )
                )
                routed = self.graph._router_node({"question": question, "history": []})
                self.assertEqual(routed["route"], "kg")
                self.assertEqual(routed["route_sub_intent"], expected_sub_intent)
                for key, value in expected_entities.items():
                    self.assertEqual(routed["route_entities"].get(key), value)

    def test_semantic_validation_fills_level_program_study_plan_entities(self):
        cases = [
            ("ايه مواد سنة تالته ذكاء اصطناعي؟", "3", "Artificial Intelligence"),
            ("مواد level 3 AI", "3", "Artificial Intelligence"),
            ("ايه مواد سنه تالته AI", "3", "Artificial Intelligence"),
            ("ايه مواد سنة ثالثة Artificial Intelligence", "3", "Artificial Intelligence"),
            ("مواد third year ذكاء اصطناعي", "3", "Artificial Intelligence"),
        ]
        for question, level, program in cases:
            with self.subTest(question=question):
                self.graph.router_service = _FakeRouterService(
                    RouterDecision(
                        route="kg",
                        sub_intent="study_path",
                        intent="study_plan_query",
                        rewritten_question=question,
                        confidence=0.9,
                        entities={},
                        missing_entities=["level", "program"],
                        reasoning="Study-plan request.",
                    )
                )
                routed = self.graph._router_node({"question": question, "history": []})
                self.assertEqual(routed["route"], "kg")
                self.assertEqual(routed["route_sub_intent"], "study_path")
                self.assertEqual(routed["route_entities"].get("level"), level)
                self.assertEqual(routed["route_entities"].get("program"), program)

    def test_broad_study_plan_signal_does_not_override_high_confidence_semantic_route(self):
        self.graph.router_service = _FakeRouterService(
            RouterDecision(
                route="rag",
                sub_intent="regulation",
                intent="regulation_query",
                rewritten_question="What is the policy for third-year AI course lists?",
                confidence=0.9,
                entities={"policy_topic": "study_plan_table"},
                reasoning="LLM chose regulation table lookup.",
            )
        )

        routed = self.graph._router_node({"question": "ايه مواد سنه تالته AI", "history": []})

        self.assertEqual(routed["route"], "rag")
        self.assertEqual(routed["route_sub_intent"], "regulation")

    def test_semantic_validation_forces_requirement_type(self):
        cases = [
            ("ايه متطلبات الجامعة الاجبارية؟", "compulsory"),
            ("university compulsory requirements", "compulsory"),
            ("ايه المواد الاختيارية في الجامعة؟", "elective"),
        ]
        for question, requirement_type in cases:
            with self.subTest(question=question):
                self.graph.router_service = _FakeRouterService(
                    RouterDecision(
                        route="kg",
                        sub_intent="category_query",
                        intent="category_requirement_query",
                        rewritten_question=question,
                        confidence=0.9,
                        entities={"category": "University Requirements", "requirement_type": "elective" if requirement_type == "compulsory" else "compulsory"},
                        reasoning="Category identified, requirement type needs validation.",
                    )
                )
                routed = self.graph._router_node({"question": question, "history": []})
                self.assertEqual(routed["route"], "kg")
                self.assertEqual(routed["route_sub_intent"], "category_query")
                self.assertEqual(routed["route_entities"].get("requirement_type"), requirement_type)

    def test_broad_category_signal_does_not_override_high_confidence_semantic_route(self):
        self.graph.router_service = _FakeRouterService(
            RouterDecision(
                route="rag",
                sub_intent="regulation",
                intent="regulation_query",
                rewritten_question="What is the official policy for university requirements?",
                confidence=0.9,
                entities={"policy_topic": "university_requirements"},
                reasoning="LLM chose regulation policy.",
            )
        )

        routed = self.graph._router_node({"question": "university compulsory requirements", "history": []})

        self.assertEqual(routed["route"], "rag")
        self.assertEqual(routed["route_sub_intent"], "regulation")

    def test_category_hours_signal_does_not_override_high_confidence_semantic_route(self):
        self.graph.router_service = _FakeRouterService(
            RouterDecision(
                route="mental",
                sub_intent="support",
                intent="general_chat",
                rewritten_question="I need help planning my study load.",
                confidence=0.9,
                entities={},
                reasoning="Support request despite category-hour wording.",
            )
        )

        routed = self.graph._router_node(
            {"question": "How many credit hours for Basic Computer Science is stressing me out?", "history": []}
        )

        self.assertEqual(routed["route"], "mental")
        self.assertEqual(routed["route_sub_intent"], "support")

    def test_router_decision_defaults_missing_entities(self):
        decision = RouterDecision(
            route="kg",
            sub_intent="study_path",
            intent="study_plan_query",
            confidence=0.9,
            entities={"level": "3"},
        )

        self.assertEqual(decision.missing_entities, [])

    def test_semantic_router_missing_entities_are_returned(self):
        self.graph.router_service = _FakeRouterService(
            RouterDecision(
                route="kg",
                sub_intent="study_path",
                intent="study_plan_query",
                rewritten_question="What are the level 3 courses?",
                confidence=0.9,
                entities={"level": "3"},
                missing_entities=["program"],
                reasoning="Missing program.",
            )
        )

        routed = self.graph._router_node({"question": "ايه مواد سنة تالته؟", "history": []})

        self.assertEqual(routed["route"], "kg")
        self.assertEqual(routed["route_missing_entities"], ["program"])

    def test_student_record_semantic_query_returns_unsupported(self):
        self.graph.router_service = _FakeRouterService(
            RouterDecision(
                route="hybrid",
                sub_intent="unsupported_student_record",
                intent="student_record_query",
                rewritten_question="What is my CGPA?",
                confidence=0.92,
                entities={"record_type": "cgpa"},
                missing_entities=[],
                reasoning="Student-specific record request.",
            )
        )

        routed = self.graph._router_node({"question": "What is my CGPA?", "history": []})

        self.assertEqual(routed["route"], "hybrid")
        self.assertEqual(routed["route_sub_intent"], "unsupported_student_record")
        self.assertIn("I can’t access student-specific records", routed["final_answer"])

    def test_student_record_heuristic_query_returns_unsupported_without_llm(self):
        self.graph.router_service = _FakeRouterService(None)

        routed = self.graph._router_node({"question": "ايه الدرجات بتاعتي؟", "history": []})

        self.assertEqual(routed["route"], "hybrid")
        self.assertEqual(routed["route_sub_intent"], "unsupported_student_record")
        self.assertIn("مش قادر أوصل لبياناتك الشخصية", routed["final_answer"])

    def test_followup_resolver_is_not_used_for_runtime_routing(self):
        self.graph.followup_resolver = _FakeFollowupResolver(
            FollowupDecision(is_followup=True, route="mental", rewritten_question="wrong", confidence=1.0)
        )
        self.graph.router_service = _FakeRouterService(
            RouterDecision(
                route="kg",
                sub_intent="prerequisites_for_course",
                rewritten_question="What are the prerequisites for AI301?",
                confidence=0.9,
                entities={"course": "AI301"},
                reasoning="Standalone course question.",
            )
        )
        history = [HumanMessage(content="What is the maximum credit load for the regular semester?")]
        state = {"question": "What are the prerequisites for AI301?", "history": history}

        routed = self.graph._router_node(state)

        self.assertEqual(routed["route"], "kg")
        self.assertEqual(len(self.graph.followup_resolver.calls), 0)
        self.assertEqual(self.graph.router_service.calls[0]["history"], [])

    def test_semantic_router_ignores_old_history_after_followup_removal(self):
        self.graph.router_service = _FakeRouterService(
            RouterDecision(
                route="kg",
                sub_intent="prerequisites_for_course",
                rewritten_question="ايه متطلبات AI301؟",
                confidence=0.9,
                entities={"course": "AI301"},
                reasoning="Current message is a standalone course question.",
            )
        )
        history = [HumanMessage(content="What is the maximum credit load for the regular semester?")]
        state = {"question": "طيب ايه متطلبات AI301؟", "history": history}

        routed = self.graph._router_node(state)

        self.assertEqual(routed["route"], "kg")
        self.assertEqual(routed["route_sub_intent"], "prerequisites_for_course")
        self.assertEqual(self.graph.router_service.calls[0]["history"], [])

    def test_current_question_semantics_override_old_history(self):
        self.graph.router_service = _FakeRouterService(
            RouterDecision(
                route="kg",
                sub_intent="prerequisites_for_course",
                rewritten_question="ايه متطلبات AI301؟",
                confidence=0.86,
                entities={"course": "AI301"},
                reasoning="Current message names a specific course.",
            )
        )
        history = [HumanMessage(content="What is the maximum credit load for the regular semester?")]
        state = {"question": "طيب ايه متطلبات AI301؟", "history": history}

        routed = self.graph._router_node(state)

        self.assertEqual(routed["route"], "kg")
        self.assertEqual(routed["route_sub_intent"], "prerequisites_for_course")
        self.assertEqual(self.graph.router_service.calls[0]["history"], [])

    def test_graduation_credit_question_routes_to_rag(self):
        state = {"question": "How many credit hours are required for graduation?"}
        self.assertEqual(self.graph._router_node(state)["route"], "rag")

    def test_specific_course_question_routes_to_kg(self):
        state = {"question": "What are the prerequisites for Machine Learning?"}
        self.assertEqual(self.graph._router_node(state)["route"], "kg")

    def test_exam_absence_question_routes_to_rag(self):
        state = {"question": "لو حصل ظرف ومحضرتش امتحان الميد ترم اعمل ايه؟"}
        self.assertEqual(self.graph._router_node(state)["route"], "rag")

    def test_short_followup_no_longer_reuses_previous_course_route(self):
        history = [
            HumanMessage(content="طيب ايه عشان اسجل ماده math 2 ايه المواد الي المفروض اكون خدتها")
        ]
        state = {"question": "اه داه الي محتاج اعرفو", "history": history}
        self.assertEqual(self.graph._router_node(state)["route"], "hybrid")

    def test_duration_followup_no_longer_reuses_previous_rag_route(self):
        history = [
            HumanMessage(content="هو الحد الاقصي للتسجيل في الفصل الصيفي كام ساعه")
        ]
        state = {"question": "طيب هو مدتو كام اسبوع", "history": history}
        self.assertEqual(self.graph._router_node(state)["route"], "hybrid")

    def test_mental_followup_uses_current_question_only(self):
        self.graph.router_service = _FakeRouterService(
            RouterDecision(
                route="rag",
                sub_intent="exam_policy",
                rewritten_question="What is the policy for the night before exams?",
                confidence=0.91,
                entities={},
                reasoning="Contains exam-related wording.",
            )
        )
        history = [
            HumanMessage(content="I feel very stressed before exams"),
            AIMessage(content="Try a realistic study plan, breaks, and support."),
        ]
        state = {"question": "and what should I do the night before?", "history": history}

        routed = self.graph._router_node(state)

        self.assertEqual(routed["route"], "rag")
        self.assertEqual(len(self.graph.router_service.calls), 1)

    def test_program_semester_course_list_routes_to_rag(self):
        state = {
            "question": "طيب ايه مواد الترم الاول سنه تالته قسم ذكاء اصطناعى",
            "history": [],
        }
        self.assertEqual(self.graph._router_node(state)["route"], "rag")

    def test_general_level_study_path_routes_to_kg(self):
        state = {
            "question": "عاوز خطة الدراسة للفرقة الأولى عامةً.",
            "history": [],
        }
        self.assertEqual(self.graph._router_node(state)["route"], "kg")

    def test_failed_regulation_prompts_route_to_rag(self):
        prompts = [
            "الدراسة في الكلية ماشية بأي نظام؟",
            "مدة الفصل الدراسي النظامي كام أسبوع؟",
            "How long is a regular semester?",
            "Is the summer semester mandatory?",
            "Max credit hours in the summer semester?",
            "التسجيل في المقررات يستمر لحد إمتى؟",
            "Until when can a student register for courses?",
            "Until when can a student withdraw from a course?",
            "حتى متى يمكن للطالب الانسحاب من مقرر؟",
            "الـ withdrawal لازم يكون قبل إمتى؟",
            "لو الطالب انسحب بعد الـ deadline بدون عذر يحصل ايه؟",
            "إيه شرط التسجيل في مقرر؟",
            "هل رأي المرشد الأكاديمي إلزامي؟",
            "الطالب يقدر ينسحب من مقرر لحد إمتى؟",
            "لو الطالب انسحب في الميعاد، هل يعتبر راسب؟",
            "الدرجة النهائية لأي مقرر من كام؟",
            "أقل درجة للنجاح في أي مقرر كام؟",
            "ايه الـ minimum للنجاح في أي مقرر؟",
            "شرط النجاح المرتبط بالامتحان النهائي التحريري إيه؟",
            "What is the minimum required from the final exam to pass?",
            "توزيع الدرجات في الـ theoretical course عامل إزاي؟",
            "نسبة الحضور المطلوبة لدخول الامتحان النهائي كام؟",
            "What attendance percentage is required to sit the final exam?",
            "لو الطالب غاب عن الامتحان النهائي بعذر قهري مقبول يحصل إيه؟",
        ]
        for prompt in prompts:
            with self.subTest(prompt=prompt):
                self.assertEqual(self.graph._router_node({"question": prompt, "history": []})["route"], "rag")

    def test_dismissal_appeals_and_grade_questions_route_to_rag(self):
        prompts = [
            "ايه حالات الفصل من الكلية؟",
            "لو عايز أعمل تظلم على نتيجة مادة، عندي مهلة قد ايه؟",
            "لو ال CGPA عندي 3.2 يبقى التقدير العام بتاعي ايه؟",
            "يعني ايه A+ و B+ و F في نظام التقديرات؟",
            "لو أنا قريب من الفصل وعندي فوق 80% من الساعات، ممكن آخد فرصة أخيرة؟",
        ]
        for prompt in prompts:
            with self.subTest(prompt=prompt):
                self.assertEqual(
                    self.graph._router_node({"question": prompt, "history": []})["route"],
                    "rag",
                )

    def test_graduation_and_grading_questions_route_to_rag(self):
        prompts = [
            "عايز افرق بين نظم تقديرات الكليه و نظام تقديرات المواد دي حاجه و دي حاجه",
            "مقررات النجاح و الرسوب",
            "ازاي المعدل التراقمي بيتحسب",
            "شروط التخرج",
            "What are the graduation requirements?",
            "When does a student receive an academic warning?",
            "What are the conditions for honor graduation?",
            "الطالب يتفصل من الكلية في أنهي حالات؟",
            "Max hours for new students in first semester?",
            "لو رسبت في مقرر وأعدته، الحد الأعلى للدرجة كام؟",
            "إمتى أقدر أسجل مشروع التخرج؟",
        ]
        for prompt in prompts:
            with self.subTest(prompt=prompt):
                self.assertEqual(
                    self.graph._router_node({"question": prompt, "history": []})["route"],
                    "rag",
                )

    def test_semester_withdrawal_question_force_routes_to_rag(self):
        state = {"question": "ما شروط الانسحاب من الفصل الدراسي أو إيقاف القيد؟", "history": []}
        routed = self.graph._router_node(state)
        self.assertEqual(routed["route"], "rag")
        self.assertEqual(routed["route_sub_intent"], "regulation")

    def test_loose_semester_withdrawal_questions_force_route_to_rag(self):
        prompts = [
            "إيقاف القيد",
            "ينفع اسيب الترم؟",
            "عايز انسحب من الفصل",
            "semester withdrawal rules",
        ]
        for prompt in prompts:
            with self.subTest(prompt=prompt):
                self.assertEqual(
                    self.graph._router_node({"question": prompt, "history": []})["route"],
                    "rag",
                )

    def test_category_required_hours_question_force_routes_to_kg(self):
        state = {"question": "How many credit hours are required for Basic Computer Science?", "history": []}
        routed = self.graph._router_node(state)
        self.assertEqual(routed["route"], "kg")
        self.assertEqual(routed["route_sub_intent"], "category_required_hours")

    def test_elective_node_delegates_category_hours_to_kg(self):
        self.graph.kg_service = _TaggedKgService()
        self.graph.elective_service = _TaggedElectiveService()
        self.graph.llm = None
        answer = self.graph._elective_node(
            {"question": "credit hours for specialization courses?", "rewritten_question": ""}
        )
        self.assertEqual(answer["elective_answer"], "KG::credit hours for specialization courses?")

    def test_elective_node_checks_original_question_for_category_hours(self):
        self.graph.kg_service = _TaggedKgService()
        self.graph.elective_service = _TaggedElectiveService()
        self.graph.llm = None
        answer = self.graph._elective_node(
            {
                "question": "credit hours for specialization courses?",
                "rewritten_question": "ما الساعات المطلوبة لدورات التخصص؟",
            }
        )
        self.assertEqual(answer["elective_answer"], "KG::credit hours for specialization courses?")


class CourseMatchingSmokeTests(unittest.TestCase):
    def test_math_two_alias_is_expanded(self):
        self.assertIn(
            "mathematics 2",
            KGService._apply_course_aliases("ايه المطلوب عشان اسجل math 2"),
        )

    def test_ai_applications_alias_maps_to_code(self):
        self.assertIn(
            "ai406",
            KGService._apply_course_aliases("عايز اعرف متطلبات ai applications"),
        )

    def test_mixed_language_after_phrase_detects_reverse_prereq(self):
        self.assertTrue(
            KGService._looks_like_reverse_prereq_query("Machine Learning لما أخلصها بتفتحلي إيه؟")
        )

    def test_mixed_language_before_phrase_detects_prereq(self):
        self.assertTrue(
            KGService._looks_like_prereq_query("Software Engineering إيه متطلبات مادة الـ؟")
        )

    def test_prerequisite_fallback_detects_course_code_question(self):
        self.assertTrue(KGService._looks_like_prereq_query("What do I need before AI301?"))
        self.assertFalse(KGService._looks_like_reverse_prereq_query("What do I need before AI301?"))

    def test_reverse_prerequisite_fallback_detects_opens_question(self):
        self.assertTrue(KGService._looks_like_reverse_prereq_query("What does CS203 open?"))

    def test_arabic_prerequisite_direction_variations_are_distinct(self):
        cases = {
            "Machine Learning بتفتح مواد ايه؟": "courses_unlocked_by_course",
            "لو مخدتش Machine Learning ايه المواد اللي هتقفل؟": "courses_blocked_if_not_completed",
            "لو مسجلتش Machine Learning مش هتفتحلي ايه؟": "courses_blocked_if_not_completed",
            "ايه المادة اللي بتفتح Machine Learning؟": "prerequisites_for_course",
            "ايه المتطلبات السابقة لـ Machine Learning؟": "prerequisites_for_course",
            "لازم آخد ايه قبل Machine Learning؟": "prerequisites_for_course",
        }
        for question, expected in cases.items():
            with self.subTest(question=question):
                self.assertEqual(KGService._classify_prerequisite_direction(question), expected)

    def test_arabic_machine_learning_opens_query_returns_dependents(self):
        answer = _InMemoryPrereqKG().query("Machine Learning بتفتح مواد ايه؟")
        expected_courses = [
            "Natural Language Processing [AI302]",
            "Computer Vision [AI304]",
            "Pattern Recognition [AI305]",
            "Intelligent Algorithms [AI401]",
            "Deep Learning [AI403]",
            "Graduation Project 1 [AI404]",
            "Multi Agent Systems [AI405]",
            "Computational Learning Theory [AI307]",
            "Cognitive Modeling [AI408]",
            "AI for Robotics [AI413]",
        ]
        for course in expected_courses:
            with self.subTest(course=course):
                self.assertIn(course, answer)
        self.assertNotIn("Machine Learning نفسها", answer)
        self.assertNotIn("[AI301] Machine Learning\n- [AI301]", answer)

    def test_arabic_machine_learning_blocked_query_returns_dependents(self):
        answer = _InMemoryPrereqKG().query("لو مخدتش Machine Learning ايه المواد اللي هتقفل؟")
        self.assertIn("Natural Language Processing [AI302]", answer)
        self.assertIn("AI for Robotics [AI413]", answer)
        self.assertNotIn("Machine Learning نفسها", answer)

    def test_arabic_machine_learning_opened_by_query_returns_prerequisites(self):
        answer = _InMemoryPrereqKG().query("ايه المادة اللي بتفتح Machine Learning؟")
        self.assertIn("Introduction to Artificial Intelligence [AI201]", answer)
        self.assertIn("Probability and Statistics 1 [MTH104]", answer)
        self.assertNotIn("Natural Language Processing [AI302]", answer)

    def test_software_engineering_prerequisite_arabic_english_mix(self):
        answer = _InMemoryPrereqKG().query("ايه المطلوب قبل software engineering")
        self.assertIn("علشان تفتح مادة Software Engineering [SW201]", answer)
        self.assertIn("Object Oriented Programming [CS201]", answer)

    def test_software_engineering_unlocks_after_phrase(self):
        answer = _InMemoryPrereqKG().query("بتفتح ايه بعد software engineering")
        self.assertIn("User Interface Design [SW303]", answer)
        self.assertIn("Software Testing & Quality Assurance [SW401]", answer)
        self.assertNotIn("Object Oriented Programming [CS201]", answer)

    def test_software_engineering_unlocks_course_first(self):
        answer = _InMemoryPrereqKG().query("software engineering بتفتح ايه")
        self.assertIn("لو خلصت Software Engineering [SW201]", answer)
        self.assertIn("User Interface Design [SW303]", answer)
        self.assertIn("Software Testing & Quality Assurance [SW401]", answer)

    def test_short_before_followup_uses_last_course_from_history(self):
        history = [
            HumanMessage(content="software engineering بتفتح ايه"),
            AIMessage(content="لو خلصت Software Engineering [SW201]، المواد اللي هتتفتحلك هي:\n- User Interface Design [SW303]\n- Software Testing & Quality Assurance [SW401]"),
        ]
        answer = _InMemoryPrereqKG().query("قبلها بقا؟", history=history)
        self.assertIn("Object Oriented Programming [CS201]", answer)

    def test_oop_prerequisite_alias(self):
        answer = _InMemoryPrereqKG().query("طيب oop متطلباتها ايه")
        self.assertIn("Programming 2 [CS102]", answer)

    def test_oop_unlocks_alias(self):
        answer = _InMemoryPrereqKG().query("oop بتفتح ايه")
        self.assertIn("Software Engineering [SW201]", answer)

    def test_short_after_followup_uses_last_course_from_history(self):
        history = [
            HumanMessage(content="ايه المطلوب قبل software engineering"),
            AIMessage(content="علشان تفتح مادة Software Engineering [SW201]، لازم تكون مخلص:\n- Object Oriented Programming [CS201]"),
        ]
        answer = _InMemoryPrereqKG().query("بعدها ايه؟", history=history)
        self.assertIn("User Interface Design [SW303]", answer)
        self.assertIn("Software Testing & Quality Assurance [SW401]", answer)

    def test_vague_course_followup_without_context_asks_for_course(self):
        answer = _InMemoryPrereqKG().query("قبلها بقا؟", history=[])
        self.assertEqual(answer, "تقصد أنهي مادة؟ اكتب اسم المادة أو كودها زي SW201 أو CS201.")

    def test_category_hours_query_detection(self):
        self.assertTrue(
            KGService._looks_like_category_hours_query(
                "How many credit hours are required for Basic Computer Science?"
            )
        )
        self.assertTrue(
            KGService._looks_like_category_hours_query(
                "متطلبات الجامعة كام ساعة معتمدة؟"
            )
        )
        self.assertTrue(
            KGService._looks_like_category_hours_query(
                "credit hours for specialization courses?"
            )
        )

    def test_required_hours_answer_language(self):
        service = KGService.__new__(KGService)
        en = service._format_required_hours_answer(
            "How many credit hours for Major Requirements?",
            "Major Requirements",
            48,
        )
        ar = service._format_required_hours_answer(
            "متطلبات الجامعة كام ساعة معتمدة؟",
            "University Requirements (Compulsory)",
            10,
        )
        self.assertIn("48 credit hours", en)
        self.assertIn("10 ساعة معتمدة", ar)

    def test_semantic_category_hours_matching_handles_loose_phrasing(self):
        cases = {
            "credit hours for specialization courses?": ("Major Requirements", 48),
            "مواد التخصص محتاجة كام ساعة؟": ("Major Requirements", 48),
            "كام ساعة في اختياري الجامعة؟": ("University Requirements (Elective)", 2),
            "math and science electives need how many hours?": ("Math & Basic Science (Elective)", 3),
            "علوم الحاسب الأساسية كام ساعة؟": ("Basic Computer Science", 39),
            "الاختياري كله كام ساعة معتمدة؟": ("Elective Courses", 21),
        }
        for question, expected in cases.items():
            with self.subTest(question=question):
                self.assertEqual(KGService._semantic_category_hours_match(question), expected)


class RagExtractionSmokeTests(unittest.TestCase):
    def test_repairs_reversed_arabic_title_lines(self):
        service = RAGService.__new__(RAGService)
        text = "يعانطصإ ءاكذ ةيلك\nبلاطلا ليلد\nةــعماجلا\nةيرصملا\nــيسورلا"
        repaired = service._repair_arabic_extraction(text)
        self.assertIn("كلية ذكاء إصطناعي", repaired)
        self.assertIn("دليل الطالب", repaired)
        self.assertIn("الجامعة", repaired)
        self.assertIn("المصرية", repaired)
        self.assertIn("الروسي", repaired)

    def test_clean_excerpts_cover_exam_policy_numbers(self):
        joined = "\n".join(excerpt["text"] for excerpt in REGULATIONS_CLEAN_EXCERPTS)
        self.assertIn("144 ساعة معتمدة", joined)
        self.assertIn("20% لامتحان منتصف الفصل", joined)
        self.assertIn("75% من المحاضرات", joined)
        self.assertIn("60% على الأقل", joined)

    def test_clean_excerpts_cover_dismissal_appeals_and_grade_topics(self):
        joined = "\n".join(excerpt["text"] for excerpt in REGULATIONS_CLEAN_EXCERPTS)
        self.assertIn("أربعة فصول دراسية نظامية متتالية", joined)
        self.assertIn("ستة فصول دراسية نظامية متفرقة", joined)
        self.assertIn("80% على الأقل", joined)
        self.assertIn("أسبوع من تاريخ إعلان النتائج", joined)
        self.assertIn("A+ من 96%", joined)
        self.assertIn("من 3.5 فأكثر ممتاز", joined)
        self.assertIn("إيقاف القيد", joined)
        self.assertIn("أربعة فصول دراسية متتالية", joined)
        self.assertIn("ستة فصول منفصلة", joined)

    def test_split_markdown_pages_includes_intro_and_plain_page_headings(self):
        raw = (
            "# Academic Regulations Clean Source\n\n"
            "### شروط التحويل\n\n"
            "- يجوز تحويل الطلاب إلى الكلية.\n\n"
            "## Page 31\n\n"
            "### عدد الساعات اللازمة للتخرج\n\n"
            "- 144 ساعة معتمدة.\n\n"
            "---\n"
            "## Page 32\n\n"
            "### المدة القصوى للدراسة\n\n"
            "- ثماني سنوات دراسية.\n"
        )

        chunks = RAGService._split_markdown_pages(raw)

        self.assertEqual(chunks[0][0], 0)
        self.assertIn("شروط التحويل", chunks[0][1])
        self.assertEqual(chunks[1][0], 31)
        self.assertIn("144 ساعة معتمدة", chunks[1][1])
        self.assertEqual(chunks[2][0], 32)
        self.assertIn("ثماني سنوات", chunks[2][1])

    def test_keyword_expansion_covers_exam_absence_terms(self):
        terms = set(RAGService._expanded_search_terms("غاب عن الفاينال بعذر مقبول"))
        self.assertIn("غياب", terms)
        self.assertIn("النهايي", terms)
        self.assertIn("مقبول", terms)

    def test_known_regulation_answers_cover_stable_arabic_facts(self):
        service = RAGService.__new__(RAGService)
        checks = {
            "كم ساعة معتمدة يجب اجتيازها للتخرج؟": "144",
            "كام ساعة عشان اتخرج؟": "144",
            "لو انا عايز اتخرج محتاج اخلص كام ساعة؟": "144",
            "كام ساعة معتمدة عشان التخرج؟": "144",
            "مدة الفصل الدراسي النظامي كام أسبوع؟": "17",
            "الترم العادي كام أسبوع؟": "17",
            "الفصل الصيفي مدته كام أسبوع؟": "8",
            "الحد الأقصى للتسجيل في الفصل الصيفي كام ساعة؟": "9",
            "أقل درجة للنجاح في أي مقرر كام؟": "50",
            "نسبة الحضور المطلوبة لدخول الامتحان النهائي كام؟": "75%",
            "لو نسبة غياب الطالب تجاوزت 25% يحصل إيه؟": "25%",
            "متى يحصل الطالب على إنذار أكاديمي لو CGPA أقل من 2؟": "CGPA أقل من 2",
        }
        for question, expected in checks.items():
            with self.subTest(question=question):
                self.assertIn(expected, service._known_regulation_answer(question))

    def test_known_regulation_answers_cover_stable_english_facts(self):
        service = RAGService.__new__(RAGService)
        checks = {
            "How many credit hours to graduate?": "144 credit hours",
            "Graduation credit hours": "144 credit hours",
            "Regular semester duration": "17 weeks",
            "Regular semester how many weeks?": "17 weeks",
            "Summer semester duration": "8 weeks",
            "Max credit hours in the summer semester?": "9 credit hours",
            "What is the minimum passing grade?": "50%",
            "What attendance percentage is required to sit the final exam?": "75%",
            "What is the absence limit?": "25%",
            "When does a student receive an academic warning?": "CGPA is less than 2",
        }
        for question, expected in checks.items():
            with self.subTest(question=question):
                self.assertIn(expected, service._known_regulation_answer(question))

    def test_known_regulation_answer_skips_long_policy_topics(self):
        service = RAGService.__new__(RAGService)
        long_policy_questions = [
            "قسم شؤون الخريجين بيقدم إيه خدمات للخريجين؟",
            "إيه شروط التحويل لكلية الذكاء الاصطناعي؟",
            "إيه شروط القبول في كلية الذكاء الاصطناعي؟",
            "إيه مواصفات خريج كلية الذكاء الاصطناعي؟",
            "ما شروط الانسحاب من الفصل الدراسي أو إيقاف القيد؟",
            "ينفع اسيب الترم؟",
            "ما معنى تقدير غير مكتمل I؟",
            "لو الطالب غاب عن الامتحان النهائي بعذر قهري مقبول يحصل إيه؟",
            "ما شروط مرتبة الشرف؟",
            "الطالب يتفصل من الكلية في أنهي حالات؟",
            "لو عايز أعمل تظلم على نتيجة مادة، عندي مهلة قد ايه؟",
            "إيه مواد الترم الاول سنة تالتة ذكاء اصطناعي؟",
        ]
        for question in long_policy_questions:
            with self.subTest(question=question):
                self.assertEqual("", service._known_regulation_answer(question))

    def test_egyptian_arabic_normalization_rewrites_colloquial_phrasing(self):
        normalized = RAGService._normalize_egyptian_question(
            "لو انا شايل مادة ينفعلي احضر الفاينال الترم ده؟"
        )
        self.assertIn("اذا كان الطالب", normalized)
        self.assertIn("راسب في مقرر", normalized)
        self.assertIn("ادخل الامتحان النهائي", normalized)
        self.assertIn("الفصل الدراسي", normalized)

    def test_retrieval_prompt_marks_student_perspective_questions(self):
        prompt = RAGService._build_retrieval_prompt(
            "لو انا عايز اسحب مادة ينفعلي لحد امتى؟"
        )
        self.assertIn("Normalized retrieval form", prompt)
        self.assertIn("Formal document-style retrieval form", prompt)
        self.assertIn("حتى متى يحق للطالب الانسحاب من مقرر", prompt)
        self.assertIn("Interpret student-related rules as applying to the asking student.", prompt)

    def test_retrieval_prompt_marks_mixed_arabic_english_questions(self):
        prompt = RAGService._build_retrieval_prompt(
            "لو ال CGPA بتاعي من 2 لاقل من 3 اقدر اسجل كام ساعة؟"
        )
        self.assertIn("Language note", prompt)
        self.assertIn("mixes Arabic and English academic wording", prompt)

    def test_formal_retrieval_rewrites_dismissal_and_appeals_questions(self):
        dismissal = RAGService._formalize_for_doc_retrieval(
            "امتى ممكن الكلية تفصل الطالب من الدراسة؟"
        )
        appeals = RAGService._formalize_for_doc_retrieval(
            "لو عايز أعمل تظلم على نتيجة مادة، عندي مهلة قد ايه؟"
        )
        self.assertIn("حالات الفصل من الكلية", dismissal)
        self.assertIn("موعد التظلم", appeals)

    def test_formal_retrieval_rewrites_grade_symbol_and_final_chance_questions(self):
        grades = RAGService._formalize_for_doc_retrieval(
            "يعني ايه A+ و B+ و F في نظام التقديرات؟"
        )
        final_chance = RAGService._formalize_for_doc_retrieval(
            "لو أنا قريب من الفصل وعندي فوق 80% من الساعات، ممكن آخد فرصة أخيرة؟"
        )
        self.assertIn("معنى رموز التقديرات", grades)
        self.assertIn("80% من الساعات اللازمة للتخرج", final_chance)

    def test_policy_wording_normalizes_without_hardcoded_answers(self):
        cases = {
            "عايز اتخرج واخلص كام ساعة": "شروط التخرج",
            "اسحب مادة": "انسحب من مقرر",
            "drop a course": "انسحب من مقرر",
            "اسيب الترم": "الانسحاب الكلي من الفصل الدراسي",
            "stop enrollment": "ايقاف القيد",
            "I grade": "تقدير غير مكتمل",
            "missed final exam": "تغيب عن الامتحان النهائي",
            "حضور الفاينال": "نسبه الحضور لدخول الامتحان النهائي",
            "academic warning": "انذار اكاديمي",
            "honor graduation": "مرتبة الشرف",
            "dismissal": "الفصل من الكلية",
            "appeal": "التظلمات الطلابية",
            "admission requirements": "شروط القبول",
            "transfer policy": "شروط التحويل",
            "graduate affairs": "شؤون الخريجين",
        }
        service = RAGService.__new__(RAGService)
        stable_fact_questions = {"عايز اتخرج واخلص كام ساعة", "حضور الفاينال", "academic warning"}
        for question, expected in cases.items():
            with self.subTest(question=question):
                self.assertIn(expected, RAGService._normalize_egyptian_question(question))
                if question not in stable_fact_questions:
                    self.assertEqual("", service._known_regulation_answer(question))

    def test_policy_wording_formalizes_for_retrieval(self):
        cases = {
            "graduation requirements": "شروط التخرج",
            "withdraw from a course": "الانسحاب من مقرر",
            "semester withdrawal": "الانسحاب الكلي",
            "incomplete": "غير مكتمل I",
            "FA after missed final exam": "FA وAbs وI",
            "attendance requirement": "المواظبة على الحضور",
            "CGPA less than 2 academic warning": "إنذار أكاديمي",
            "honor graduation": "مرتبة الشرف",
            "dismissal": "الفصل من الكلية",
            "grievance": "التظلم",
            "admission requirements": "شروط القبول",
            "transfer policy": "شروط التحويل",
            "graduate affairs": "شؤون الخريجين",
        }
        for question, expected in cases.items():
            with self.subTest(question=question):
                self.assertIn(expected, RAGService._formalize_for_doc_retrieval(question))

    def test_requested_mixed_policy_wording_reaches_retrieval_helpers(self):
        cases = {
            "الدراسة عندنا ماشية بنظام ايه بالظبط؟": ("نظام الدراسة", "الساعات المعتمدة"),
            "اشيل مادة لحد امتى؟": ("انسحب من مقرر", "الانسحاب من مقرر"),
            "اسحب الترم ينفع؟": ("الانسحاب الكلي من الفصل الدراسي", "الانسحاب الكلي"),
            "غبت عن الفاينال بعذر": ("الامتحان النهائي", "عذر"),
            "غبت عن الفاينال من غير عذر": ("دون عذر مقبول", "دون عذر"),
            "لو غيابي عدى 25%": ("تجاوزت نسبة الغياب 25%", "25%"),
            "اعمل تظلم ازاي؟": ("التظلمات الطلابية", "التظلم"),
            "what is academic warning?": ("انذار اكاديمي", "إنذار أكاديمي"),
            "appeal deadline": ("التظلمات الطلابية", "التظلم"),
            "transfer requirements": ("transfer", "60"),
        }
        for question, (normalized_term, formal_term) in cases.items():
            with self.subTest(question=question):
                normalized = RAGService._normalize_egyptian_question(question)
                formal = RAGService._formalize_for_doc_retrieval(question)
                terms = set(RAGService._expanded_search_terms(question))

                self.assertIn(normalized_term, normalized)
                self.assertTrue(
                    formal_term in formal
                    or RAGService._normalize_for_search(formal_term) in terms
                )

    def test_policy_wording_expands_search_terms(self):
        terms = set(RAGService._expanded_search_terms(
            "appeal transfer policy I grade Abs Con CGPA less than 2"
        ))

        for expected in (
            "التظلمات", "التحويل", "معادله", "غير مكتمل", "abs",
            "con", "cgpa", "المعدل التراكمي", "انذار", "اكاديمي",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, terms)


    def test_weak_generic_hosted_answer_triggers_local_fallback(self):
        self.assertTrue(
            RAGService._should_try_local_fallback(
                "لو عايز أعمل تظلم على نتيجة مادة، عندي مهلة قد ايه؟",
                "بالنسبة لتظلم على نتيجة مادة، عادةً المهلة بتكون محددة من قبل الجامعة. يفضل تتأكد من القسم الأكاديمي.",
            )
        )

    def test_explicit_not_found_hosted_answer_triggers_local_fallback(self):
        self.assertTrue(
            RAGService._should_try_local_fallback(
                "إيه شروط التحويل لكلية الذكاء الاصطناعي؟",
                "مش لاقي المعلومة دي في اللائحة.",
            )
        )
        self.assertTrue(
            RAGService._should_try_local_fallback(
                "What are the admission requirements?",
                "I couldn't find this specific regulation in the document.",
            )
        )

    def test_specific_regulation_answer_missing_required_details_triggers_local_fallback(self):
        self.assertTrue(
            RAGService._should_try_local_fallback(
                "مدة الفصل الدراسي النظامي كام أسبوع؟",
                "مدة الفصل الدراسي النظامي موضحة في اللائحة.",
            )
        )
        self.assertTrue(
            RAGService._should_try_local_fallback(
                "When does a student receive an academic warning?",
                "A student may receive an academic warning under the regulation.",
            )
        )

    def test_specific_grounded_answer_does_not_trigger_local_fallback(self):
        self.assertFalse(
            RAGService._should_try_local_fallback(
                "لو عندي عذر واتحسبلي I، لازم أمتحن الفاينال امتى؟",
                "إذا كان لديك عذر قهري مقبول وحصلت على تقدير غير مكتمل (I)، يجب عليك أداء الامتحان النهائي خلال حد أقصى أسبوع من بداية الفصل الدراسي التالي.",
            )
        )

    def test_good_hosted_answer_with_required_details_does_not_trigger_local_fallback(self):
        self.assertFalse(
            RAGService._should_try_local_fallback(
                "مدة الفصل الدراسي النظامي كام أسبوع؟",
                "مدة الفصل الدراسي النظامي 17 أسبوعا متضمنة فترة الامتحانات.",
            )
        )
        self.assertFalse(
            RAGService._should_try_local_fallback(
                "When does a student receive an academic warning?",
                "A student receives an academic warning when CGPA is less than 2.",
            )
        )

    def test_local_fallback_retrieves_clean_intro_admin_sections(self):
        service = RAGService.__new__(RAGService)

        transfer = service._local_regulation_fallback("إيه شروط التحويل لكلية الذكاء الاصطناعي؟")
        admission = service._local_regulation_fallback("What are the admission requirements?")
        graduate_affairs = service._local_regulation_fallback("خدمات شؤون الخريجين")

        self.assertIn("المقدمة", transfer)
        self.assertIn("التحويل", transfer)
        self.assertIn("شروط القبول", admission)
        self.assertIn("إصدار شهادات التخرج", graduate_affairs)

    def test_local_fallback_retrieves_clean_page_regulation_sections(self):
        service = RAGService.__new__(RAGService)

        graduation = service._local_regulation_fallback("كم ساعة معتمدة للتخرج؟")
        withdrawal = service._local_regulation_fallback("اسحب مادة لحد امتى؟")
        warning = service._local_regulation_fallback("متى يحصل الطالب على إنذار أكاديمي لو CGPA أقل من 2؟")
        attendance = service._local_regulation_fallback("نسبة الحضور المطلوبة لدخول الامتحان النهائي كام؟")
        dismissal = service._local_regulation_fallback("الطالب يتفصل من الكلية في أنهي حالات؟")
        study_system = service._local_regulation_fallback("الدراسة عندنا ماشية بنظام ايه بالظبط؟")
        registration_deadline = service._local_regulation_fallback("التسجيل في المواد بيفضل مفتوح لحد امتى؟")
        final_absence = service._local_regulation_fallback("لو غبت عن الفاينال من غير عذر، هاخد ايه؟")

        self.assertIn("144", graduation)
        self.assertIn("الأسبوع التاسع", withdrawal)
        self.assertIn("CGPA", warning)
        self.assertIn("2", warning)
        self.assertIn("75", attendance)
        self.assertIn("إنذار", dismissal)
        self.assertIn("أربعة", dismissal)
        self.assertIn("ستة", dismissal)
        self.assertIn("الساعات المعتمدة", study_system)
        self.assertIn("الأسبوع الثاني", registration_deadline)
        self.assertIn("FA", final_absence)


class MassivePromptRoutingTests(unittest.TestCase):
    def setUp(self):
        self.graph = self._make_graph()

    def _make_graph(self, kg_service=None):
        graph = AdvisorGraph.__new__(AdvisorGraph)
        graph.rag_service = _TaggedRagService()
        graph.kg_service = kg_service or _TaggedKgService()
        graph.mental_service = _TaggedMentalService()
        graph.elective_service = _TaggedElectiveService()
        graph.llm = None
        graph.course_names = [
            "Deep Learning",
            "Data Structures",
            "Introduction to AI",
            "Image Processing",
            "Neural Networks",
            "Artificial Intelligence",
            "Programming",
            "AI301",
            "CS203",
        ]
        graph.graph = graph._build_graph()
        return graph

    def test_kg_questions_route_to_kg(self):
        questions = [
            "What are the prerequisites for Deep Learning?",
            "What courses does Data Structures open for me?",
            "Is Introduction to AI an elective or a core course?",
            "Can I register for AI301 if I failed CS203?",
            "ايه متطلبات تسجيل مادة Image Processing؟",
            "لو نجحت في مادة Data Structures، ايه المواد اللي هتفتحلي الترم الجاي؟",
            "هي مادة Neural Networks دي اختياري ولا اجباري؟",
            "ينفع اسجل AI301 لو انا شايل مادة البرمجة؟",
        ]
        for question in questions:
            with self.subTest(question=question):
                self.assertTrue(self.graph.run(question).startswith("KG::"))

    def test_rag_questions_route_to_rag(self):
        questions = [
            "What is the maximum number of credit hours I can take in a regular semester?",
            "What is the passing grade for graduation projects?",
            "How is my GPA calculated?",
            "Are there any penalties for missing more than 25% of lectures?",
            "What is the procedure if I want to withdraw from a course after the add/drop deadline?",
            "Can I repeat a course to improve my GPA?",
            "الحد الأقصى للتسجيل في الترم العادي كام ساعة معتمدة؟",
            "ازاي بيتم حساب المعدل التراكمي (GPA)؟",
            "لو غبت اكتر من 25% من المحاضرات ايه اللي هيحصل؟",
            "ايه الاجراءات لو عايز اسحب مادة بعد فترة الحذف والاضافة؟",
            "ينفع اعيد مادة عشان احسن المجموع بتاعي؟",
            "لو جبت مقبول في مادة، هل ممكن اعيدها؟",
        ]
        for question in questions:
            with self.subTest(question=question):
                self.assertTrue(self.graph.run(question).startswith("RAG::"))

    def test_elective_questions_route_to_elective_service(self):
        questions = [
            "What are the available elective courses for this semester?",
            "ايه المواد الاختيارية المتاحة ليا اسجلها الترم ده؟",
        ]
        for question in questions:
            with self.subTest(question=question):
                self.assertTrue(self.graph.run(question).startswith("ELECTIVE::"))

    def test_curriculum_semester_questions_route_to_rag(self):
        questions = [
            "What are the second-term courses for a level 3 Artificial Intelligence student?",
            "ايه هي مواد الترم التاني لسنة رابعة قسم ذكاء اصطناعي؟",
        ]
        for question in questions:
            with self.subTest(question=question):
                self.assertTrue(self.graph.run(question).startswith("RAG::"))

    def test_course_followups_do_not_reuse_previous_course_context(self):
        history = [HumanMessage(content="What are the prerequisites for AI301?")]
        self.assertEqual(
            self.graph.run("Is it a core course?", history=history),
            "KG::Is it a core course?",
        )
        self.assertEqual(
            self.graph.run("What does it open?", history=history),
            "KG::What does it open?",
        )
        self.assertEqual(
            self.graph.run("هي المادة دي اجباري؟", history=history),
            "مش لاقي السؤال ده في بيانات المواد أو مستندات اللوايح عندي.",
        )

    def test_unlock_followup_reaches_kg_without_previous_prerequisite_text(self):
        history = [
            HumanMessage(content="What are the prerequisites for AI301?"),
            AIMessage(content="AI301 requires AI201 and MTH104."),
        ]

        self.assertEqual(
            self.graph.run("What does it open?", history=history),
            "KG::What does it open?",
        )

    def test_rag_followups_keep_rag_context(self):
        history = [HumanMessage(content="What is the maximum credit load for the regular semester?")]
        questions = [
            "What about if my GPA is above 3.5?",
            "And for the summer semester?",
            "Is this the same for graduating students?",
            "طيب لو ال GPA بتاعي اعلى من 3.5؟",
            "طيب وبالنسبة للترم الصيفي؟",
            "هل الكلام ده ينطبق على خريجين الترم ده؟",
        ]
        for question in questions:
            with self.subTest(question=question):
                self.assertTrue(self.graph.run(question, history=history).startswith("RAG::"))

    def test_prerequisite_typos_still_route_to_kg(self):
        questions = [
            "What are the prequesits for Deep Learnng?",
            "ايه ال prequesits بتاعة مادة Image Processing؟",
        ]
        for question in questions:
            with self.subTest(question=question):
                self.assertTrue(self.graph.run(question).startswith("KG::"))

    def test_out_of_scope_questions_return_standard_fallback(self):
        self.assertEqual(
            self.graph.run("Who is the dean of the faculty?"),
            "I couldn't find this specific question in our course data or regulation documents.",
        )
        self.assertEqual(
            self.graph.run("مين عميد الكلية؟"),
            "مش لاقي السؤال ده في بيانات المواد أو مستندات اللوايح عندي.",
        )

    def test_unsupported_course_metadata_followup_returns_fallback(self):
        history = [HumanMessage(content="What are the prerequisites for AI301?")]
        self.assertEqual(
            self.graph.run("Who teaches it this semester?", history=history),
            "I couldn't find this specific question in our course data or regulation documents.",
        )
        history = [HumanMessage(content="ايه متطلبات تسجيل مادة Image Processing؟")]
        self.assertEqual(
            self.graph.run("مين الدكتور بتاعها الترم ده؟", history=history),
            "مش لاقي السؤال ده في بيانات المواد أو مستندات اللوايح عندي.",
        )

    def test_unknown_course_not_found_is_converted_to_fallback(self):
        graph = self._make_graph(kg_service=_MissingKgService())
        self.assertEqual(
            graph.run("What are the prerequisites for Quantum Cooking 101?"),
            "I couldn't find this specific question in our course data or regulation documents.",
        )

    def test_kg_unavailable_falls_back_to_rag_for_course_queries(self):
        graph = self._make_graph(kg_service=_UnavailableKgService())
        self.assertTrue(
            graph.run("What are the prerequisites for Deep Learning?").startswith("RAG::")
        )

    def test_kg_unavailable_falls_back_to_rag_for_study_path_queries(self):
        graph = self._make_graph(kg_service=_UnavailableKgService())
        self.assertTrue(
            graph.run("عاوز أعرف مواد الفرقة الثالثة ذكاء اصطناعي").startswith("RAG::")
        )

    def test_semantic_rewritten_question_reaches_rag_service(self):
        graph = self._make_graph()
        graph.router_service = _FakeRouterService(
            RouterDecision(
                route="rag",
                sub_intent="regulation",
                rewritten_question="What is the duration of the summer semester?",
                confidence=0.93,
                entities={"policy_topic": "summer_semester"},
                reasoning="Clear regulation request.",
            )
        )

        self.assertEqual(
            graph.run("هو الترم الصيفي مدتو قد ايه ؟"),
            "RAG::What is the duration of the summer semester?\n\n"
            "Original student question: هو الترم الصيفي مدتو قد ايه ؟\n"
            "Response language requirement: answer in Arabic only.",
        )

    def test_semantic_rewritten_question_reaches_kg_service(self):
        graph = self._make_graph()
        graph.router_service = _FakeRouterService(
            RouterDecision(
                route="kg",
                sub_intent="reverse_prerequisite",
                rewritten_question="What courses does Machine Learning open?",
                confidence=0.92,
                entities={"course": "AI301"},
                reasoning="Clear after-course request.",
            )
        )

        self.assertEqual(
            graph.run("Machine Learning لما أخلصها بتفتحلي إيه؟"),
            "KG::What courses does Machine Learning open?\n\n"
            "Original student question: Machine Learning لما أخلصها بتفتحلي إيه؟\n"
            "Response language requirement: answer in Arabic only.",
        )

    def test_semantic_rewritten_question_reaches_mental_service(self):
        graph = self._make_graph()
        graph.router_service = _FakeRouterService(
            RouterDecision(
                route="mental",
                sub_intent="support",
                rewritten_question="I am anxious about exams and need help starting.",
                confidence=0.95,
                entities={},
                reasoning="Clear support request.",
            )
        )

        self.assertEqual(
            graph.run("انا متوتر جدا من الامتحانات ومش عارف ابدا منين"),
            "MENTAL::I am anxious about exams and need help starting.::None",
        )


class MentalSupportRoutingTests(unittest.TestCase):
    def setUp(self):
        self.graph = AdvisorGraph.__new__(AdvisorGraph)
        self.graph.rag_service = _TaggedRagService()
        self.graph.kg_service = _TaggedKgService()
        self.graph.mental_service = _TaggedMentalService()
        self.graph.elective_service = _TaggedElectiveService()
        self.graph.llm = None
        self.graph.course_names = [
            "Deep Learning",
            "Data Structures",
            "Introduction to AI",
            "Image Processing",
            "Neural Networks",
            "Artificial Intelligence",
            "Programming",
            "AI301",
            "CS203",
        ]
        self.graph.graph = self.graph._build_graph()

    def test_mental_support_questions_route_to_mental_service(self):
        questions = [
            "I am afraid I will fail this semester",
            "I am stressed and need study tips",
            "انا خايف اسقط الترم ده",
            "محتاج نصايح للمذاكرة",
        ]
        for question in questions:
            with self.subTest(question=question):
                self.assertTrue(self.graph.run(question).startswith("MENTAL::"))

    def test_major_selection_questions_route_to_major_guidance(self):
        questions = [
            "Which major should I choose, AI or Cybersecurity?",
            "اختار AI ولا Cyber؟",
        ]
        for question in questions:
            with self.subTest(question=question):
                self.assertTrue(self.graph.run(question).startswith("MAJOR::"))


class MissingOpenAIKeySmokeTests(unittest.TestCase):
    def test_chat_controller_does_not_initialize_graph_for_history(self):
        with patch.dict("os.environ", {}, clear=True):
            with patch("advisor_ai.chat_controller.AdvisorGraph") as graph_cls:
                controller = ChatController()
                self.assertEqual(controller.get_history("student-101", "session-1"), [])
                graph_cls.assert_not_called()

    def test_history_endpoint_returns_empty_history_without_openai_key(self):
        with patch.dict("os.environ", {}, clear=True):
            from advisor_ai import main

            main._chat_controller = None
            client = TestClient(main.app)
            response = client.get(
                "/history",
                params={"student_id": "student-101", "session_id": "session-1"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"student_id": "student-101", "session_id": "session-1", "history": []},
        )


class StudentSessionApiTests(unittest.TestCase):
    def setUp(self):
        self.fake_db = _FakeSupabase()
        patcher = patch("advisor_ai.chat_controller.get_supabase", return_value=self.fake_db)
        self.addCleanup(patcher.stop)
        patcher.start()
        self.controller = ChatController()

    def test_create_session_returns_backend_uuid_for_student(self):
        session = self.controller.create_session("225241")

        UUID(session["session_id"])
        self.assertEqual(session["student_id"], "225241")
        self.assertEqual(session["title"], "New chat")
        self.assertEqual(len(self.fake_db.tables["sessions"]), 1)
        self.assertEqual(self.fake_db.tables["sessions"][0]["student_id"], "225241")

    def test_history_is_scoped_by_student_and_session(self):
        self.controller.create_session("225241", title="First")
        first_session = self.fake_db.tables["sessions"][0]["session_id"]
        self.controller.create_session("225241", title="Second")
        second_session = self.fake_db.tables["sessions"][1]["session_id"]
        self.controller.create_session("999999", title="Other")
        other_student_session = self.fake_db.tables["sessions"][2]["session_id"]

        self.controller._save_message("225241", first_session, "user", "First topic")
        self.controller._save_message("225241", second_session, "user", "Second topic")
        self.controller._save_message("999999", other_student_session, "user", "Other student")

        history = self.controller.get_history("225241", first_session)

        self.assertEqual([message["content"] for message in history], ["First topic"])

    def test_list_sessions_returns_only_student_recents_newest_first(self):
        first = self.controller.create_session("225241", title="First")
        second = self.controller.create_session("225241", title="Second")
        self.controller.create_session("999999", title="Other")

        self.controller._save_message("225241", first["session_id"], "user", "Older message")
        self.controller._save_message("225241", second["session_id"], "user", "Newest message")

        sessions = self.controller.list_sessions("225241")

        self.assertEqual([session["session_id"] for session in sessions], [
            second["session_id"],
            first["session_id"],
        ])
        self.assertEqual(sessions[0]["last_message"], "Newest message")
        self.assertEqual({session["title"] for session in sessions}, {"First", "Second"})

    def test_chat_endpoint_requires_student_id_and_returns_it(self):
        from advisor_ai import main

        main._chat_controller = self.controller
        client = TestClient(main.app)
        created = client.post("/sessions", json={"student_id": "225241"}).json()
        self.controller._graph = _FakeGraph()

        with patch.dict("os.environ", {}, clear=True):
            response = client.post(
                "/chat",
                json={
                    "student_id": "225241",
                    "session_id": created["session_id"],
                    "message": "What are AI electives?",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["student_id"], "225241")
        self.assertEqual(response.json()["session_id"], created["session_id"])

    def test_category_hours_message_bypasses_graph_routing(self):
        session = self.controller.create_session("225241")
        graph = _FakeGraph()
        graph.kg_service = MagicMock()
        graph.kg_service.query.return_value = "- The required credit hours for Major Requirements are 48 credit hours."
        self.controller._graph = graph

        response = self.controller.handle_message(
            "225241",
            session["session_id"],
            "credit hours for specialization courses?",
        )

        self.assertIn("48 credit hours", response)
        graph.kg_service.query.assert_called_once_with("credit hours for specialization courses?")

    def test_chat_history_includes_internal_memory_summary_for_followups(self):
        session = self.controller.create_session("225241")
        self.controller._save_message("225241", session["session_id"], "user", "What are prerequisites for AI301?")
        self.controller._save_message("225241", session["session_id"], "assistant", "You need AI201 before AI301.")
        graph = _CapturingGraph()
        self.controller._graph = graph

        response = self.controller.handle_message(
            "225241",
            session["session_id"],
            "What about it?",
        )

        self.assertEqual(response, "answer")
        history = graph.calls[0]["history"]
        self.assertIsInstance(history[0], SystemMessage)
        self.assertIn("Session memory summary", history[0].content)
        self.assertIn("AI301", history[0].content)
        self.assertIn("Last student question", history[0].content)

    def test_followup_turn_passes_previous_question_and_answer_to_graph(self):
        session = self.controller.create_session("225241")
        self.controller._save_message(
            "225241",
            session["session_id"],
            "user",
            "What are prerequisites for AI301?",
        )
        self.controller._save_message(
            "225241",
            session["session_id"],
            "assistant",
            "AI301 requires AI201 and MTH104.",
        )
        graph = _CapturingGraph()
        self.controller._graph = graph

        response = self.controller.handle_message(
            "225241",
            session["session_id"],
            "What does it open?",
        )

        self.assertEqual(response, "answer")
        self.assertEqual(graph.calls[0]["question"], "What does it open?")
        history = graph.calls[0]["history"]
        self.assertTrue(
            any(
                isinstance(message, HumanMessage)
                and message.content == "What are prerequisites for AI301?"
                for message in history
            )
        )
        self.assertTrue(
            any(
                isinstance(message, AIMessage)
                and message.content == "AI301 requires AI201 and MTH104."
                for message in history
            )
        )

    def test_sessions_endpoint_returns_json_list(self):
        from advisor_ai import main

        main._chat_controller = self.controller
        client = TestClient(main.app)
        first = self.controller.create_session("225241", title="First")
        second = self.controller.create_session("999999", title="Second")

        filtered = client.get("/sessions", params={"student_id": "225241"})
        self.assertEqual(filtered.status_code, 200)
        self.assertIsInstance(filtered.json(), list)
        self.assertEqual(filtered.json()[0]["session_id"], first["session_id"])
        self.assertNotIn(second["session_id"], [session["session_id"] for session in filtered.json()])

        unfiltered = client.get("/sessions")
        self.assertEqual(unfiltered.status_code, 200)
        self.assertEqual(
            {session["session_id"] for session in unfiltered.json()},
            {first["session_id"], second["session_id"]},
        )

    def test_upload_electives_endpoint_accepts_json_list(self):
        from advisor_ai import main

        service = _FakeElectiveService()
        main._elective_service = service
        self.addCleanup(setattr, main, "_elective_service", None)
        client = TestClient(main.app)

        response = client.post(
            "/admin/upload-electives",
            json={"electives": ["AI Ethics", " Cloud Computing ", "", "Computer Vision"]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(service.electives, ["AI Ethics", "Cloud Computing", "Computer Vision"])
        self.assertEqual(response.json()["status"], "success")

    def test_meaningful_message_uses_openai_generated_session_title(self):
        session = self.controller.create_session("225241")
        self.controller._graph = _FakeGraph()
        llm = MagicMock()
        llm.invoke.return_value.content = "Machine Learning Prerequisites"

        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}, clear=True):
            with patch("advisor_ai.chat_controller.ChatOpenAI", return_value=llm):
                self.controller.handle_message(
                    "225241",
                    session["session_id"],
                    "What are the prerequisites for Machine Learning?",
                )

        sessions = self.controller.list_sessions("225241")
        self.assertEqual(sessions[0]["title"], "Machine Learning Prerequisites")
        llm.invoke.assert_called_once()

    def test_greeting_does_not_generate_session_title(self):
        session = self.controller.create_session("225241")

        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}, clear=True):
            with patch("advisor_ai.chat_controller.ChatOpenAI") as llm_cls:
                self.controller.handle_message("225241", session["session_id"], "hi")

        sessions = self.controller.list_sessions("225241")
        self.assertEqual(sessions[0]["title"], "New chat")
        llm_cls.assert_not_called()

    def test_level_only_message_does_not_generate_session_title(self):
        session = self.controller.create_session("225241")

        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}, clear=True):
            with patch("advisor_ai.chat_controller.ChatOpenAI") as llm_cls:
                self.controller.handle_message("225241", session["session_id"], "1")

        sessions = self.controller.list_sessions("225241")
        self.assertEqual(sessions[0]["title"], "New chat")
        llm_cls.assert_not_called()

    def test_custom_title_is_not_overwritten_by_openai_title(self):
        session = self.controller.create_session("225241", title="Custom title")
        self.controller._graph = _FakeGraph()

        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}, clear=True):
            with patch("advisor_ai.chat_controller.ChatOpenAI") as llm_cls:
                self.controller.handle_message(
                    "225241",
                    session["session_id"],
                    "What are the AI electives this term?",
                )

        sessions = self.controller.list_sessions("225241")
        self.assertEqual(sessions[0]["title"], "Custom title")
        llm_cls.assert_not_called()

    def test_openai_title_failure_falls_back_to_message_preview(self):
        session = self.controller.create_session("225241")
        self.controller._graph = _FakeGraph()
        llm = MagicMock()
        llm.invoke.side_effect = RuntimeError("OpenAI unavailable")

        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}, clear=True):
            with patch("advisor_ai.chat_controller.ChatOpenAI", return_value=llm):
                self.controller.handle_message(
                    "225241",
                    session["session_id"],
                    "What are the AI electives this term?",
                )

        sessions = self.controller.list_sessions("225241")
        self.assertEqual(sessions[0]["title"], "What are the AI electives this term?")

    def test_rag_service_reports_missing_openai_key_without_crashing(self):
        with patch.dict("os.environ", {}, clear=True):
            service = RAGService()
            status = service.status()
            response = service.query("graduation")

        self.assertIsNone(service.chain)
        self.assertIn("OPENAI_API_KEY is not configured", response)
        self.assertFalse(status["openai_configured"])

    def test_rag_service_reports_missing_vector_store_without_crashing(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}, clear=True):
            service = RAGService()
            status = service.status()
            response = service.query("graduation")

        self.assertIsNone(service.chain)
        self.assertIn("OPENAI_VECTOR_STORE_ID is not configured", response)
        self.assertTrue(status["openai_configured"])
        self.assertFalse(status["vector_store_configured"])

    def test_rag_service_sends_administrative_topics_to_file_search(self):
        with patch.dict("os.environ", {}, clear=True):
            service = RAGService()

            graduates = service._known_regulation_answer("قسم شؤون الخريجين بيقدم إيه خدمات للخريجين؟")
            transfer = service._known_regulation_answer("إيه شروط التحويل لكلية الذكاء الاصطناعي؟")
            admission = service._known_regulation_answer("إيه شروط القبول في كلية الذكاء الاصطناعي؟")
            graduate_specs = service._known_regulation_answer("إيه مواصفات خريج كلية الذكاء الاصطناعي؟")
            response = service.query("إيه شروط التحويل لكلية الذكاء الاصطناعي؟")

        self.assertEqual("", graduates)
        self.assertEqual("", transfer)
        self.assertEqual("", admission)
        self.assertEqual("", graduate_specs)
        self.assertIn("OPENAI_API_KEY is not configured", response)

    def test_rag_service_uses_openai_file_search(self):
        with patch.dict(
            "os.environ",
            {
                "OPENAI_API_KEY": "sk-test",
                "OPENAI_VECTOR_STORE_ID": "vs_test",
                "OPENAI_LLM_MODEL": "gpt-test",
            },
            clear=True,
        ), patch("advisor_ai.rag_service.OpenAI") as client_cls:
            client = client_cls.return_value
            client.responses.create.return_value.output_text = "144 credit hours."

            service = RAGService()
            answer = service.query("How many credit hours are required?")

        self.assertEqual(answer, "144 credit hours.")
        client.responses.create.assert_called_once()
        kwargs = client.responses.create.call_args.kwargs
        self.assertEqual(kwargs["model"], "gpt-test")
        self.assertEqual(
            kwargs["tools"][0]["vector_store_ids"],
            ["vs_test"],
        )

    def test_rag_service_uses_local_text_when_file_search_misses(self):
        with patch.dict(
            "os.environ",
            {
                "OPENAI_API_KEY": "sk-test",
                "OPENAI_VECTOR_STORE_ID": "vs_test",
            },
            clear=True,
        ), patch("advisor_ai.rag_service.OpenAI") as client_cls:
            client = client_cls.return_value
            client.responses.create.return_value.output_text = (
                "I couldn't find this specific regulation in the document."
            )

            service = RAGService()
            answer = service.query("إيه شروط التحويل لكلية الذكاء الاصطناعي؟")

        self.assertIn("التحويل", answer)

    def test_rag_service_falls_back_to_local_text_on_openai_error(self):
        with patch.dict(
            "os.environ",
            {
                "OPENAI_API_KEY": "sk-test",
                "OPENAI_VECTOR_STORE_ID": "vs_test",
            },
            clear=True,
        ), patch("advisor_ai.rag_service.OpenAI") as client_cls:
            client = client_cls.return_value
            client.responses.create.side_effect = RuntimeError("timeout")

            service = RAGService()
            answer = service.query("ما نسبة الحضور المطلوبة لدخول الامتحان النهائي؟")

        self.assertIn("75", answer)


class KgConfigSmokeTests(unittest.TestCase):
    def test_neo4j_username_fallback(self):
        with patch.dict(
            "os.environ",
            {
                "NEO4J_URI": "bolt://example:7687",
                "NEO4J_USERNAME": "neo4j_user",
                "NEO4J_PASSWORD": "secret",
            },
            clear=True,
        ):
            config = get_neo4j_config()
        self.assertEqual(config["uri"], "bolt://example:7687")
        self.assertEqual(config["user"], "neo4j_user")
        self.assertEqual(config["password"], "secret")


if __name__ == "__main__":
    unittest.main()

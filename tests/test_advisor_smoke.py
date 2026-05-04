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
        self.assertEqual(call["history"], history)

    def test_graduation_credit_question_routes_to_rag(self):
        state = {"question": "How many credit hours are required for graduation?"}
        self.assertEqual(self.graph._router_node(state)["route"], "rag")

    def test_specific_course_question_routes_to_kg(self):
        state = {"question": "What are the prerequisites for Machine Learning?"}
        self.assertEqual(self.graph._router_node(state)["route"], "kg")

    def test_exam_absence_question_routes_to_rag(self):
        state = {"question": "لو حصل ظرف ومحضرتش امتحان الميد ترم اعمل ايه؟"}
        self.assertEqual(self.graph._router_node(state)["route"], "rag")

    def test_short_followup_reuses_previous_course_route(self):
        history = [
            HumanMessage(content="طيب ايه عشان اسجل ماده math 2 ايه المواد الي المفروض اكون خدتها")
        ]
        state = {"question": "اه داه الي محتاج اعرفو", "history": history}
        self.assertEqual(self.graph._router_node(state)["route"], "kg")

    def test_duration_followup_reuses_previous_rag_route(self):
        history = [
            HumanMessage(content="هو الحد الاقصي للتسجيل في الفصل الصيفي كام ساعه")
        ]
        state = {"question": "طيب هو مدتو كام اسبوع", "history": history}
        self.assertEqual(self.graph._router_node(state)["route"], "rag")

    def test_mental_followup_keeps_previous_mental_route(self):
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

        self.assertEqual(routed["route"], "mental")
        self.assertEqual(routed["route_sub_intent"], "contextual_followup")
        self.assertEqual(len(self.graph.router_service.calls), 0)

    def test_contextualizes_vague_duration_followup(self):
        history = [
            HumanMessage(content="هو الحد الاقصي للتسجيل في الفصل الصيفي كام ساعه")
        ]
        contextualized = self.graph._contextualize_followup("طيب هو مدتو كام اسبوع", history)
        self.assertEqual("ما مدة الفصل الصيفي كام أسبوع؟", contextualized)

    def test_summer_alternate_followup_reuses_duration_question(self):
        history = [
            HumanMessage(content="مدة الفصل الدراسي النظامي كام أسبوع؟")
        ]
        state = {"question": "طيب و الصيفي؟", "history": history}
        self.assertEqual(self.graph._router_node(state)["route"], "rag")
        contextualized = self.graph._contextualize_followup("طيب و الصيفي؟", history)
        self.assertEqual("ما مدة الفصل الصيفي كام أسبوع؟", contextualized)

    def test_duration_after_summer_topic_followup_stays_on_summer(self):
        history = [
            HumanMessage(content="مدة الفصل الدراسي النظامي كام أسبوع؟"),
            HumanMessage(content="طيب و الصيفي؟"),
        ]
        contextualized = self.graph._contextualize_followup("لا مدتو كام اسبوع؟", history)
        self.assertEqual("ما مدة الفصل الصيفي كام أسبوع؟", contextualized)

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
            "التسجيل في المقررات يستمر لحد إمتى؟",
            "إيه شرط التسجيل في مقرر؟",
            "هل رأي المرشد الأكاديمي إلزامي؟",
            "الطالب يقدر ينسحب من مقرر لحد إمتى؟",
            "لو الطالب انسحب في الميعاد، هل يعتبر راسب؟",
            "الدرجة النهائية لأي مقرر من كام؟",
            "أقل درجة للنجاح في أي مقرر كام؟",
            "شرط النجاح المرتبط بالامتحان النهائي التحريري إيه؟",
            "نسبة الحضور المطلوبة لدخول الامتحان النهائي كام؟",
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

    def test_keyword_expansion_covers_exam_absence_terms(self):
        terms = set(RAGService._expanded_search_terms("غاب عن الفاينال بعذر مقبول"))
        self.assertIn("غياب", terms)
        self.assertIn("النهايي", terms)
        self.assertIn("مقبول", terms)

    def test_known_regulation_answers_cover_failed_arabic_variants(self):
        service = RAGService.__new__(RAGService)
        checks = {
            "الدراسة في الكلية ماشية بأي نظام؟": "الساعات المعتمدة",
            "مدة الفصل الدراسي النظامي كام أسبوع؟": "17",
            "التسجيل في المقررات يستمر لحد إمتى؟": "الأسبوع الثاني",
            "إيه شرط التسجيل في مقرر؟": "اجتياز متطلباته السابقة",
            "هل رأي المرشد الأكاديمي إلزامي؟": "استشاري",
            "الطالب يقدر ينسحب من مقرر لحد إمتى؟": "الأسبوع التاسع",
            "لو الطالب انسحب في الميعاد، هل يعتبر راسب؟": "W",
            "الدرجة النهائية لأي مقرر من كام؟": "100",
            "أقل درجة للنجاح في أي مقرر كام؟": "50",
            "شرط النجاح المرتبط بالامتحان النهائي التحريري إيه؟": "30%",
            "نسبة الحضور المطلوبة لدخول الامتحان النهائي كام؟": "75%",
            "لو نسبة غياب الطالب تجاوزت 25% يحصل إيه؟": "25%",
            "لو الطالب غاب عن الامتحان النهائي بعذر قهري مقبول يحصل إيه؟": "غير مكتمل",
        }
        for question, expected in checks.items():
            with self.subTest(question=question):
                self.assertIn(expected, service._known_regulation_answer(question))

    def test_known_regulation_answer_covers_semester_withdrawal_rules(self):
        service = RAGService.__new__(RAGService)
        answer = service._known_regulation_answer("ما شروط الانسحاب من الفصل الدراسي أو إيقاف القيد؟")
        self.assertIn("قبل الامتحان بشهر", answer)
        self.assertIn("4 فصول", answer)
        self.assertIn("6 فصول", answer)

    def test_known_regulation_answer_covers_loose_semester_withdrawal_phrase(self):
        service = RAGService.__new__(RAGService)
        answer = service._known_regulation_answer("ينفع اسيب الترم؟")
        self.assertIn("قبل الامتحان بشهر", answer)
        self.assertIn("4 فصول", answer)

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


    def test_weak_generic_hosted_answer_triggers_local_fallback(self):
        self.assertTrue(
            RAGService._should_try_local_fallback(
                "لو عايز أعمل تظلم على نتيجة مادة، عندي مهلة قد ايه؟",
                "بالنسبة لتظلم على نتيجة مادة، عادةً المهلة بتكون محددة من قبل الجامعة. يفضل تتأكد من القسم الأكاديمي.",
            )
        )

    def test_specific_grounded_answer_does_not_trigger_local_fallback(self):
        self.assertFalse(
            RAGService._should_try_local_fallback(
                "لو عندي عذر واتحسبلي I، لازم أمتحن الفاينال امتى؟",
                "إذا كان لديك عذر قهري مقبول وحصلت على تقدير غير مكتمل (I)، يجب عليك أداء الامتحان النهائي خلال حد أقصى أسبوع من بداية الفصل الدراسي التالي.",
            )
        )


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

    def test_course_followups_keep_kg_context(self):
        history = [HumanMessage(content="What are the prerequisites for AI301?")]
        questions = [
            "Is it a core course?",
            "And what does it open?",
            "هي المادة دي اجباري؟",
            "طيب والمادة دي بتفتح ايه؟",
        ]
        for question in questions:
            with self.subTest(question=question):
                self.assertTrue(self.graph.run(question, history=history).startswith("KG::"))

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
            "RAG::What is the duration of the summer semester?",
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
            "KG::What courses does Machine Learning open?",
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

    def test_rag_service_answers_known_administrative_topics_without_openai(self):
        with patch.dict("os.environ", {}, clear=True):
            service = RAGService()

            graduates = service.query("قسم شؤون الخريجين بيقدم إيه خدمات للخريجين؟")
            transfer = service.query("إيه شروط التحويل لكلية الذكاء الاصطناعي؟")
            admission = service.query("إيه شروط القبول في كلية الذكاء الاصطناعي؟")
            graduate_specs = service.query("إيه مواصفات خريج كلية الذكاء الاصطناعي؟")

        self.assertIn("إصدار شهادات التخرج", graduates)
        self.assertIn("CGPA", transfer)
        self.assertIn("Pre-mathematic", admission)
        self.assertIn("تلبية متطلبات أصحاب العمل", graduate_specs)

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
            answer = service.query("كم ساعة للتخرج؟")

        self.assertIn("شروط التخرج", answer)

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

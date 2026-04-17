import unittest
from datetime import datetime, timedelta, timezone
from uuid import UUID
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from langchain_core.messages import HumanMessage

from advisor_ai.chat_controller import ChatController
from advisor_ai.graph import AdvisorGraph
from advisor_ai.kg_service import KGService, get_neo4j_config
from advisor_ai.rag_service import REGULATIONS_CLEAN_EXCERPTS, RAGService


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


class _FakeElectiveService:
    def __init__(self):
        self.electives = []

    def set_electives(self, electives):
        self.electives = electives


class RoutingSmokeTests(unittest.TestCase):
    def setUp(self):
        self.graph = AdvisorGraph.__new__(AdvisorGraph)
        self.graph.course_names = ["Machine Learning", "Graduation Project 1"]

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


class CourseMatchingSmokeTests(unittest.TestCase):
    def test_math_two_alias_is_expanded(self):
        self.assertIn(
            "mathematics 2",
            KGService._apply_course_aliases("ايه المطلوب عشان اسجل math 2"),
        )

    def test_prerequisite_fallback_detects_course_code_question(self):
        self.assertTrue(KGService._looks_like_prereq_query("What do I need before AI301?"))
        self.assertFalse(KGService._looks_like_reverse_prereq_query("What do I need before AI301?"))

    def test_reverse_prerequisite_fallback_detects_opens_question(self):
        self.assertTrue(KGService._looks_like_reverse_prereq_query("What does CS203 open?"))


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

    def test_keyword_expansion_covers_exam_absence_terms(self):
        terms = set(RAGService._expanded_search_terms("غاب عن الفاينال بعذر مقبول"))
        self.assertIn("غياب", terms)
        self.assertIn("النهايي", terms)
        self.assertIn("مقبول", terms)


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

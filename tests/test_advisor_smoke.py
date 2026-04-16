import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from langchain_core.messages import HumanMessage

from advisor_ai.chat_controller import ChatController
from advisor_ai.graph import AdvisorGraph
from advisor_ai.kg_service import KGService, get_neo4j_config
from advisor_ai.rag_service import REGULATIONS_CLEAN_EXCERPTS, RAGService


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
                self.assertEqual(controller.get_history("student-101"), [])
                graph_cls.assert_not_called()

    def test_history_endpoint_returns_empty_history_without_openai_key(self):
        with patch.dict("os.environ", {}, clear=True):
            from advisor_ai import main

            main._chat_controller = None
            client = TestClient(main.app)
            response = client.get("/history", params={"session_id": "student-101"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"session_id": "student-101", "history": []},
        )

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

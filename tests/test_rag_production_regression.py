import unittest

from advisor_ai.rag_service import RAGService
from scripts.run_production_rag_regression_checks import cases, answer_case, hit_any, normalize


class ProductionRagRegressionTests(unittest.TestCase):
    def test_production_regression_cases_retrieve_expected_markers(self):
        service = RAGService.__new__(RAGService)
        failures = []

        for case in cases():
            answer = answer_case(service, case)
            missing_groups = [
                group for group in case.expected_groups
                if not hit_any(answer, group)
            ]
            forbidden_hits = [
                marker for marker in case.forbidden
                if normalize(marker) in normalize(answer)
            ]
            if missing_groups or forbidden_hits:
                failures.append(
                    f"{case.topic}: {case.prompt} "
                    f"missing={missing_groups} forbidden={forbidden_hits} answer={answer}"
                )

        self.assertEqual([], failures)

    def test_production_rag_cases_do_not_include_course_list_ownership(self):
        prompts = " ".join(case.prompt for case in cases()).lower()

        for course_code in ("ai301", "ds307", "cs302"):
            self.assertNotIn(course_code, prompts)


if __name__ == "__main__":
    unittest.main()

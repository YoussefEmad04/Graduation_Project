"""
Run 20 Egyptian-Arabic KG checks against the local KG service.

This script exercises:
- prerequisite questions
- reverse prerequisite questions
- study-path requests
- category questions
- course info lookup
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from advisor_ai.kg_service import KGService


@dataclass
class Case:
    prompt: str
    expected_any: List[str]


def normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي").replace("ة", "ه")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def cases() -> List[Case]:
    return [
        Case("ايه المطلوب عشان اسجل ماده machine learning؟", ["AI201", "Introduction to Artificial Intelligence"]),
        Case("محتاج اخلص ايه قبل ماده algorithms؟", ["CS102", "Structured Programming"]),
        Case("ماده data structures بتتفتح بايه؟", ["CS201", "Object oriented Programming"]),
        Case("ماده CS101 بتفتحلي ايه بعد كده؟", ["CS102", "Structured programming"]),
        Case("لو نجحت في AI301 هتفتحلي ايه؟", ["AI403", "Deep Learning", "AI401"]),
        Case("عايز اعرف معلومات عن ماده deep learning", ["AI403", "Deep Learning"]),
        Case("ايه مواد سنه اولى عامه؟", ["CS101", "MTH101", "IS101"]),
        Case("ايه مواد سنه تالته ذكاء اصطناعي؟", ["AI301", "DS307", "CS302"]),
        Case("ايه مواد سنه رابعه سايبر؟", ["CB401", "CB402", "CB403", "CB404"]),
        Case("قوللي مواد data science سنه تالته", ["DS302", "DS303", "DS304", "AI301"]),
        Case("ايه متطلبات الجامعه الاجباريه؟", ["HM001", "HM002", "HM003"]),
        Case("ايه مواد الرياضه الاختياريه؟", ["MTH201", "MTH202", "MTH203"]),
        Case("ايه مواد ai الاختياريه؟", ["AI307", "AI308", "AI310", "AI311"]),
        Case("ايه مواد cyber الاختياريه؟", ["CB310", "CB311", "CB312", "CB313"]),
        Case("لو انا شايل math 1 مش هعرف افتح ايه؟", ["MTH103", "MTH104"]),
        Case("ماده AI406 محتاجه ايه قبلها؟", ["AI401", "AI304"]),
        Case("graduation project 2 محتاجه ايه؟", ["AI404", "DS406", "CB406", "SW406"]),
        Case("هو كورس human rights ده اجباري ولا ايه؟", ["HM003", "Human Rights"]),
        Case("عايز خطه مواد سنه تانيه", ["CS201", "IS201", "CS205", "AI201"]),
        Case("ماده introduction to ai دي اختياري ولا اجباري؟", ["AI201", "Introduction to Artificial Intelligence"]),
    ]


def run() -> int:
    service = KGService()
    all_cases = cases()
    passed = 0

    for index, case in enumerate(all_cases, start=1):
        answer = service.query(case.prompt)
        normalized_answer = normalize(answer)
        hits = [term for term in case.expected_any if normalize(term) in normalized_answer]
        ok = bool(hits)
        if ok:
            passed += 1

        status = "PASS" if ok else "FAIL"
        print(f"\n[{status}] {index}. {case.prompt}")
        print(f"Expected any: {case.expected_any}")
        print(f"Answer: {answer}")

    print(f"\nSummary: {passed}/{len(all_cases)} passed")
    return 0 if passed == len(all_cases) else 1


if __name__ == "__main__":
    raise SystemExit(run())

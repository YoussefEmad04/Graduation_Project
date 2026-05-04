"""
Run Egyptian-Arabic KG checks focused on:
- before a course: prerequisites
- after a course: what it opens

This script uses the real KG service backed by Neo4j.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from advisor_ai.kg_service import KGService


@dataclass
class Case:
    mode: str
    prompt: str
    expected_any: List[str]


def normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي").replace("ة", "ه")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def cases() -> List[Case]:
    return [
        Case("before", "ايه المواد اللي المفروض اكون خلصتها عشان تفتحلي ماده machine learning؟", ["AI201", "Introduction to Artificial Intelligence"]),
        Case("after", "لما اخلص machine learning بيتفتحلي ايه؟", ["AI403", "AI401", "AI304"]),
        Case("before", "ايه المطلوب قبل algorithms؟", ["CS102", "Structured Programming"]),
        Case("after", "لما اخلص algorithms بيتفتحلي ايه؟", ["not a prerequisite", "ليس متطلب", "is not a prerequisite"]),
        Case("before", "ايه اللي لازم اكون مخلصه قبل data structures؟", ["CS201", "Object Oriented Programming"]),
        Case("after", "ماده data structures بتفتحلي ايه بعد كده؟", ["CS204", "Operating Systems"]),
        Case("before", "عشان اسجل operating systems لازم اكون مخلص ايه؟", ["CS201", "Object Oriented Programming"]),
        Case("after", "لما اخلص operating systems هيتفتحلي ايه؟", ["CS302", "Computer Architecture and Organization"]),
        Case("before", "ايه المتطلبات بتاعة software engineering؟", ["CS201", "Object Oriented Programming"]),
        Case("after", "لما اخلص software engineering بيتفتحلي ايه؟", ["SW303", "User Interface Design"]),
        Case("before", "ايه المطلوب قبل introduction to ai؟", ["MTH102", "Linear Algebra"]),
        Case("after", "لما اخلص introduction to ai بيتفتحلي ايه؟", ["AI301", "AI311"]),
        Case("before", "ايه المواد اللي قبل deep learning؟", ["AI301", "Machine Learning"]),
        Case("after", "بعد deep learning بيتفتحلي ايه؟", ["not a prerequisite", "ليس متطلب", "is not a prerequisite"]),
        Case("before", "عشان اخد AI applications لازم اكون مخلص ايه؟", ["AI401", "AI304"]),
        Case("after", "لما اخلص AI applications بيتفتحلي ايه؟", ["not a prerequisite", "ليس متطلب", "is not a prerequisite"]),
        Case("before", "ايه المطلوب قبل graduation project 2؟", ["AI404", "Graduation Project 1"]),
        Case("after", "لما اخلص graduation project 1 بيتفتحلي ايه؟", ["AI407", "Graduation Project 2"]),
        Case("before", "قبل computer vision لازم اكون مخلص ايه؟", ["AI301", "Machine Learning"]),
        Case("after", "لما اخلص computer vision بيتفتحلي ايه؟", ["AI306", "AI406", "AI310"]),
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
        print(f"\n[{status}] {index}. ({case.mode}) {case.prompt}")
        print(f"Expected any: {case.expected_any}")
        print(f"Answer: {answer}")

    print(f"\nSummary: {passed}/{len(all_cases)} passed")
    return 0 if passed == len(all_cases) else 1


if __name__ == "__main__":
    raise SystemExit(run())

"""
Run 20 Egyptian-Arabic RAG checks against the local RAG service.

This script calls advisor_ai.rag_service.RAGService directly so we can validate:
- Egyptian Arabic phrasing
- student-perspective wording like "لو انا" / "أقدر" / "ينفعلي"
- regulation grounding before deploying to Vercel
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from typing import List

from advisor_ai.rag_service import RAGService


@dataclass
class Case:
    prompt: str
    expected_any: List[str]
    note: str = ""


def normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي").replace("ة", "ه")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def cases() -> List[Case]:
    return [
        Case("لو انا عايز اتخرج، محتاج اخلص كام ساعة معتمدة؟", ["144"]),
        Case("الدراسة عندنا ماشية بنظام ايه بالظبط؟", ["الساعات المعتمدة"]),
        Case("الترم العادي مدته كام اسبوع؟", ["17"]),
        Case("طب والصيفي مدته كام اسبوع؟", ["8"]),
        Case("الصيفي ده اختياري ولا لازم؟", ["اختياري"]),
        Case("ينفعلي اسجل كام ساعة في الصيفي؟", ["9"]),
        Case("لو انا الـ CGPA بتاعي من 2 لاقل من 3، اقدر اسجل كام ساعة؟", ["18"]),
        Case("لو معدلي اقل من 1، مسموحلي بكام ساعة؟", ["12"]),
        Case("التسجيل في المواد بيفضل مفتوح لحد امتى؟", ["الاسبوع الثاني", "نهايه الاسبوع الثاني"]),
        Case("الحذف والاضافة متاحين لحد امتى؟", ["الاسبوع الثالث", "نهايه الاسبوع الثالث"]),
        Case("لو انا عايز اسجل مادة، لازم اكون مخلص ايه قبلها؟", ["اجتياز متطلباته السابقة", "اجتياز متطلباته"]),
        Case("رأي المرشد الاكاديمي لازم امشي بيه ولا استشاري؟", ["استشاري"]),
        Case("اقدر اسحب مادة لحد امتى؟", ["الاسبوع التاسع", "نهايه الاسبوع التاسع"]),
        Case("لو شيلت المادة في المعاد، هاتحسب عليا رسوب؟", ["w", "منسحب"]),
        Case("لو غبت عن الفاينال من غير عذر، هاخد ايه؟", ["fa", "راسب"]),
        Case("لو انا غبت عن الفاينال بعذر قهري، هاخد ايه؟", ["غير مكتمل", "i", "60%"]),
        Case("لازم احضر كام في الميه عشان ادخل الامتحان النهائي؟", ["75%"]),
        Case("لو غيابي زاد عن 25%، ممكن يحصللي ايه؟", ["25%", "حرمان", "انذاره"]),
        Case("ايه شرط النجاح في الامتحان النهائي التحريري؟", ["30%"]),
        Case("ايه مواد الترم الاول سنة تالتة ذكاء اصطناعي؟", ["AI301", "DS307", "CS302"]),
    ]


def run() -> int:
    service = RAGService()
    all_cases = cases()
    passed = 0

    for index, case in enumerate(all_cases, start=1):
        answer = (
            service._known_regulation_answer(case.prompt)
            or service._local_regulation_fallback(case.prompt)
            or "مش لاقي المعلومة دي في اللائحة."
        )
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

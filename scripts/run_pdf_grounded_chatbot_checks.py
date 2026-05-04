"""
Run a grounded regression pass against the deployed chatbot.

Categories:
- 30 RAG questions based on important_pdf/RAG/regulations_extracted.md and question_bank.md
- 30 KG questions based on course/prerequisite/category content from important_pdf/KG/*
- 30 General/Mental questions for greetings, mental support, major selection, electives, and fallback
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional
from uuid import uuid4

import requests


ROOT = Path(__file__).resolve().parents[1]
REPORT_MD = ROOT / "docs" / "pdf_grounded_chatbot_report.md"
REPORT_JSON = ROOT / "docs" / "pdf_grounded_chatbot_report.json"
DEFAULT_BASE_URL = "https://smart-academic-advisor-api.vercel.app"


@dataclass
class Case:
    category: str
    prompt: str
    expected_any: List[str]
    expected_all: Optional[List[str]] = None
    note: str = ""


@dataclass
class Result:
    category: str
    prompt: str
    response: str
    passed: bool
    missing_any: List[str]
    missing_all: List[str]
    note: str
    error: str = ""


def normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي").replace("ة", "ه")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def matches_case(response: str, case: Case) -> tuple[bool, List[str], List[str]]:
    normalized_response = normalize(response)
    any_terms = [term for term in case.expected_any if normalize(term) in normalized_response]
    missing_all = [
        term for term in (case.expected_all or [])
        if normalize(term) not in normalized_response
    ]
    passed = bool(any_terms) and not missing_all
    return passed, [term for term in case.expected_any if term not in any_terms], missing_all


def rag_cases() -> List[Case]:
    return [
        Case("RAG", "كام ساعة معتمدة لازم الطالب يجتازها عشان يتخرج؟", ["144"]),
        Case("RAG", "الدراسة في الكلية ماشية بأي نظام؟", ["الساعات المعتمدة"]),
        Case("RAG", "مدة الفصل الدراسي النظامي كام أسبوع؟", ["17"]),
        Case("RAG", "الفصل الصيفي مدته كام أسبوع؟", ["8"]),
        Case("RAG", "هل الفصل الصيفي إجباري ولا اختياري؟", ["اختياري"]),
        Case("RAG", "الحد الأقصى للتسجيل في الفصل الصيفي كام ساعة؟", ["9"]),
        Case("RAG", "أقل عدد ساعات للتسجيل في فصل خريف أو ربيع كام؟", ["9"]),
        Case("RAG", "الطالب صاحب CGPA أعلى من أو يساوي 3 يقدر يسجل كام ساعة؟", ["21"]),
        Case("RAG", "الطالب صاحب CGPA من 2 إلى أقل من 3 يقدر يسجل كام ساعة؟", ["18"]),
        Case("RAG", "الطالب صاحب CGPA من 1 إلى أقل من 2 يقدر يسجل كام ساعة؟", ["15"]),
        Case("RAG", "الطالب صاحب CGPA أقل من 1 يقدر يسجل كام ساعة؟", ["12"]),
        Case("RAG", "التسجيل في المقررات يستمر لحد إمتى؟", ["نهاية الاسبوع الثاني", "نهايه الاسبوع الثاني", "الاسبوع الثاني"]),
        Case("RAG", "الحذف والإضافة بيكونوا لحد إمتى؟", ["الاسبوع الثالث", "نهاية الاسبوع الثالث"]),
        Case("RAG", "إيه شرط التسجيل في مقرر؟", ["اجتياز متطلباته", "اجتياز المتطلبات"]),
        Case("RAG", "هل رأي المرشد الأكاديمي إلزامي؟", ["استشاري"]),
        Case("RAG", "الطالب يقدر ينسحب من مقرر لحد إمتى؟", ["الاسبوع التاسع", "نهاية الاسبوع التاسع"]),
        Case("RAG", "لو الطالب انسحب في الميعاد، هل يعتبر راسب؟", ["w", "منسحب"]),
        Case("RAG", "لو الطالب انسحب بعد الفترة المحددة دون عذر قهري مقبول، يحصل إيه؟", ["راسب"]),
        Case("RAG", "الدرجة النهائية لأي مقرر من كام؟", ["100"]),
        Case("RAG", "أقل درجة للنجاح في أي مقرر كام؟", ["50"]),
        Case("RAG", "توزيع درجات المقرر النظري إيه؟", ["40%", "20%"], expected_all=["40%", "20%"]),
        Case("RAG", "امتحان الميدترم عليه كام في المقرر النظري؟", ["20%"]),
        Case("RAG", "شرط النجاح المرتبط بالامتحان النهائي التحريري إيه؟", ["30%"]),
        Case("RAG", "توزيع درجات المقرر الذي يحتوي على تطبيقات عملية إيه؟", ["20%"]),
        Case("RAG", "زمن امتحان نهاية الفصل لأي مقرر كام؟", ["ساعتان", "2"]),
        Case("RAG", "نسبة الحضور المطلوبة لدخول الامتحان النهائي كام؟", ["75%"]),
        Case("RAG", "لو نسبة غياب الطالب تجاوزت 25% يحصل إيه؟", ["25%", "حرمانه", "انذاره"]),
        Case("RAG", "لو الطالب غاب عن الامتحان النهائي بدون عذر مقبول يحصل إيه؟", ["fa", "راسب", "abs"]),
        Case("RAG", "لو الطالب غاب عن الامتحان النهائي بعذر قهري مقبول يحصل إيه؟", ["i", "غير مكتمل", "60%"]),
        Case("RAG", "ما معنى تقدير غير مكتمل I؟", ["غير مكتمل", "i"]),
    ]


def kg_cases() -> List[Case]:
    return [
        Case("KG", "مادة Algorithms (CS205) محتاجة إيه قبلها عشان أقدر أسجلها؟", ["CS102", "Structured Programming"]),
        Case("KG", "مادة Data Structures تتفتح بإيه؟", ["CS201", "Object oriented Programming"]),
        Case("KG", "إيه هي سلسلة المواد اللي محتاجها كلها بالكامل عشان أوصل لمشروع التخرج 2 في الـ AI؟", ["Graduation Project", "AI407", "AI404"]),
        Case("KG", "مادة Introduction to Computer Science (CS101) بتفتح إيه في المستويات اللي بعد كده؟", ["CS102", "Structured"]),
        Case("KG", "لو شلت مادة Math 1 لا قدر الله، دي بتقفل إيه؟", ["MTH103", "MTH104", "Mathematics 2", "Probability"]),
        Case("KG", "مادة Human Rights بتفتح إيه؟", ["not a prerequisite", "ليست متطلب", "is not a prerequisite", "مش شرط", "مش متطلب"]),
        Case("KG", "إيه هي المواد المقترحة لسنة تالتة في برنامج الأمن السيبراني؟", ["CB301", "CB302", "CB303", "CB304"]),
        Case("KG", "عاوز خطة الدراسة للفرقة الأولى عامةً.", ["CS101", "MTH101", "Level 1"]),
        Case("KG", "إيه هي متطلبات الجامعة الإجبارية؟", ["HM001", "HM002", "HM003"]),
        Case("KG", "قوللي مواد العلوم الأساسية والاختيارية بتاعت الرياضة؟", ["MTH201", "MTH202", "MTH203"]),
        Case("KG", "كلمني عن مادة الـ ML", ["AI301", "Machine Learning"]),
        Case("KG", "عاوز اعرف معلومات عن مادة رياضه 2", ["MTH103", "Mathematics 2"]),
        Case("KG", "ما متطلب Mathematics 2 [MTH103] في Level 1؟", ["MTH101", "Mathematics 1"]),
        Case("KG", "ما متطلب Probability and Statistics 1 [MTH104]؟", ["MTH101", "Mathematics 1"]),
        Case("KG", "ما متطلب Structured Programming [CS102]؟", ["CS101", "Introduction to Computer Science"]),
        Case("KG", "ما متطلب Signal and System [CS202] في Level 2؟", ["MTH103", "Mathematics 2"]),
        Case("KG", "ما متطلب Algorithms [CS205]؟", ["CS102", "Structured Programming"]),
        Case("KG", "ما متطلب Data Structure [CS203]؟", ["CS201", "Object oriented Programming"]),
        Case("KG", "ما متطلب Introduction to Artificial Intelligence [AI201]؟", ["MTH102", "Linear Algebra"]),
        Case("KG", "اذكر مواد AI program في Level 4 Semester 1.", ["AI401", "AI402", "AI403", "AI404"]),
        Case("KG", "ما متطلب AI406 AI Applications؟", ["AI401", "AI304"]),
        Case("KG", "ما متطلب AI407 Graduation Project 2؟", ["AI404", "Graduation Project 1"]),
        Case("KG", "اذكر بعض مواد AI elective courses.", ["AI307", "AI308", "AI310", "AI311", "STA301", "DS307", "CB310", "CB311"]),
        Case("KG", "اذكر مواد Data Science Level 3 Semester 1.", ["DS304", "DS303", "DS302", "AI301"]),
        Case("KG", "ما متطلب DS306 Advanced Database Systems؟", ["IS201", "Database Systems"]),
        Case("KG", "ما متطلب DS407 Graduation Project 2؟", ["DS406", "Graduation Project 1"]),
        Case("KG", "اذكر مواد Cybersecurity Level 3 Semester 1.", ["CB301", "CB302", "CB303", "CB304"]),
        Case("KG", "ما متطلب CB404 Ethical Hacking؟", ["CB307", "CB308", "Ethical Hacking"]),
        Case("KG", "ما متطلب CB405 Penetration Testing & Vulnerabilities Discovery؟", ["CB307", "Cyber Attacks"]),
        Case("KG", "اذكر بعض Cybersecurity elective courses.", ["CB310", "CB311", "CB312", "CB313"]),
    ]


def general_cases() -> List[Case]:
    return [
        Case("GENERAL", "hi", ["smart academic advisor", "how can i assist"]),
        Case("GENERAL", "hello", ["smart academic advisor", "how can i assist"]),
        Case("GENERAL", "مرحبا", ["smart academic advisor", "how can i assist", "welcome"]),
        Case("GENERAL", "ازيك", ["smart academic advisor", "how can i assist", "welcome"]),
        Case("GENERAL", "I am afraid I will fail this semester", ["study", "professor", "counseling", "schedule"]),
        Case("GENERAL", "I am stressed and need study tips", ["study", "tips", "schedule", "break"]),
        Case("GENERAL", "I feel overwhelmed and burned out", ["break", "professor", "counseling", "study"]),
        Case("GENERAL", "I am worried about my exams", ["study", "exam", "organize", "professor"]),
        Case("GENERAL", "انا خايف اسقط الترم ده", ["متفهم", "الدكتور", "المساعده", "الاستشاره", "جدول", "الاساتذه", "المساعدين", "مساعده", "راجع"]),
        Case("GENERAL", "محتاج نصايح للمذاكرة", ["المذاكره", "نصايح", "تنظيم", "بومودورو"]),
        Case("GENERAL", "حاسس اني مش لاحق ومتوتر", ["تنظم", "مساعده", "الدكتور", "خطوه"]),
        Case("GENERAL", "خايف من الامتحانات ومش عارف ابدا", ["ابدا", "تنظيم", "الدكتور", "مساعده", "جدول", "خطه", "الاساتذه", "المستشارين"]),
        Case("GENERAL", "Which major should I choose, AI or Cybersecurity?", ["AI", "Cybersecurity"], expected_all=["AI", "Cybersecurity"]),
        Case("GENERAL", "I am confused between AI and Cybersecurity", ["AI", "Cybersecurity"], expected_all=["AI", "Cybersecurity"]),
        Case("GENERAL", "Should I choose AI or Cyber?", ["AI", "Cyber"], expected_all=["AI", "Cyber"]),
        Case("GENERAL", "اختار AI ولا Cyber؟", ["AI", "Cyber", "الذكاء", "السيبراني"]),
        Case("GENERAL", "انا محتار بين الذكاء الاصطناعي والامن السيبراني", ["الذكاء", "السيبراني"], expected_all=["الذكاء", "السيبراني"]),
        Case("GENERAL", "ايه الفرق بين AI و Cybersecurity؟", ["AI", "Cybersecurity"], expected_all=["AI", "Cybersecurity"]),
        Case("GENERAL", "What are the available elective courses for this semester?", ["elective", "term", "available", "no electives"]),
        Case("GENERAL", "ايه المواد الاختيارية المتاحة ليا اسجلها الترم ده؟", ["اختياري", "المتاح", "ترم", "elective"]),
        Case("GENERAL", "Who is the dean of the faculty?", ["couldn't find this specific question"]),
        Case("GENERAL", "مين عميد الكلية؟", ["مش لاقي السؤال"]),
        Case("GENERAL", "What is the weather today?", ["couldn't find this specific question"]),
        Case("GENERAL", "مين احسن لاعب كوره في العالم؟", ["مش لاقي السؤال"]),
        Case("GENERAL", "Can you tell me the tuition fees?", ["couldn't find this specific question", "مش لاقي السؤال"]),
        Case("GENERAL", "فين الكافتيريا؟", ["couldn't find this specific question", "مش لاقي السؤال"]),
        Case("GENERAL", "What can you help me with?", ["course", "regulation", "elective", "advisor"]),
        Case("GENERAL", "بتساعد في ايه؟", ["course", "regulation", "elective", "advisor", "materials", "courses"]),
        Case("GENERAL", "new", ["welcome", "smart academic advisor"]),
        Case("GENERAL", "/start", ["welcome", "smart academic advisor"]),
    ]


def all_cases() -> List[Case]:
    return rag_cases() + kg_cases() + general_cases()


def call_chat(base_url: str, prompt: str) -> str:
    payload = {
        "student_id": "pdf-grounded-regression",
        "session_id": str(uuid4()),
        "message": prompt,
    }
    response = requests.post(f"{base_url}/chat", json=payload, timeout=90)
    response.raise_for_status()
    data = response.json()
    return str(data.get("response", ""))


def run_cases(base_url: str, cases: Iterable[Case]) -> List[Result]:
    results: List[Result] = []
    for case in cases:
        try:
            response = call_chat(base_url, case.prompt)
            passed, missing_any, missing_all = matches_case(response, case)
            error = ""
        except Exception as exc:
            response = ""
            passed = False
            missing_any = case.expected_any[:]
            missing_all = (case.expected_all or [])[:]
            error = str(exc)
        results.append(
            Result(
                category=case.category,
                prompt=case.prompt,
                response=response,
                passed=passed,
                missing_any=missing_any,
                missing_all=missing_all,
                note=case.note,
                error=error,
            )
        )
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {case.category}: {case.prompt}", flush=True)
    return results


def write_reports(base_url: str, results: List[Result]) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    summary = {}
    for result in results:
        bucket = summary.setdefault(result.category, {"total": 0, "passed": 0})
        bucket["total"] += 1
        if result.passed:
            bucket["passed"] += 1

    REPORT_JSON.write_text(
        json.dumps(
            {
                "timestamp_utc": timestamp,
                "base_url": base_url,
                "summary": summary,
                "results": [asdict(item) for item in results],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    lines = [
        "# PDF Grounded Chatbot Report",
        "",
        f"- Timestamp UTC: `{timestamp}`",
        f"- Base URL: `{base_url}`",
        "",
        "## Summary",
        "",
    ]
    for category, bucket in summary.items():
        lines.append(f"- `{category}`: {bucket['passed']}/{bucket['total']} passed")

    for category in ("RAG", "KG", "GENERAL"):
        lines.extend(["", f"## {category}", ""])
        for result in [item for item in results if item.category == category]:
            status = "PASS" if result.passed else "FAIL"
            lines.append(f"### {status} - {result.prompt}")
            lines.append("")
            if result.missing_any:
                lines.append(f"- Missing any-match keywords: `{', '.join(result.missing_any)}`")
            if result.missing_all:
                lines.append(f"- Missing required keywords: `{', '.join(result.missing_all)}`")
            if result.error:
                lines.append(f"- Error: `{result.error}`")
            lines.append("- Response:")
            lines.append("")
            lines.append("```text")
            lines.append(result.response.strip())
            lines.append("```")
            lines.append("")

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    base_url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BASE_URL
    cases = all_cases()
    results = run_cases(base_url, cases)
    write_reports(base_url, results)
    failures = [item for item in results if not item.passed]
    print()
    print(f"Wrote {REPORT_MD}")
    print(f"Wrote {REPORT_JSON}")
    print(f"Failures: {len(failures)} / {len(results)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""
Run the full live chatbot checklist against the deployed Vercel API.

The report is intentionally marker-based: a case is a full match when all
expected markers are present, partial when at least one marker is present, and
no match when none are present or the request errors.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List
from uuid import uuid4

import requests


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "https://smart-academic-advisor-api.vercel.app"
REPORT_MD = ROOT / "docs" / "live_full_chatbot_check_2026_05_12.md"
REPORT_JSON = ROOT / "docs" / "live_full_chatbot_check_2026_05_12.json"


@dataclass(frozen=True)
class Case:
    index: str
    part: str
    question: str
    expected: List[str]
    session_group: str = ""


@dataclass
class Result:
    index: str
    part: str
    question: str
    expected: List[str]
    response: str
    present: List[str]
    missing: List[str]
    verdict: str
    error: str = ""


def normalize(text: str) -> str:
    text = text.lower()
    text = (
        text.replace("أ", "ا")
        .replace("إ", "ا")
        .replace("آ", "ا")
        .replace("ى", "ي")
        .replace("ة", "ه")
        .replace("≥", ">=")
        .replace("≤", "<=")
    )
    return re.sub(r"\s+", " ", text).strip()


def marker_present(answer: str, marker: str) -> bool:
    answer_n = normalize(answer)
    marker_n = normalize(marker)
    alternatives = [part.strip() for part in marker_n.split("|")]
    return any(part and part in answer_n for part in alternatives)


def evaluate(answer: str, expected: Iterable[str]) -> tuple[List[str], List[str], str]:
    present = [marker for marker in expected if marker_present(answer, marker)]
    missing = [marker for marker in expected if marker not in present]
    if not missing:
        verdict = "FULL"
    elif present:
        verdict = "PARTIAL"
    else:
        verdict = "NO_MATCH"
    return present, missing, verdict


def cases() -> List[Case]:
    data = [
        ("1", "A1", "What are the prerequisites for Machine Learning?", ["AI201", "MTH104"]),
        ("2", "A1", "What do I need before Deep Learning?", ["AI301"]),
        ("3", "A1", "What are the prereqs for Network Security?", ["CB301", "CB304"]),
        ("4", "A1", "What are the prequesits for AI Applications?", ["AI401", "AI304"]),
        ("5", "A1", "What do I need before Ethical Hacking?", ["CB308"]),
        ("6", "A1", "What are the prerequisites for Database Systems?", ["IS101", "CS102"]),
        ("7", "A1", "What are the prerequisites for Logic Design?", ["ELC101"]),
        ("8", "A1", "What are the prerequisites for Mathematics 3?", ["MTH103"]),
        ("9", "A1", "ما هي متطلبات مقرر التعلم الآلي؟", ["AI201", "MTH104"]),
        ("10", "A1", "ما المطلوب قبل تسجيل مقرر أمن الشبكات؟", ["CB301", "CB304"]),
        ("11", "A1", "ايه المتطلبات بتاعت AI406؟", ["AI401", "AI304"]),
        ("12", "A1", "لازم اكون واخد ايه قبل Machine Learning؟", ["AI201", "MTH104"]),
        ("13", "A1", "ايه المطلوب قبل Deep Learning؟", ["AI301"]),
        ("14", "A1", "Network Security محتاجه ايه قبلها؟", ["CB301", "CB304"]),
        ("15", "A1", "ايه البري ريكويست بتاع AI Applications؟", ["AI401", "AI304"]),
        ("16", "A1", "Logic Design متطلبها ايه؟", ["ELC101"]),
        ("17", "A1", "Software Testing محتاجه انهي مادة قبلها؟", ["SW201"]),
        ("18", "A1", "Algorithms محتاجه ايه قبلها عشان اقدر اسجلها؟", ["CS102"]),
        ("19", "A1", "مادة الـ Data Structures تتفتح بإيه؟", ["CS201"]),
        ("20", "A1", "CS205 محتاجه ايه قبلها؟", ["CS102"]),
        ("21", "A1", "ايه الـ prerequisites بتاعت Computer Vision؟", ["AI301"]),
        ("22", "A1", "Ethical Hacking لازم قبلها ايه؟", ["CB308"]),
        ("23", "A1", "مادة الـ Advanced Cryptography بتتفتح بإيه؟", ["CB303"]),
        ("24", "A1", "CB407 Graduation Project 2 محتاج ايه؟", ["CB406"]),
        ("25", "A2", "After I finish AI301, what courses does it unlock?", ["AI302", "AI304", "AI403"]),
        ("26", "A2", "What future courses open after CS201?", ["CS203", "CS204", "SW201"]),
        ("27", "A2", "Which courses does Cryptography unlock?", ["CB403", "CB311", "CB410"]),
        ("28", "A2", "What does MTH101 open later?", ["MTH103", "MTH104"]),
        ("29", "A2", "What does Software Engineering unlock?", ["SW303", "SW401"]),
        ("30", "A2", "If I complete CB305, what does it unlock?", ["CB308", "CB314", "CB408"]),
        ("31", "A2", "What courses require ELC201?", ["CB309"]),
        ("32", "A2", "After Deep Learning, what can I take?", ["AI410"]),
        ("33", "A2", "ما المقررات التي يفتحها مقرر CS101؟", ["CS102"]),
        ("34", "A2", "ما الذي يفتحه مقرر هندسة البرمجيات؟", ["SW303", "SW401"]),
        ("35", "A2", "لو خلصت AI301 هتفتحلي مواد ايه؟", ["AI302", "AI304", "AI403"]),
        ("36", "A2", "CS201 بتفتحلي ايه بعد كده؟", ["CS203", "CS204", "SW201"]),
        ("37", "A2", "Cryptography بتفتح مواد ايه؟", ["CB403", "CB311", "CB410"]),
        ("38", "A2", "MTH101 بتفتحلي ايه؟", ["MTH103", "MTH104"]),
        ("39", "A2", "AI302 بتفتح ايه بعد كده؟", ["AI303", "AI308", "AI411"]),
        ("40", "A2", "لو خلصت CB305 هيفتحلي ايه؟", ["CB308", "CB314", "CB408"]),
        ("41", "A2", "Software Engineering بتفتح ايه؟", ["SW303", "SW401"]),
        ("42", "A2", "بعد Deep Learning اقدر اخد ايه؟", ["AI410"]),
        ("43", "A2", "مادة الـ Machine Learning بتفتح ايه؟", ["AI302", "AI304", "AI403"]),
        ("44", "A2", "لو خلصت CB304، ايه الـ courses اللي بتتفتح؟", ["CB305", "CB306", "CB307"]),
        ("45", "A2", "CS102 بتفتح ايه من courses؟", ["CS201", "CS205", "IS201"]),
        ("46", "A2", "ELC201 بتفتح اي مواد؟", ["CB309"]),
        ("47", "A2", "مادة الـ Math 1 بتفتح إيه؟", ["MTH103", "MTH104"]),
        ("48", "A2", "لو بسنت خلصت CB303 هيفتحلها ايه؟", ["CB403", "CB311", "CB410"]),
        ("49", "A3", "If I don't take Machine Learning, what courses will be blocked?", ["AI302", "AI304", "AI403"]),
        ("50", "A3", "If I don't complete CB304, what stays locked?", ["CB305", "CB306", "CB307"]),
        ("51", "A3", "لو مخدتش Machine Learning ايه المواد اللي هتقفل؟", ["AI302", "AI304", "AI403"]),
        ("52", "A3", "لو مسجلتش CB304 مش هتفتحلي ايه؟", ["CB305", "CB306", "CB307"]),
        ("53", "A3", "لو مخدتش CS102 هيتقفل عليا ايه؟", ["CS201", "CS205", "IS201"]),
        ("54", "A3", "لو مخدتش مادة الـ Math 1 دي بتقفل ايه؟", ["MTH103", "MTH104"]),
        ("55", "A4", "What courses should I take in Level 1?", ["CS101", "CS102", "MTH101"]),
        ("56", "A4", "Show me the Level 3 Cybersecurity study path.", ["CB301", "CB303", "CB304"]),
        ("57", "A4", "What courses are in the fourth year for AI?", ["AI401", "AI403", "AI404"]),
        ("58", "A4", "ما هي المقررات المقترحة في المستوى الثالث لبرنامج الأمن السيبراني؟", ["CB301", "CB303", "CB304"]),
        ("59", "A4", "ايه المواد في الفرقه الاولي؟", ["CS101", "CS102", "MTH101"]),
        ("60", "A4", "عاوز خطة الدراسة للفرقة الأولى عامةً", ["CS101", "CS102"]),
        ("61", "A4", "ايه الـ study plan بتاعت Level 3 في الـ Cybersecurity؟", ["CB301", "CB303", "CB304"]),
        ("62", "A4", "عايز اعرف مواد السنه الرابعة في AI", ["AI401", "AI403", "AI404"]),
        ("63", "A5", "Give me information about CS201.", ["Object Oriented Programming", "credit hours|ساعات"]),
        ("64", "A5", "What level is Network Security offered at?", ["CB305", "Level 3|المستوى 3"]),
        ("65", "A5", "معلومات عن ماده CS201 ايه؟", ["Object Oriented Programming"]),
        ("66", "A5", "كام ساعة معتمدة في مادة AI301?", ["3"]),
        ("67", "A5", "كلمني عن مادة الـ ML", ["Machine Learning", "AI301"]),
        ("68", "A5", "عاوز اعرف معلومات عن مادة \"رياضه 2\"", ["Mathematics 2", "MTH103"]),
        ("69", "A5", "معلومات عن مادة الـ OOP", ["CS201", "Object Oriented Programming"]),
        ("70", "A6", "List the Basic Computer Science courses.", ["CS101", "CS102", "MTH101"]),
        ("71", "A6", "What are the AI Major Electives?", ["AI", "elective|اختيار"]),
        ("72", "A6", "How many credit hours for Basic Computer Science?", ["39"]),
        ("73", "A6", "How many hours for University Requirements (Compulsory)?", ["10"]),
        ("74", "A6", "How many credit hours for Major Requirements?", ["48"]),
        ("75", "A6", "What are the Math Electives?", ["MTH", "elective|اختيار"]),
        ("76", "A6", "ما هي متطلبات الجامعة الإجبارية؟", ["HM001", "HM002"]),
        ("77", "A6", "كام ساعة معتمدة في علوم الحاسب الاساسيه؟", ["39"]),
        ("78", "A6", "كام ساعة في متطلبات الجامعه الاجباريه؟", ["10"]),
        ("79", "A6", "مواد AI الاختياريه ايه؟", ["AI", "اختيار|elective"]),
        ("80", "A6", "ايه هي الـ university requirements الاجبارية؟", ["HM001", "HM002"]),
        ("81", "A6", "قوللي مواد الـ Math Electives", ["MTH", "اختيار|elective"]),
        ("82", "B1", "How many credit hours does a student need to graduate?", ["144"]),
        ("83", "B1", "How long is a regular semester?", ["17", "week|اسبوع"]),
        ("84", "B1", "Is the summer semester mandatory?", ["optional|اختياري"]),
        ("85", "B1", "Max credit hours in the summer semester?", ["9"]),
        ("86", "B1", "كم ساعة معتمدة يجب اجتيازها للتخرج؟", ["144"]),
        ("87", "B1", "ما مدة الفصل الدراسي الصيفي؟", ["8", "اسابيع|weeks"]),
        ("88", "B1", "كام ساعة معتمدة لازم الطالب يجتازها عشان يتخرج؟", ["144"]),
        ("89", "B1", "الدراسة في الكلية ماشية بأي نظام؟", ["الساعات المعتمده|credit hour"]),
        ("90", "B1", "مدة الفصل الدراسي النظامي كام أسبوع؟", ["17"]),
        ("91", "B1", "هل الفصل الصيفي إجباري؟", ["اختياري|optional"]),
        ("92", "B1", "كام الـ credit hours اللازمة للتخرج؟", ["144"]),
        ("93", "B1", "الـ summer semester إجباري ولا اختياري؟", ["اختياري|optional"]),
        ("94", "B2", "Until when can a student register for courses?", ["week 2|second week|الاسبوع الثاني"]),
        ("95", "B2", "Until when can a student withdraw from a course?", ["week 9|ninth week|الاسبوع التاسع"]),
        ("96", "B2", "What grade does a student get for timely withdrawal?", ["W"]),
        ("97", "B2", "حتى متى يمكن للطالب الانسحاب من مقرر؟", ["الاسبوع التاسع|نهايه الاسبوع التاسع"]),
        ("98", "B2", "التسجيل في المقررات يستمر لحد إمتى؟", ["الاسبوع الثاني|نهايه الاسبوع الثاني"]),
        ("99", "B2", "الطالب يقدر ينسحب من مقرر لحد إمتى؟", ["الاسبوع التاسع|نهايه الاسبوع التاسع"]),
        ("100", "B2", "لو الطالب انسحب في الميعاد، هل يعتبر راسب؟", ["لا", "W"]),
        ("101", "B2", "الحذف والإضافة بيكونوا لحد إمتى؟", ["الاسبوع الثالث|نهايه الاسبوع الثالث"]),
        ("102", "B2", "الـ withdrawal لازم يكون قبل إمتى؟", ["التاسع|week 9|ninth"]),
        ("103", "B2", "لو الطالب انسحب بعد الـ deadline بدون عذر يحصل ايه؟", ["راسب|fail"]),
        ("104", "B3", "What is the minimum passing grade in any course?", ["50"]),
        ("105", "B3", "How is the grade distributed for a theoretical course?", ["40%", "20%", "coursework|اعمال"]),
        ("106", "B3", "What is the minimum required from the final exam to pass?", ["30%"]),
        ("107", "B3", "ما توزيع درجات المقرر النظري؟", ["40%", "20%", "اعمال|coursework"]),
        ("108", "B3", "أقل درجة للنجاح في أي مقرر كام؟", ["50"]),
        ("109", "B3", "توزيع درجات المقرر النظري إيه؟", ["40%", "20%"]),
        ("110", "B3", "امتحان الميدترم عليه كام في المقرر النظري؟", ["20%"]),
        ("111", "B3", "شرط النجاح في الامتحان النهائي التحريري إيه؟", ["30%"]),
        ("112", "B3", "ايه الـ minimum للنجاح في أي مقرر؟", ["50"]),
        ("113", "B3", "توزيع الدرجات في الـ theoretical course عامل إزاي؟", ["40%", "20%", "coursework|اعمال"]),
        ("114", "B4", "What attendance percentage is required to sit the final exam?", ["75%"]),
        ("115", "B4", "What happens if a student misses the final with an excuse?", ["I", "Incomplete|غير مكتمل"]),
        ("116", "B4", "نسبة الحضور المطلوبة لدخول الامتحان النهائي كام؟", ["75%"]),
        ("117", "B4", "لو الطالب غاب عن الامتحان النهائي بدون عذر يحصل إيه؟", ["FA|Abs|راسب"]),
        ("118", "B4", "ما معنى تقدير غير مكتمل I؟", ["عذر|excuse", "60%"]),
        ("119", "B4", "لو الطالب غاب عن الـ final بعذر مقبول يحصل على إيه؟", ["I", "Incomplete|غير مكتمل"]),
        ("120", "B5", "What are the graduation requirements?", ["144", "CGPA", "2"]),
        ("121", "B5", "When does a student receive an academic warning?", ["CGPA", "2"]),
        ("122", "B5", "What are the conditions for honor graduation?", ["3", "failure|رسوب", "4"]),
        ("123", "B5", "ما شروط الحصول على مرتبة الشرف؟", ["3", "رسوب|fail"]),
        ("124", "B5", "شروط التخرج الأساسية إيه؟", ["144", "CGPA", "2"]),
        ("125", "B5", "الطالب بياخد إنذار أكاديمي إمتى؟", ["CGPA", "2"]),
        ("126", "B5", "الطالب يتفصل من الكلية في أنهي حالات؟", ["4", "6"]),
        ("127", "B5", "شروط مرتبة الشرف إيه؟", ["3", "4", "رسوب|failure"]),
        ("128", "B5", "الطالب بياخد الـ academic warning إمتى؟", ["CGPA", "2"]),
        ("129", "B5", "الـ dismissal conditions إيه؟", ["4", "6"]),
        ("130", "B5", "ايه شروط الـ honor degree؟", ["3", "failure|رسوب", "4"]),
        ("131", "C", "What are the prerequisites for XXXX999?", ["could not find|مش لاقي|not find"]),
        ("132", "C", "مادة Human Rights بتفتح ايه؟", ["not a prerequisite|ليست متطلب|مش متطلب"]),
        ("133", "C", "Tell me about OOP", ["CS201", "Object Oriented Programming"]),
        ("134", "C", "prerequisites for software testing", ["SW201"]),
        ("135", "C", "قبلها ايه؟", ["تقصد|which course|انهي ماده"]),
        ("136", "C", "What is the weather today?", ["academic|course|regulation|مش لاقي|couldn't find|advisor"]),
        ("137", "C", "الطالب صاحب CGPA أعلى من 3 يسجل كام ساعة؟", ["21"]),
        ("138", "C", "Max hours for new students in first semester?", ["18"]),
        ("139", "C", "لو رسبت في مقرر وأعدته، الحد الأعلى للدرجة كام؟", ["83", "B"]),
        ("140", "C", "إمتى أقدر أسجل مشروع التخرج؟", ["70%|70"]),
    ]
    result = [Case(*item) for item in data]
    followups = [
        Case("A7.1.1", "A7", "What are the prerequisites for Machine Learning?", ["AI201", "MTH104"], "a7-1"),
        Case("A7.1.2", "A7", "What does it unlock?", ["AI302", "AI304", "AI403"], "a7-1"),
        Case("A7.2.1", "A7", "ايه متطلبات AI301؟", ["AI201", "MTH104"], "a7-2"),
        Case("A7.2.2", "A7", "طيب بعدها بتفتح ايه؟", ["AI302", "AI304", "AI403"], "a7-2"),
        Case("A7.3.1", "A7", "ايه هي مادة Data Structures؟", ["CS203"], "a7-3"),
        Case("A7.3.2", "A7", "طيب دي بتفتح ايه؟", ["CS204"], "a7-3"),
        Case("A7.4.1", "A7", "ايه المطلوب عشان اسجل Math 2؟", ["MTH101"], "a7-4"),
        Case("A7.4.2", "A7", "اه ده اللي محتاج اعرفه", ["MTH101"], "a7-4"),
        Case("A7.5.1", "A7", "ايه متطلبات CS101؟", ["no prerequisites|مفيش|لا يوجد"], "a7-5"),
        Case("A7.5.2", "A7", "و مادة CS102؟", ["CS101"], "a7-5"),
    ]
    return result[:81] + followups + result[81:]


def call_chat(base_url: str, student_id: str, session_id: str, message: str) -> str:
    response = requests.post(
        f"{base_url.rstrip('/')}/chat",
        json={"student_id": student_id, "session_id": session_id, "message": message},
        timeout=90,
    )
    response.raise_for_status()
    return str(response.json().get("response", ""))


def run(base_url: str) -> List[Result]:
    student_id = f"codex-live-full-{int(time.time())}"
    sessions: dict[str, str] = {}
    results: List[Result] = []
    for case in cases():
        session_key = case.session_group or case.index
        session_id = sessions.setdefault(session_key, f"{session_key}-{uuid4()}")
        try:
            answer = call_chat(base_url, student_id, session_id, case.question)
            present, missing, verdict = evaluate(answer, case.expected)
            error = ""
        except Exception as exc:
            answer = ""
            present = []
            missing = case.expected[:]
            verdict = "ERROR"
            error = str(exc)
        results.append(
            Result(
                index=case.index,
                part=case.part,
                question=case.question,
                expected=case.expected,
                response=answer,
                present=present,
                missing=missing,
                verdict=verdict,
                error=error,
            )
        )
        print(f"{case.index:>6} {case.part:<3} {verdict}", flush=True)
        time.sleep(0.15)
    return results


def write_reports(base_url: str, results: List[Result]) -> None:
    counts = {name: sum(1 for item in results if item.verdict == name) for name in ["FULL", "PARTIAL", "NO_MATCH", "ERROR"]}
    payload = {
        "base_url": base_url,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counts": counts,
        "total": len(results),
        "results": [asdict(item) for item in results],
    }
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Live Full Chatbot Check",
        "",
        f"- Target: `{base_url}`",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Total: {len(results)}",
        f"- Full: {counts['FULL']}",
        f"- Partial: {counts['PARTIAL']}",
        f"- No match: {counts['NO_MATCH']}",
        f"- Error: {counts['ERROR']}",
        "",
        "## Summary",
        "",
        "| # | Part | Verdict | Missing | Question |",
        "|---:|---|---|---|---|",
    ]
    for item in results:
        missing = ", ".join(item.missing) if item.missing else "-"
        question = item.question.replace("|", "\\|")
        lines.append(f"| {item.index} | {item.part} | {item.verdict} | {missing} | {question} |")

    lines.extend(["", "## Details", ""])
    for item in results:
        lines.extend(
            [
                f"### {item.index}. {item.part} - {item.verdict}",
                "",
                f"**Question:** {item.question}",
                "",
                f"**Expected markers:** {', '.join(item.expected)}",
                "",
                f"**Present:** {', '.join(item.present) if item.present else '-'}",
                "",
                f"**Missing:** {', '.join(item.missing) if item.missing else '-'}",
                "",
                "**Live answer:**",
                "",
                "```text",
                item.response.strip(),
                "```",
                "",
            ]
        )
        if item.error:
            lines.extend(["**Error:**", "", f"```text\n{item.error}\n```", ""])
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    base_url = DEFAULT_BASE_URL
    results = run(base_url)
    write_reports(base_url, results)
    counts = {name: sum(1 for item in results if item.verdict == name) for name in ["FULL", "PARTIAL", "NO_MATCH", "ERROR"]}
    print(json.dumps({"total": len(results), **counts}, ensure_ascii=False))
    print(f"Markdown report: {REPORT_MD}")
    print(f"JSON report: {REPORT_JSON}")
    return 0 if counts["NO_MATCH"] == 0 and counts["ERROR"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

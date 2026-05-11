"""
Run production KG prerequisite/reverse-prerequisite checks through the public API.

This intentionally targets the Vercel production URL, not local services.
It writes a Markdown report with every prompt, response, and marker-based verdict.
"""

from __future__ import annotations

import json
import re
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


PRODUCTION_URL = "https://smart-academic-advisor-api.vercel.app/chat"
REPORT_PATH = Path("docs/production_kg_prereq_checks_2026_05_11.md")


@dataclass(frozen=True)
class Case:
    language: str
    question: str
    expected_all: List[str]


def normalize(text: str) -> str:
    text = text.lower()
    text = (
        text.replace("أ", "ا")
        .replace("إ", "ا")
        .replace("آ", "ا")
        .replace("ى", "ي")
        .replace("ة", "ه")
    )
    return re.sub(r"\s+", " ", text).strip()


def cases() -> List[Case]:
    english = [
        Case("English", "What are the prerequisites for AI406?", ["AI401", "AI304"]),
        Case("English", "After I finish AI301, what courses does it unlock?", ["AI302", "AI304", "AI403"]),
        Case("English", "What do I need before Machine Learning?", ["AI201", "MTH104"]),
        Case("English", "What future courses open after CS201?", ["CS203", "CS204", "SW201"]),
        Case("English", "What are the prerequisites for Deep Learning?", ["AI301"]),
        Case("English", "What can I take after CB304?", ["CB305", "CB306", "CB307"]),
        Case("English", "What are the prerequisites for Network Security?", ["CB301", "CB304"]),
        Case("English", "Which courses does Cryptography unlock?", ["CB403", "CB311", "CB410"]),
        Case("English", "What are the prerequisites for AI407?", ["AI404"]),
        Case("English", "What does MTH101 open later?", ["MTH103", "MTH104"]),
        Case("English", "What are the prerequisites for Mathematics 3?", ["MTH103"]),
        Case("English", "After CS102, which courses become available?", ["CS201", "CS205", "IS201"]),
        Case("English", "What are the prerequisites for Database Systems?", ["IS101", "CS102"]),
        Case("English", "What courses come after AI302?", ["AI303", "AI308", "AI411"]),
        Case("English", "What are the prerequisites for Computer Vision?", ["AI301"]),
        Case("English", "If I complete CB305, what does it unlock?", ["CB308", "CB314", "CB408"]),
        Case("English", "What are the prerequisites for Ethical Hacking?", ["CB308"]),
        Case("English", "What courses require ELC201?", ["CB309"]),
        Case("English", "What are the prerequisites for Logic Design?", ["ELC101"]),
        Case("English", "What does Software Engineering unlock?", ["SW303", "SW401"]),
        Case("English", "What are the prerequisites for Software Testing and Quality Assurance?", ["SW201"]),
        Case("English", "After Deep Learning, what can I take?", ["AI410"]),
        Case("English", "What are the prequesits for AI Applications?", ["AI401", "AI304"]),
        Case("English", "What comes after Graduation Project 1 in AI?", ["AI407"]),
        Case("English", "What are the prerequisites for Advanced Cryptography?", ["CB303"]),
    ]
    egyptian_arabic = [
        Case("Egyptian Arabic", "ايه المتطلبات بتاعت AI406؟", ["AI401", "AI304"]),
        Case("Egyptian Arabic", "لو خلصت AI301 هتفتحلي مواد ايه؟", ["AI302", "AI304", "AI403"]),
        Case("Egyptian Arabic", "لازم اكون واخد ايه قبل Machine Learning؟", ["AI201", "MTH104"]),
        Case("Egyptian Arabic", "CS201 بتفتحلي ايه بعد كده؟", ["CS203", "CS204", "SW201"]),
        Case("Egyptian Arabic", "ايه المطلوب قبل Deep Learning؟", ["AI301"]),
        Case("Egyptian Arabic", "بعد ما اخلص CB304 اقدر اخد ايه؟", ["CB305", "CB306", "CB307"]),
        Case("Egyptian Arabic", "Network Security محتاجه ايه قبلها؟", ["CB301", "CB304"]),
        Case("Egyptian Arabic", "Cryptography بتفتح مواد ايه؟", ["CB403", "CB311", "CB410"]),
        Case("Egyptian Arabic", "ايه متطلبات AI407؟", ["AI404"]),
        Case("Egyptian Arabic", "MTH101 بتفتحلي ايه؟", ["MTH103", "MTH104"]),
        Case("Egyptian Arabic", "Mathematics 3 محتاجه ايه؟", ["MTH103"]),
        Case("Egyptian Arabic", "بعد CS102 ايه المواد اللي بتتفتح؟", ["CS201", "CS205", "IS201"]),
        Case("Egyptian Arabic", "Database Systems لازم قبلها ايه؟", ["IS101", "CS102"]),
        Case("Egyptian Arabic", "AI302 بتفتح ايه بعد كده؟", ["AI303", "AI308", "AI411"]),
        Case("Egyptian Arabic", "Computer Vision متطلباتها ايه؟", ["AI301"]),
        Case("Egyptian Arabic", "لو خلصت CB305 هيفتحلي ايه؟", ["CB308", "CB314", "CB408"]),
        Case("Egyptian Arabic", "Ethical Hacking محتاجه ايه قبلها؟", ["CB308"]),
        Case("Egyptian Arabic", "ELC201 بتفتح اي مواد؟", ["CB309"]),
        Case("Egyptian Arabic", "Logic Design متطلبها ايه؟", ["ELC101"]),
        Case("Egyptian Arabic", "Software Engineering بتفتح ايه؟", ["SW303", "SW401"]),
        Case("Egyptian Arabic", "Software Testing محتاجه انهي مادة قبلها؟", ["SW201"]),
        Case("Egyptian Arabic", "بعد Deep Learning اقدر اخد ايه؟", ["AI410"]),
        Case("Egyptian Arabic", "ايه البري ريكويست بتاع AI Applications؟", ["AI401", "AI304"]),
        Case("Egyptian Arabic", "Graduation Project 1 في AI بيفتح ايه؟", ["AI407"]),
        Case("Egyptian Arabic", "Advanced Cryptography محتاجه ايه؟", ["CB303"]),
    ]
    return english + egyptian_arabic


def post_chat(case: Case, index: int) -> str:
    payload = {
        "student_id": "codex-production-kg-check",
        "session_id": f"prod-kg-prereq-2026-05-11-{index:02d}",
        "message": case.question,
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        PRODUCTION_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        body = json.loads(response.read().decode("utf-8"))
    return body.get("response", "")


def missing_markers(answer: str, expected: Iterable[str]) -> List[str]:
    normalized = normalize(answer)
    return [marker for marker in expected if normalize(marker) not in normalized]


def render_report(results: list[dict]) -> str:
    passed = sum(1 for result in results if result["passed"])
    lines = [
        "# Production KG Prerequisite Checks",
        "",
        "- Target: `https://smart-academic-advisor-api.vercel.app/chat`",
        "- Date: 2026-05-11",
        f"- Total: {passed}/{len(results)} passed",
        "- Scope: 25 English and 25 Egyptian Arabic prerequisite / after-course questions.",
        "",
        "## Summary",
        "",
        "| # | Language | Result | Missing markers |",
        "|---:|---|---|---|",
    ]
    for result in results:
        missing = ", ".join(result["missing"]) if result["missing"] else "-"
        lines.append(
            f"| {result['index']} | {result['language']} | "
            f"{'PASS' if result['passed'] else 'FAIL'} | {missing} |"
        )

    lines.extend(["", "## Detailed Results", ""])
    for result in results:
        lines.extend(
            [
                f"### {result['index']}. {result['language']} - "
                f"{'PASS' if result['passed'] else 'FAIL'}",
                "",
                f"**Question:** {result['question']}",
                "",
                f"**Expected markers:** {', '.join(result['expected_all'])}",
                "",
                "**Production answer:**",
                "",
                "```text",
                result["answer"].strip(),
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    socket.setdefaulttimeout(25)
    results = []
    for index, case in enumerate(cases(), start=1):
        try:
            answer = post_chat(case, index)
            missing = missing_markers(answer, case.expected_all)
        except (urllib.error.URLError, TimeoutError, socket.timeout, json.JSONDecodeError) as exc:
            answer = f"ERROR: {exc}"
            missing = list(case.expected_all)
        result = {
            "index": index,
            "language": case.language,
            "question": case.question,
            "expected_all": case.expected_all,
            "answer": answer,
            "missing": missing,
            "passed": not missing,
        }
        results.append(result)
        print(
            f"{index:02d}/50 {case.language}: "
            f"{'PASS' if result['passed'] else 'FAIL'}",
            flush=True,
        )
        time.sleep(0.2)

    REPORT_PATH.write_text(render_report(results), encoding="utf-8")
    print(f"Report written to {REPORT_PATH}")
    return 0 if all(result["passed"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

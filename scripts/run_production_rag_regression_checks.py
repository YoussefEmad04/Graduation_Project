"""
Run broad production-style RAG regression checks over regulations_clean.md.

The checks intentionally use marker groups instead of exact answer text. Each
case passes only when the local RAG path retrieves the expected regulation
details and avoids common wrong-topic sections.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

from advisor_ai.rag_service import RAGService


@dataclass(frozen=True)
class RagCase:
    topic: str
    prompt: str
    expected_groups: List[List[str]]
    forbidden: List[str] = field(default_factory=list)


def normalize(text: str) -> str:
    text = text.lower()
    replacements = {
        "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
        "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي",
        "ـ": "",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"[^\w\s٪%+.-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def hit_any(answer: str, markers: List[str]) -> bool:
    normalized_answer = normalize(answer)
    return any(normalize(marker) in normalized_answer for marker in markers)


def cases() -> List[RagCase]:
    return [
        RagCase("graduate affairs", "ما خدمات قسم شؤون الخريجين؟", [["شهادات التخرج"], ["المحتوى العلمي"]]),
        RagCase("graduate affairs", "قسم الخريجين بيطلعلي ايه؟", [["شهادات التخرج"], ["الخريجين"]]),
        RagCase("graduate affairs", "graduate affairs services", [["شهادات التخرج"], ["الخريجين"]]),

        RagCase("transfer policy", "ما شروط التحويل لكلية الذكاء الاصطناعي؟", [["CGPA", "المعدل التراكمي"], ["2"], ["60"]]),
        RagCase("transfer policy", "لو عايز احول للكلية محتاج CGPA كام؟", [["CGPA", "المعدل التراكمي"], ["2"], ["60"]]),
        RagCase("transfer policy", "transfer requirements to AI faculty", [["CGPA"], ["2"], ["60"]]),

        RagCase("admission requirements", "ما شروط القبول بالكلية؟", [["علمي"], ["رياضيات", "علوم"], ["Pre-mathematic"]]),
        RagCase("admission requirements", "القبول في الكلية محتاج علمي ايه؟", [["علمي"], ["رياضيات", "علوم"], ["Pre-mathematic"]]),
        RagCase("admission requirements", "admission requirements", [["علمي"], ["رياضيات", "علوم"], ["Pre-mathematic"]]),

        RagCase("graduate specifications", "ما مواصفات خريج كلية الذكاء الاصطناعي؟", [["حل المشكلات", "المشكلات الحاسوبية"], ["التعلم الذاتي"], ["أصحاب العمل"]]),
        RagCase("graduate specifications", "الخريج المفروض يعرف يعمل ايه؟", [["المشكلات الحاسوبية"], ["فرق"], ["أخلاقية", "المهنية"]]),

        RagCase("teaching language", "ما لغة التدريس في الكلية؟", [["الإنجليزية", "الانجليزية"]]),
        RagCase("teaching language", "الدراسة بالانجليزي ولا العربي؟", [["الإنجليزية", "الانجليزية"]]),

        RagCase("graduation credit hours", "كم ساعة معتمدة للتخرج؟", [["144"]]),
        RagCase("graduation credit hours", "كام ساعة عشان اتخرج؟", [["144"]]),
        RagCase("graduation credit hours", "how many credit hours to graduate?", [["144"]]),

        RagCase("study system", "ما نظام الدراسة في الكلية؟", [["الساعات المعتمدة"], ["الخريف"], ["الربيع"], ["الصيفي"], ["17"], ["8"]]),
        RagCase("study system", "الدراسة عندنا ماشية بنظام ايه؟", [["الساعات المعتمدة"], ["الصيفي"], ["17"], ["8"]]),
        RagCase("study system", "study system credit hours summer?", [["الساعات المعتمدة"], ["الصيفي"], ["17"], ["8"]]),

        RagCase("maximum study duration", "ما المدة القصوى للدراسة؟", [["ثماني", "8"], ["16"], ["إيقاف القيد"]]),
        RagCase("maximum study duration", "اخر مدة اقعدها في الكلية كام سنة؟", [["ثماني", "8"], ["16"], ["إيقاف القيد"]]),

        RagCase("credit hour definition", "ما تعريف الساعة المعتمدة؟", [["وحدة قياس"], ["المحاضرة"], ["المعمل", "التمرين"]]),
        RagCase("credit hour definition", "يعني ايه credit hour؟", [["وحدة قياس"], ["المحاضرة"], ["نصف ساعة"]]),

        RagCase("graduation requirements", "ما شروط التخرج؟", [["CGPA"], ["2"], ["المقررات بدون ساعات"], ["مستلزمات"]]),
        RagCase("graduation requirements", "عايز اتخرج غير 144 ساعة محتاج ايه؟", [["CGPA"], ["2"], ["مستلزمات"]]),

        RagCase("minimum graduation duration", "ما الحد الأدنى للتخرج؟", [["ثلاث"], ["ستة"], ["خريف", "ربيع"]]),
        RagCase("minimum graduation duration", "اقل مدة للتخرج كام سنة؟", [["ثلاث"], ["ستة"], ["فصول"]]),

        RagCase("level transition", "ما شروط الانتقال بين المستويات؟", [["Freshman"], ["34"], ["Sophomore"], ["73"], ["Junior"], ["109"], ["Senior"], ["144"]]),
        RagCase("level transition", "Junior يبدأ من كام ساعة؟", [["Junior"], ["109"]]),

        RagCase("regular registration minimum", "ما الحد الأدنى للتسجيل في فصل الخريف أو الربيع؟", [["9"], ["الخريف", "الربيع"]]),
        RagCase("regular registration minimum", "اقل ساعات اسجلها في الترم العادي كام؟", [["9"], ["الخريف", "الربيع", "فصل"]]),

        RagCase("maximum registered hours by CGPA", "ما الحد الأقصى للساعات المسجلة حسب CGPA؟", [["21"], ["18"], ["15"], ["12"], ["CGPA"]]),
        RagCase("maximum registered hours by CGPA", "لو CGPA من 1 لاقل من 2 اسجل كام ساعة؟", [["15"], ["CGPA"]]),
        RagCase("maximum registered hours by CGPA", "CGPA less than 1 max registered hours", [["12"], ["CGPA"]]),

        RagCase("summer semester", "ما مدة الفصل الصيفي؟", [["8"]]),
        RagCase("summer semester", "ما الحد الأقصى للتسجيل في الفصل الصيفي؟", [["9"]]),
        RagCase("summer semester", "summer semester كام ساعة؟", [["9"]]),

        RagCase("registration deadline", "حتى متى يستمر تسجيل المقررات؟", [["الأسبوع الثاني", "الاسبوع الثاني"]], ["متطلباته السابقة"]),
        RagCase("registration deadline", "التسجيل في المواد بيفضل مفتوح لحد امتى؟", [["الأسبوع الثاني", "الاسبوع الثاني"]], ["متطلباته السابقة"]),

        RagCase("add drop deadline", "حتى متى يسمح بالحذف والإضافة؟", [["الأسبوع الثالث", "الاسبوع الثالث"]], ["الأسبوع التاسع", "الاسبوع التاسع"]),
        RagCase("add drop deadline", "الحذف والاضافة اخرهم امتى؟", [["الأسبوع الثالث", "الاسبوع الثالث"]], ["الأسبوع التاسع", "الاسبوع التاسع"]),

        RagCase("prerequisite registration", "ما شرط التسجيل في مقرر؟", [["اجتياز"], ["متطلباته السابقة"]], ["الأسبوع الثاني", "الاسبوع الثاني"]),
        RagCase("prerequisite registration", "لو عايز اسجل مادة لازم اكون مخلص ايه؟", [["اجتياز"], ["متطلباته"]], ["الأسبوع الثاني", "الاسبوع الثاني"]),

        RagCase("course withdrawal", "ما قواعد الانسحاب من مقرر؟", [["الأسبوع التاسع", "الاسبوع التاسع"], ["W", "منسحب"]], ["الأسبوع الثاني", "الاسبوع الثاني"]),
        RagCase("course withdrawal", "اسحب مادة لحد امتى وهل هتبقى W؟", [["الأسبوع التاسع", "الاسبوع التاسع"], ["W", "منسحب"]], ["الأسبوع الثاني", "الاسبوع الثاني"]),
        RagCase("course withdrawal", "withdraw from a course deadline W", [["الأسبوع التاسع", "الاسبوع التاسع"], ["W", "منسحب"]]),

        RagCase("semester withdrawal", "ما قواعد إيقاف القيد والانسحاب الكلي من الفصل الدراسي؟", [["شهر"], ["أربعة", "4"], ["ستة", "6"]]),
        RagCase("semester withdrawal", "اسحب الترم كله ينفع لحد امتى؟", [["شهر"], ["أربعة", "4"], ["ستة", "6"]]),

        RagCase("incomplete grade I", "ما قواعد تقدير غير مكتمل I؟", [["I"], ["60"], ["W", "منسحب"]]),
        RagCase("incomplete grade I", "لو غبت عن final بعذر هاخد ايه؟", [["I"], ["60"]]),
        RagCase("incomplete grade I", "incomplete I grade accepted excuse", [["I"], ["60"], ["W", "منسحب"]]),

        RagCase("exam system", "ما نظام الامتحانات والنجاح؟", [["100"], ["50"]]),
        RagCase("exam system", "اقل درجة نجاح في المادة كام؟", [["50"]]),

        RagCase("theoretical grade distribution", "ما توزيع درجات المقرر النظري؟", [["40"], ["20"], ["30"]]),
        RagCase("theoretical grade distribution", "المادة النظري درجاتها بتتوزع ازاي؟", [["40"], ["20"], ["30"]]),

        RagCase("practical grade distribution", "ما توزيع درجات المقرر الذي يحتوي على تطبيقات عملية؟", [["40"], ["20"], ["التطبيقات", "تطبيقات", "المشاريع", "مشاريع"], ["30"]]),
        RagCase("practical grade distribution", "practical course grade distribution", [["40"], ["20"], ["التطبيقات", "تطبيقات", "المشاريع", "مشاريع"], ["30"]]),

        RagCase("graduation project", "ما قواعد مشروع التخرج؟", [["60"], ["40"], ["70"], ["خريف"], ["ربيع"]]),
        RagCase("graduation project", "مشروع التخرج بيتسجل امتى؟", [["70"], ["فصلين"], ["خريف"], ["ربيع"]]),

        RagCase("special grade symbols", "ما معنى Abs و I و W و Con؟", [["Abs"], ["I"], ["W"], ["Con"]]),
        RagCase("special grade symbols", "يعني ايه Abs و Con في التقديرات؟", [["Abs"], ["Con"]]),

        RagCase("grade scale", "ما جدول تقديرات A+ إلى F؟", [["A+"], ["96"], ["F"], ["50"]]),
        RagCase("grade scale", "A+ و F معناهم كام؟", [["A+"], ["96"], ["F"], ["50"]]),

        RagCase("cgpa calculation", "كيف يتم حساب CGPA؟", [["CGPA"], ["نقاط التقدير"], ["الساعات المعتمدة"]]),
        RagCase("cgpa calculation", "how is CGPA calculated?", [["CGPA"], ["نقاط"], ["الساعات"]]),

        RagCase("general grade classification", "ما التقدير العام حسب CGPA؟", [["ممتاز"], ["جيد جدا"], ["مقبول"], ["ضعيف"]]),
        RagCase("general grade classification", "CGPA 3.5 تقديره العام ايه؟", [["3.5"], ["ممتاز"]]),

        RagCase("pass fail non credit", "ما رموز مقررات النجاح والرسوب بدون ساعات معتمدة؟", [["AU"], ["P"], ["F"], ["W"], ["Abs"], ["I"]]),
        RagCase("pass fail non credit", "non credit pass fail symbols", [["AU"], ["P"], ["F"], ["W"]]),

        RagCase("academic warning", "متى يحصل الطالب على إنذار أكاديمي؟", [["CGPA"], ["2"]]),
        RagCase("academic warning", "يعني ايه انذار اكاديمي لو CGPA اقل من 2؟", [["CGPA"], ["2"]]),

        RagCase("absence warning 20", "متى يوجه إنذار غياب للطالب؟", [["20"]]),
        RagCase("absence warning 20", "غيابي وصل 20% يحصل ايه؟", [["20"], ["إنذار", "انذار"]]),

        RagCase("absence deprivation 25", "ماذا يحدث إذا تجاوز الغياب 25%؟", [["25"], ["حرمان", "يحرم"]]),
        RagCase("absence deprivation 25", "لو غيابي عدى 25% يحصل ايه؟", [["25"], ["حرمان", "يحرم"]]),

        RagCase("failed course retake", "ما قواعد إعادة مقرر رسب فيه الطالب؟", [["رسب"], ["83"], ["B"]], ["Withdrawal", "منسحب W"]),
        RagCase("failed course retake", "هعيد مادة كنت ساقط فيها الدرجة بتتحسب ازاي؟", [["رسب", "ساقط"], ["83"], ["B"]], ["Withdrawal", "منسحب W"]),

        RagCase("retake passed avoid dismissal", "ما قواعد إعادة مقرر نجح فيه الطالب لتجنب الفصل؟", [["تجنب الفصل"], ["CGPA"], ["2"], ["83"], ["B"]], ["تحسين معدله"]),
        RagCase("retake passed avoid dismissal", "انا تحت الملاحظة و CGPA اقل من 2 اعيد مادة نجحت فيها؟", [["CGPA"], ["2"], ["83"], ["B"]], ["3 مقررات"]),

        RagCase("improvement retake", "ما قواعد إعادة مقرر للتحسين؟", [["تحسين"], ["83"], ["B"], ["3 مقررات"]], ["مشروع التخرج"]),
        RagCase("improvement retake", "اعيد مادة عشان احسن المعدل ينفع؟", [["تحسين"], ["83"], ["3 مقررات"]], ["مشروع التخرج"]),

        RagCase("attendance final exam", "ما نسبة الحضور المطلوبة لدخول الامتحان النهائي؟", [["75"]]),
        RagCase("attendance final exam", "لازم احضر كام في الميه عشان ادخل الفاينال؟", [["75"]]),

        RagCase("final absence no excuse", "ماذا يحدث إذا تغيب الطالب عن الامتحان النهائي دون عذر؟", [["FA", "راسب"]]),
        RagCase("final absence no excuse", "لو غبت عن الفاينال من غير عذر؟", [["FA", "راسب"]]),

        RagCase("final absence accepted excuse", "ماذا يحدث إذا تغيب عن الامتحان النهائي بعذر قهري مقبول؟", [["I", "غير مكتمل"], ["60"]]),
        RagCase("final absence accepted excuse", "لو غبت عن final بعذر؟", [["I", "غير مكتمل"], ["60"]]),

        RagCase("hybrid learning", "ما قاعدة التعليم الهجين؟", [["60"], ["40"], ["مجلس القسم"], ["اعتماد الجامعة", "موافقة الجامعة"]]),
        RagCase("hybrid learning", "ينفع المقرر يبقى hybrid learning؟", [["60"], ["40"], ["الهجين"]]),

        RagCase("honor graduation", "ما شروط مرتبة الشرف؟", [["CGPA", "معدل تراكمي"], ["3"], ["أربع", "4"], ["ثمانية", "8"], ["رسب", "حرم"]]),
        RagCase("honor graduation", "مرتبة الشرف محتاجة CGPA كام؟", [["CGPA", "معدل تراكمي"], ["3"], ["أربع", "4"], ["ثمانية", "8"]]),

        RagCase("dismissal", "ما حالات الفصل من الكلية؟", [["أربعة", "4"], ["ستة", "6"], ["إنذار", "انذار"]]),
        RagCase("dismissal", "امتى الطالب يتفصل من الكلية؟", [["أربعة", "4"], ["ستة", "6"], ["إنذار", "انذار"]]),

        RagCase("final chance 80", "متى يمنح الطالب فرصة إضافية ونهائية؟", [["80"], ["موافقة مجلس الكلية"], ["الجامعة"]]),
        RagCase("final chance 80", "لو مخلص 80% من الساعات ومتعرض للفصل اخد فرصة اخيرة؟", [["80"], ["فرصة إضافية", "فرصه اضافيه"]]),

        RagCase("student grievance", "ما موعد التظلم من نتيجة الامتحان؟", [["أسبوع", "اسبوع"], ["إعلان النتائج"], ["نتيجة فحص التظلم"]]),
        RagCase("student grievance", "التظلم آخره امتى؟", [["أسبوع", "اسبوع"], ["إعلان النتائج"]]),
        RagCase("student grievance", "what is the appeal deadline?", [["أسبوع", "اسبوع"], ["التظلم"]]),
    ]


def answer_case(service: RAGService, case: RagCase) -> str:
    return (
        service._known_regulation_answer(case.prompt)
        or service._local_regulation_fallback(case.prompt)
        or "مش لاقي المعلومة دي في اللائحة."
    )


def run() -> int:
    service = RAGService()
    topic_stats: Dict[str, List[int]] = {}
    total = 0
    passed = 0

    for case in cases():
        total += 1
        topic_stats.setdefault(case.topic, [0, 0])
        topic_stats[case.topic][1] += 1

        answer = answer_case(service, case)
        missing_groups = [
            group for group in case.expected_groups
            if not hit_any(answer, group)
        ]
        forbidden_hits = [
            marker for marker in case.forbidden
            if normalize(marker) in normalize(answer)
        ]
        ok = not missing_groups and not forbidden_hits

        if ok:
            passed += 1
            topic_stats[case.topic][0] += 1
        else:
            print(f"\n[FAIL] {case.topic}: {case.prompt}")
            print(f"Expected groups: {case.expected_groups}")
            if missing_groups:
                print(f"Missing groups: {missing_groups}")
            if forbidden_hits:
                print(f"Forbidden hits: {forbidden_hits}")
            print(f"Answer: {answer}")

    print("\nTopic summary:")
    for topic in sorted(topic_stats):
        topic_passed, topic_total = topic_stats[topic]
        status = "PASS" if topic_passed == topic_total else "FAIL"
        print(f"- {status} {topic}: {topic_passed}/{topic_total}")

    print(f"\nSummary: {passed}/{total} passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(run())

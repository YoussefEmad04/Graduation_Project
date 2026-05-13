"""
RAG Service - Retrieval-Augmented Generation over academic regulations.

Production uses OpenAI hosted vector stores and the Responses API file_search
tool, so Vercel does not need local ChromaDB or PDF parsing dependencies.
"""

import logging
import os
import re
from functools import lru_cache
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI

from advisor_ai.language_utils import contains_arabic, should_respond_arabic, strict_language_instruction

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# -- Configuration ---------------------------------------------------------

def _env(name: str, default: str = "") -> str:
    """Read an environment variable and trim deployment-input whitespace."""
    return (os.getenv(name, default) or "").strip()


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CLEAN_REGULATIONS_SOURCE = os.path.join(
    PROJECT_ROOT, "important_pdf", "RAG", "regulations_clean.md"
)
EXTRACTED_REGULATIONS_SOURCE = os.path.join(
    PROJECT_ROOT, "important_pdf", "RAG", "regulations_extracted.md"
)
REGULATIONS_SOURCE = (
    CLEAN_REGULATIONS_SOURCE
    if os.path.exists(CLEAN_REGULATIONS_SOURCE)
    else EXTRACTED_REGULATIONS_SOURCE
)

RETRIEVE_K = 8
OPENAI_VECTOR_STORE_ID_ENV = "OPENAI_VECTOR_STORE_ID"

OPENAI_API_KEY_ERROR = (
    "OPENAI_API_KEY is not configured. Set it in your shell, .env file, or "
    "Vercel environment variables to use regulation RAG."
)
OPENAI_VECTOR_STORE_ERROR = (
    "OPENAI_VECTOR_STORE_ID is not configured. Run "
    "`python scripts/setup_openai_vector_store.py`, then add the printed "
    "vector store id to your .env and Vercel environment variables."
)

REVERSED_ARABIC_MARKERS = (
    "ةعماجلا", "ةيلك", "بلاطلا", "تاعاس", "لدعملا", "جرخت",
    "ررقم", "ةسارد", "ماظن", "طورش", "تابلطتم", "ةجرد",
)

READABLE_ARABIC_TERMS = (
    "الطالب", "الكلية", "الجامعة", "الساعات", "المعتمدة", "التخرج",
    "الدراسة", "الفصل", "الدراسي", "التسجيل", "المقرر", "المقررات",
    "الامتحان", "الإمتحان", "النهائي", "منتصف", "غياب", "عذر",
    "مقبول", "غير", "مكتمل", "منسحب", "شروط", "نظام", "الحضور",
    "الأعمال", "الفصلية", "مجلس", "المرشد", "الأكاديمي",
)

REGULATIONS_CLEAN_EXCERPTS = [
    {
        "page": 31,
        "text": (
            "لغة التدريس: اللغة الإنجليزية، ويمكن تدريس مقررات متطلبات الجامعة بلغة أخرى "
            "على أن يكون الامتحان بنفس لغة تدريس المقرر.\n"
            "عدد الساعات اللازمة للتخرج: يتطلب الحصول على درجة البكالوريوس أن يجتاز الطالب "
            "بنجاح 144 ساعة معتمدة موزعة على ستة فصول دراسية نظامية على الأقل.\n"
            "نظام الدراسة: تعتمد الدراسة على نظام الساعات المعتمدة. السنة الدراسية تتكون من "
            "فصل الخريف وفصل الربيع، وفصل صيفي اختياري للطالب. مدة الفصول النظامية 17 أسبوعا "
            "تتضمن فترة عقد الامتحانات، والفصل الصيفي مدته 8 أسابيع تتضمن فترة عقد الامتحانات."
        ),
    },
    {
        "page": 32,
        "text": (
            "المدة القصوى للدراسة في الكلية هي ثماني سنوات دراسية، أي ستة عشر فصلا دراسيا "
            "نظاميا خريف وربيع، مع عدم احتساب فصول إيقاف القيد التي تمت الموافقة عليها من "
            "مجلس الكلية ومجلس الجامعة ضمن الفصول المسموح بها.\n"
            "تعريف الساعة المعتمدة: هي وحدة قياس دراسية تحدد وزن المقرر الدراسي، وتحتسب ساعة "
            "المحاضرة بساعة معتمدة، بينما تحتسب ساعة التمرين أو المعمل بنصف ساعة معتمدة.\n"
            "يجوز في الحالات الاستثنائية وبناء على اقتراح المرشد الأكاديمي أن يتحمل الطالب "
            "ساعات معتمدة أكثر من الحد الأقصى في حالات التخرج والحالات التي يحددها مجلس القسم "
            "بعد موافقة عميد الكلية."
        ),
    },
    {
        "page": 33,
        "text": (
            "شروط التخرج: تمنح الدرجة العلمية متى استوفى الطالب متطلبات الحصول عليها بحسب "
            "لائحة الكلية. يجب أن يجتاز الطالب بنجاح عدد الساعات المعتمدة المنصوص عليها في "
            "اللائحة بمعدل تراكمي مجمع CGPA لا يقل عن 2، وأن يجتاز جميع المقررات بدون ساعات "
            "معتمدة المنصوص عليها بلائحة الكلية، وأن يجتاز ما تنص عليه الجامعة كمستلزمات "
            "للتخرج.\n"
            "الحد الأدنى للتخرج والحصول على درجة البكالوريوس هو ثلاث سنوات دراسية، أي ستة "
            "فصول نظامية خريف وربيع.\n"
            "الانتقال بين المستويات يكون بحسب عدد الساعات المعتمدة التي اجتازها الطالب "
            "بنجاح: Freshman حتى 34 ساعة، Sophomore حتى 73 ساعة، Junior حتى 109 ساعات، "
            "Senior حتى 144 ساعة."
        ),
    },
    {
        "page": 34,
        "text": (
            "عدد ساعات التسجيل في الفصول الدراسية المختلفة: الحد الأدنى للتسجيل في الفصول "
            "النظامية خريف وربيع هو 9 ساعات معتمدة، ويجوز التجاوز عن الحد الأدنى إذا كانت "
            "الساعات المتبقية للتخرج أقل من ذلك.\n"
            "الحد الأقصى للساعات المسجلة: 18 ساعة للطلاب المستجدين في الفصل الدراسي الأول، "
            "و21 ساعة للطلاب الحاصلين على CGPA أعلى من أو يساوي 3 وكذلك الطالب الذي "
            "سيتخرج في نفس الفصل، و18 ساعة للطلاب الحاصلين على CGPA من 2 إلى أقل من 3، "
            "و15 ساعة للطلاب الحاصلين على CGPA من 1 إلى أقل من 2، و12 ساعة للطلاب "
            "الحاصلين على CGPA أقل من 1.\n"
            "يسمح للطالب الحاصل سابقا على تقدير غير مكتمل I بتسجيل مقرر إضافي واحد فوق "
            "هذه الحدود. الفصل الصيفي اختياري، والحد الأقصى للساعات المسجلة فيه 9 ساعات "
            "معتمدة."
        ),
    },
    {
        "page": 35,
        "text": (
            "أوقات التسجيل والحذف والإضافة والانسحاب: تسجيل المقررات يستمر حتى نهاية "
            "الأسبوع الثاني. بعد بدء الدراسة يمكن للطالب حذف مقرر أو أكثر أو إضافة مقرر أو "
            "أكثر بعد موافقة المرشد الأكاديمي ومراعاة المواعيد التي يحددها مجلس الجامعة، "
            "وذلك حتى نهاية الأسبوع الثالث.\n"
            "شروط التسجيل في مقرر: يسمح للطالب بدراسة والتسجيل في أي مقرر بناء على "
            "اجتياز متطلباته السابقة.\n"
            "الانسحاب Withdrawal: يجوز للطالب أن ينسحب من التسجيل في مقرر أو أكثر بعد "
            "موافقة المرشد الأكاديمي حتى نهاية الأسبوع التاسع مع مراعاة الحد الأدنى لعدد "
            "الساعات المعتمدة، وفي هذه الحالة لا يعد الطالب راسبا ويحتسب له تقدير "
            "منسحب W فقط. أما إذا انسحب بعد الفترة المحددة دون عذر قهري يقبله مجلس "
            "الكلية فيحتسب له تقدير راسب في المقررات التي انسحب منها. وإذا تقدم قبل "
            "الامتحان بشهر على الأقل بعذر قهري يقبله مجلس الكلية فيحتسب له تقدير "
            "منسحب W.\n"
            "إيقاف القيد والانسحاب الكلي من الفصل الدراسي: يجوز للطالب إيقاف قيده أو "
            "الانسحاب الكلي من الفصل الدراسي وفقا للضوابط التي تحددها الكلية والجامعة "
            "على ألا يتجاوز ذلك موعدا قبل الامتحان بشهر على الأقل. والطالب الذي لم "
            "يحضر للتسجيل خلال فترة التسجيل والحذف والإضافة في الفصول النظامية يعتبر "
            "منسحبا. ولا يجوز أن يتجاوز عدد الفصول النظامية التي ينسحب منها الطالب "
            "أربعة فصول دراسية متتالية أو ستة فصول منفصلة."
        ),
    },
    {
        "page": 36,
        "text": (
            "تقدير غير مكتمل I: إذا تقدم الطالب بعذر قهري قبله مجلس الكلية عن عدم حضور "
            "الامتحان النهائي لأي مقرر، يحتسب له تقدير غير مكتمل I بشرط أن يكون حاصلا "
            "على 60% على الأقل من درجات الأعمال الفصلية وألا يكون قد تم حرمانه من دخول "
            "الامتحانات النهائية.\n"
            "يؤدي الطالب الحاصل على تقدير غير مكتمل الامتحان النهائي فقط، وتحتسب الدرجة "
            "النهائية على أساس درجة الامتحان النهائي مضافة إلى درجة الأعمال الفصلية السابقة. "
            "ويجب أداء الامتحان خلال نفس العام الدراسي أو العام الدراسي التالي من احتساب "
            "المقرر غير مكتمل، وإلا يتحول التقدير إلى منسحب W ويعيد الطالب المقرر كاملا "
            "دراسة وامتحانا.\n"
            "إذا لم يحقق الطالب شرط 60% من الأعمال الفصلية رغم وجود عذر قهري مقبول، "
            "فيحتسب له تقدير منسحب W في المقرر ويعيده كاملا."
        ),
    },
    {
        "page": 37,
        "text": (
            "نظام الامتحانات: النهاية العظمى لدرجات كل مقرر 100 درجة، والنهاية الصغرى للنجاح 50 درجة.\n"
            "توزيع درجات المقرر النظري: 40% لامتحان نهاية الفصل الدراسي، بشرط أن يحصل الطالب على "
            "30% من درجة الامتحان النهائي التحريري على الأقل شرطا للنجاح، و20% لامتحان منتصف الفصل "
            "الدراسي، و40% للاختبارات الدورية والأعمال الفصلية."
        ),
    },
    {
        "page": 38,
        "text": (
            "توزيع درجات المقرر الذي يحتوي على تطبيقات عملية: 40% للامتحان النهائي، بشرط "
            "الحصول على 30% على الأقل من درجة الامتحان النهائي التحريري شرطا للنجاح، "
            "و20% لامتحان منتصف الفصل، و20% للاختبارات الدورية والأعمال الفصلية، و20% "
            "للتطبيقات العملية من امتحانات عملية أو مشاريع.\n"
            "توزيع درجات مشروع التخرج: 60% للأعمال الفصلية و40% لتقييم لجنة المناقشة.\n"
            "الحد الأدنى للنجاح في المقرر الدراسي هو 50% من الدرجة النهائية، وزمن امتحان "
            "نهاية الفصل لأي مقرر دراسي ساعتان.\n"
            "يحق للطالب الذي اجتاز 70% من عدد الساعات المعتمدة اللازمة للتخرج تسجيل مقرر "
            "المشروع، ويتم تسجيل المشروع في فصلين نظاميين متتاليين خريف ثم ربيع."
        ),
    },
    {
        "page": 39,
        "text": (
            "جدول التقديرات يوضح أن النهاية الصغرى للنجاح هي 50%، وأن تقدير الغياب عن "
            "الامتحان النهائي بدون عذر مقبول هو Abs، وتقدير غير مكتمل هو I، والانسحاب "
            "من مقرر هو W.\n"
            "جدول تقديرات ونقاط المقررات ذات الساعات المعتمدة: A+ من 96% فأكثر يساوي 4، "
            "A من 92% إلى أقل من 96% يساوي 3.7، A- من 88% إلى أقل من 92% يساوي 3.4، "
            "B+ من 84% إلى أقل من 88% يساوي 3.2، B من 80% إلى أقل من 84% يساوي 3، "
            "B- من 76% إلى أقل من 80% يساوي 2.8، C+ من 72% إلى أقل من 76% يساوي 2.6، "
            "C من 68% إلى أقل من 72% يساوي 2.4، C- من 64% إلى أقل من 68% يساوي 2.2، "
            "D+ من 60% إلى أقل من 64% يساوي 2، D من 55% إلى أقل من 60% يساوي 1.5، "
            "D- من 50% إلى أقل من 55% يساوي 1، وF أقل من 50%.\n"
            "كيفية حساب المعدل التراكمي المجمع CGPA تعتمد على مجموع حاصل ضرب نقاط التقدير "
            "في عدد الساعات المعتمدة لكل مقرر مقسوما على مجموع الساعات المعتمدة للمقررات."
        ),
    },
    {
        "page": 39,
        "text": (
            "التقدير العام لكل فصل دراسي وعند التخرج بحسب المعدل التراكمي المجمع يكون كالتالي: "
            "أقل من 1 ضعيف جدا، ومن 1 إلى أقل من 2 ضعيف، ومن 2 إلى أقل من 2.5 مقبول، "
            "ومن 2.5 إلى أقل من 3 جيد، ومن 3 إلى أقل من 3.5 جيد جدا، ومن 3.5 فأكثر ممتاز."
        ),
    },
    {
        "page": 39,
        "text": (
            "مقررات النجاح والرسوب بدون ساعات معتمدة يكون تقديرها كالتالي: AU مستمع، "
            "P ناجح، F راسب، W منسحب، Abs غياب عن حضور الامتحان النهائي بدون عذر مقبول، "
            "و I غير مكتمل إذا كان للمقرر أعمال سنة."
        ),
    },
    {
        "page": 40,
        "text": (
            "الإنذار الأكاديمي: يحصل الطالب على إنذار أكاديمي إذا كان معدله التراكمي "
            "المجمع CGPA في أي فصل دراسي نظامي أقل من 2 فيما عدا الفصل الدراسي الأول "
            "للطالب في الكلية.\n"
            "يوجه إنذار للطالب إذا وصلت نسبة غيابه في المقرر إلى 20%، وإذا تجاوزت "
            "25% يتخذ مجلس الكلية قرارا بحرمانه من دخول الامتحان ويحسب له في المقرر "
            "معدل صفر.\n"
            "إذا رسب الطالب في مقرر فعليه إعادة دراسته والامتحان فيه مرة أخرى، وإذا نجح "
            "بعد الإعادة تحتسب له الدرجة الفعلية التي حصل عليها وبما لا يزيد عن 83 "
            "أعلى درجة في B."
        ),
    },
    {
        "page": 41,
        "text": (
            "إذا كان الطالب تحت الملاحظة الأكاديمية وكان CGPA في بداية الفصل الدراسي أقل "
            "من 2، فيجوز له إعادة مقرر سبق أن نجح فيه لرفع معدله التراكمي المجمع لتجنب "
            "الفصل، وتحتسب له أعلى درجة حصل عليها في جميع مرات الإعادة وبما لا يزيد "
            "عن 83 أعلى درجة في B.\n"
            "يمكن للطالب إعادة أي عدد من المقررات التي سبق ونجح بها من أجل رفع معدله "
            "إلى 2، مع احتساب عدد ساعات المقرر مرة واحدة فقط."
        ),
    },
    {
        "page": 42,
        "text": (
            "يجوز للطالب إعادة مقرر سبق أن نجح فيه لتحسين معدله التراكمي المجمع، وتحتسب "
            "له أعلى درجة حصل عليها وبما لا يزيد عن 83 أعلى درجة في B.\n"
            "الحد الأقصى لإعادة المقررات بغرض التحسين هو 3 مقررات، ويجب أن يكون المقرر "
            "تابعا للمستوى المقيد به الطالب أو لمستوى أقل."
        ),
    },
    {
        "page": 45,
        "text": (
            "قواعد المواظبة على الحضور: يتطلب دخول الطالب الامتحان النهائي لأي مقرر تحقيق نسبة "
            "حضور لا تقل عن 75% من المحاضرات والتطبيقات المحددة له. إذا تجاوزت نسبة الغياب 25% "
            "يجوز لمجلس الكلية حرمانه من دخول الامتحان النهائي بعد إنذاره كتابيا.\n"
            "إذا تغيب الطالب عن الامتحان النهائي لأي مقرر دون عذر مقبول يعطى تقدير راسب FA. "
            "أما إذا تقدم بعذر قهري يقبله مجلس الكلية فيحسب له تقدير غير مكتمل I بشرط حصوله "
            "على 60% على الأقل من درجات الأعمال الفصلية."
        ),
    },
    {
        "page": 43,
        "text": (
            "قواعد المواظبة على الحضور: يتطلب دخول الطالب الامتحان النهائي لأي مقرر تم "
            "تسجيله تحقيق نسبة حضور لا تقل عن 75% من المحاضرات والتطبيقات المحددة له. "
            "إذا تجاوزت نسبة الغياب 25% يجوز لمجلس الكلية حرمانه من دخول الامتحان النهائي "
            "بعد إنذاره كتابيا.\n"
            "إذا تغيب الطالب عن الامتحان النهائي دون عذر مقبول يعطى تقدير راسب FA. وإذا "
            "تقدم بعذر قهري مقبول يحتسب له تقدير غير مكتمل I بشرط حصوله على 60% على الأقل "
            "من درجات الأعمال الفصلية.\n"
            "للطالب الحاصل على غير مكتمل فرصة أداء الامتحان النهائي بحد أقصى أسبوع من "
            "بداية الفصل الدراسي التالي.\n"
            "تحتسب الدرجة النهائية للطالب في حالة غير مكتمل على أساس درجة الامتحان النهائي "
            "مضافة إلى الدرجة التي سبق حصوله عليها في الأعمال الفصلية.\n"
            "يجوز لمجلس الكلية بعد أخذ رأي مجلس القسم أن يقرر تدريس مقرر أو أكثر بنمط "
            "التعليم الهجين بنسبة 60% وجها لوجه و40% بنظام التعليم عن بعد أو بأي نسبة "
            "أخرى بعد موافقة الجامعة."
        ),
    },
    {
        "page": 44,
        "text": (
            "مرتبة الشرف: تمنح للطالب إذا اجتاز مقرراته الدراسية بمعدل تراكمي مجمع لا يقل "
            "عن 3 بما يعادل جيد جدا، بشرط ألا تزيد فترة الدراسة عن أربع سنوات دراسية "
            "ثمانية فصول نظامية، وألا يكون قد رسب أو حرم في أي مقرر خلال دراسته.\n"
            "الفصل من الكلية: يفصل الطالب إذا حصل على إنذار أكاديمي في أربعة فصول دراسية "
            "نظامية متتالية أو ستة فصول دراسية نظامية متفرقة، أو إذا تجاوز المدة القصوى "
            "للدراسة بعد حذف فصول إيقاف القيد.\n"
            "يجوز منح الطالب المعرض للفصل فرصة إضافية ونهائية للتسجيل في فصلين نظاميين "
            "متتاليين بالإضافة إلى فصل صيفي إذا كان قد اجتاز 80% على الأقل من إجمالي "
            "الساعات اللازمة للتخرج، وذلك بعد موافقة مجلس الكلية والجامعة."
        ),
    },
    {
        "page": 44,
        "text": (
            "التظلمات الطلابية: يحق للطالب التقدم بطلب تظلم من نتيجة امتحانه في مقرر أو أكثر. "
            "آخر موعد للتظلم هو أسبوع من تاريخ إعلان النتائج، ويتم إبلاغ الطالب كتابيا "
            "بنتيجة فحص التظلم المقدم منه."
        ),
    },
]

RAG_FILE_SEARCH_INSTRUCTIONS = """You are the Smart Academic Advisor for the Faculty of Artificial Intelligence at the Egyptian Russian University (ERU).

Answer student questions about academic regulations, policies, and study-plan tables using ONLY the content retrieved from the official regulations file attached through file_search.

Key facts:
- Faculty programs: Artificial Intelligence, Data Science, Cybersecurity, Software Engineering
- Graduation: 144 credit hours minimum
- Study system: Credit hours, Fall + Spring semesters + optional Summer
- Teaching language: English, except some university requirements may use another language

Language rules:
- If the student writes in English, respond only in English.
- If the student writes in Arabic, including Egyptian Arabic, respond only in Arabic.
- If the student writes Arabizi, respond in friendly Egyptian Arabic.
- If the student mixes Arabic and English in one question, respond only in Arabic. Preserve official English terms like CGPA, W, I, FA, and course/program names when useful.
- Do not mix languages in one response.

Understanding rules:
- Treat Egyptian Arabic and colloquial student wording as valid queries even if the document uses formal Arabic.
- Map colloquial wording to the official regulation meaning before answering.
- Treat mixed Arabic/English academic wording as equivalent to the formal wording in the regulation document. Examples:
  - "final" / "فاينال" -> الامتحان النهائي
  - "midterm" / "ميدترم" -> امتحان منتصف الفصل
  - "CGPA" inside Arabic questions stays CGPA
  - "withdraw" / "drop" inside Arabic questions -> الانسحاب من مقرر
- When the student asks with "أنا", "لو أنا", "أقدر", "ينفعلي", or asks about "الطالب", interpret the rule as applying to the asking student.
- Answer student-facing policies directly to the student when appropriate, while keeping the regulation facts exact.

Answer rules:
- Use only retrieved file content. Do not invent regulations.
- Be precise with numbers, percentages, weeks, credit hours, and course codes.
- For study-plan tables, preserve course codes exactly. If a prerequisite is shown only as a code, return the code only.
- Do not dump full program course catalogs from RAG. If the retrieved content contains long course lists for Software Engineering, Artificial Intelligence, Cybersecurity, or Data Science, omit those lists and give only a concise summary of the requirement, semester, credit hours, or category the student asked about.

Arabic answer format:
- Start with a short direct answer.
- Then write concise bullets from the regulation.
- Clearly highlight important numbers and official symbols, including credit hours, weeks, percentages, CGPA, deadlines, W, I, FA, Abs, and Withdrawal.
- Do not mix Arabic and English except for official terms such as CGPA, W, I, FA, Abs, Withdrawal, course codes, and program names.
- Do not write a long answer unless the student asks for details.
- If the retrieved content does not contain the answer, say only: "مش لاقي المعلومة دي في اللائحة."

English answer format:
- Start with a direct short answer.
- Then write concise bullets from the regulation.
- Clearly include numbers, weeks, percentages, CGPA thresholds, deadlines, or grade symbols.
- Do not write a long answer unless the student asks for details.
- If the retrieved content does not contain the answer, say only: "I couldn't find this specific regulation in the document."
"""


class RAGService:
    """Handles regulation queries using OpenAI vector store file search."""

    def __init__(self):
        self.client = None
        self.vector_store_id = _env(OPENAI_VECTOR_STORE_ID_ENV)
        self.model = _env("OPENAI_LLM_MODEL", "gpt-4o-mini")
        self.last_error = None

        if not _env("OPENAI_API_KEY"):
            self.last_error = OPENAI_API_KEY_ERROR
            logger.warning(OPENAI_API_KEY_ERROR)
            return

        if not self.vector_store_id:
            self.last_error = OPENAI_VECTOR_STORE_ERROR
            logger.warning(OPENAI_VECTOR_STORE_ERROR)
            return

        self.client = OpenAI(api_key=_env("OPENAI_API_KEY"))
        logger.info("RAG Service initialized with OpenAI vector store file_search")

    @property
    def chain(self):
        """Backward-compatible truthy marker for tests/status callers."""
        return self.client if self.client and self.vector_store_id else None

    def query(self, question: str) -> str:
        """Answer a regulation-related question using OpenAI file_search."""
        known_answer = self._known_regulation_answer(question)
        if known_answer:
            return known_answer

        if not _env("OPENAI_API_KEY"):
            return OPENAI_API_KEY_ERROR
        if not self.vector_store_id:
            return OPENAI_VECTOR_STORE_ERROR
        if not self.client:
            self.client = OpenAI(api_key=_env("OPENAI_API_KEY"))

        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=RAG_FILE_SEARCH_INSTRUCTIONS,
                input=self._build_retrieval_prompt(question),
                tools=[
                    {
                        "type": "file_search",
                        "vector_store_ids": [self.vector_store_id],
                        "max_num_results": RETRIEVE_K,
                    }
                ],
                temperature=0.2,
            )
            self.last_error = None
            answer = self._response_text(response)
            if self._should_try_local_fallback(question, answer):
                local_answer = self._local_regulation_fallback(question)
                if local_answer:
                    return local_answer
            return answer
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error querying OpenAI vector store RAG: {e}")
            local_answer = self._local_regulation_fallback(question)
            if local_answer:
                return local_answer
            return f"Error querying regulations: {str(e)}"

    def _known_regulation_answer(self, question: str) -> str:
        """Return deterministic answers only for exact, stable numeric regulation facts."""
        q = self._normalize_egyptian_question(question)

        graduation_terms = ("يتخرج", "اتخرج", "للتخرج", "التخرج", "graduate")
        hour_terms = (
            "كم ساعه", "كام ساعه", "ساعه معتمده", "ساعات معتمده",
            "credit hours", "عدد الساعات اللازمة",
        )
        if any(term in q for term in graduation_terms) and any(term in q for term in hour_terms):
            if should_respond_arabic(question):
                return "- لازم الطالب يجتاز 144 ساعة معتمدة عشان يتخرج."
            return "- Students must complete 144 credit hours to graduate."
        if "graduation credit hours" in q:
            return "- Students must complete 144 credit hours to graduate."

        if "الفصل الدراسي النظامي" in q and any(term in q for term in ("كام اسبوع", "كم اسبوع", "مدته", "مده")):
            return "- مدة الفصل الدراسي النظامي 17 أسبوعًا متضمنة فترة الامتحانات."
        if "regular semester" in q and any(term in q for term in ("how long", "duration", "weeks", "how many")):
            return "- A regular semester lasts 17 weeks including the exam period."

        if (
            ("الفصل الصيفي" in q or "الصيفي" in q)
            and any(term in q for term in ("كام اسبوع", "كم اسبوع", "مدته", "مده"))
            and not any(term in q for term in ("كام ساعه", "كم ساعه", "تسجيل", "اسجل", "الحد الاقصي", "الحد الاقصى"))
        ):
            return "- الفصل الصيفي مدته 8 أسابيع متضمنة فترة الامتحانات."
        if "summer semester" in q and any(term in q for term in ("how long", "duration", "weeks", "how many")):
            return "- The summer semester lasts 8 weeks including the exam period."

        if (
            ("الفصل الصيفي" in q or "الصيفي" in q)
            and any(term in q for term in ("الحد الاقصي", "الحد الاقصى", "كام ساعه", "كم ساعه", "تسجيل", "اسجل"))
            and not any(term in q for term in ("كام اسبوع", "كم اسبوع", "مدته", "مده"))
        ):
            return "- الحد الأقصى للتسجيل في الفصل الصيفي هو 9 ساعات معتمدة."
        if "summer semester" in q and any(term in q for term in ("max", "maximum", "credit hours", "hours")):
            return "- The maximum load in the summer semester is 9 credit hours."

        if any(term in q for term in ("اقل درجه للنجاح", "اقل درجة للنجاح", "اقل درجه نجاح", "اقل درجة نجاح", "النهايه الصغري للنجاح", "النهاية الصغري للنجاح")):
            return "- أقل درجة للنجاح في أي مقرر هي 50 درجة."
        if any(term in q for term in ("minimum passing grade", "minimum pass grade", "minimum grade to pass")):
            return "- The minimum passing grade in any course is 50%."

        if ("نسبه الحضور" in q or "نسبة الحضور" in q or "الحضور" in q) and "الامتحان النهائي" in q:
            return "- نسبة الحضور المطلوبة لدخول الامتحان النهائي لا تقل عن 75% من المحاضرات والتطبيقات."
        if "attendance" in q and "الامتحان النهائي" in q:
            return "- A student needs at least 75% attendance to sit the final exam."
        if "attendance" in q and "final" in q:
            return "- A student needs at least 75% attendance to sit the final exam."

        if "غياب" in q and "25" in q:
            return "- حد الغياب هو 25%؛ إذا تجاوز الطالب هذه النسبة قد يحرم من دخول الامتحان النهائي."
        if "absence" in q and any(term in q for term in ("limit", "maximum", "25")):
            return "- The absence limit is 25%."

        if "academic warning" in q or "انذار اكاديمي" in q:
            if should_respond_arabic(question):
                return "- يحصل الطالب على إنذار أكاديمي إذا كان CGPA أقل من 2."
            return "- A student receives an academic warning when their CGPA is less than 2."
        if "انذار" in q and ("cgpa" in q or "معدل" in q) and "2" in q:
            return "- يحصل الطالب على إنذار أكاديمي إذا كان CGPA أقل من 2."
        return ""

    @staticmethod
    def _normalize_question(question: str) -> str:
        """Normalize question text for deterministic regulation matching."""
        q = (question or "").lower().strip()
        replacements = {
            "أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه",
            "cgpa": "cgpa",
            "credit hours": "credit hours",
            "midterm": "ميدترم",
            "mid term": "ميدترم",
            "final exam": "الامتحان النهائي",
            "summer semester": "summer semester",
            "study system": "نظام الدراسة",
            "teaching language": "لغة التدريس",
            "credit hour": "تعريف الساعة المعتمدة",
            "maximum study duration": "المدة القصوى للدراسة",
            "minimum graduation duration": "الحد الأدنى للتخرج",
            "level transition": "الانتقال بين المستويات",
            "registered hours": "الساعات المسجلة",
            "grade distribution": "توزيع درجات",
            "graduation project": "مشروع التخرج",
            "grade scale": "جدول تقديرات",
            "general grade": "التقدير العام",
            "pass fail": "مقررات النجاح والرسوب",
            "failed retake": "إعادة مقرر رسب فيه الطالب",
            "retake failed": "إعادة مقرر رسب فيه الطالب",
            "improvement retake": "إعادة مقرر للتحسين",
            "hybrid learning": "التعليم الهجين",
            "regular semester": "regular semester",
            "graduation requirements": "شروط التخرج",
            "withdraw from a course": "انسحب من مقرر",
            "drop a course": "انسحب من مقرر",
            "semester withdrawal": "الانسحاب الكلي من الفصل الدراسي",
            "stop enrollment": "ايقاف القيد",
            "incomplete grade": "تقدير غير مكتمل",
            "i grade": "تقدير غير مكتمل i",
            "missed final exam": "تغيب عن الامتحان النهائي",
            "attendance requirement": "نسبه الحضور",
            "academic warning": "انذار اكاديمي",
            "honor graduation": "مرتبة الشرف",
            "dismissal": "الفصل من الكلية",
            "grievance": "التظلمات الطلابية",
            "appeal": "التظلمات الطلابية",
            "admission requirements": "شروط القبول",
            "transfer policy": "شروط التحويل",
            "transfer requirements": "شروط التحويل",
            "graduate specifications": "مواصفات خريج كلية الذكاء الاصطناعي",
            "graduate affairs": "شؤون الخريجين",
        }
        for old, new in replacements.items():
            q = q.replace(old, new)
        q = q.replace("تعريف الساعة المعتمدةs", "credit hours")
        q = re.sub(r"\s+", " ", q)
        return q

    @classmethod
    def _normalize_egyptian_question(cls, question: str) -> str:
        """Rewrite common Egyptian Arabic phrasing into regulation-friendly wording."""
        q = cls._normalize_question(question)
        replacements = {
            "الترم العادي": "الفصل الدراسي النظامي",
            "الترم": "الفصل الدراسي",
            "والصيفي": "والفصل الصيفي",
            "الفاينال": "الامتحان النهائي",
            "الميدترم": "امتحان منتصف الفصل",
            "ميدترم": "امتحان منتصف الفصل",
            "ميد ترم": "امتحان منتصف الفصل",
            "لغة التدريس": "لغة التدريس",
            "الدراسة بالانجليزي": "لغة التدريس",
            "الدراسه بالانجليزي": "لغة التدريس",
            "الدراسة عندنا ماشية بنظام ايه": "نظام الدراسة",
            "الدراسه عندنا ماشيه بنظام ايه": "نظام الدراسة",
            "الدراسة ماشية بنظام ايه": "نظام الدراسة",
            "الدراسه ماشيه بنظام ايه": "نظام الدراسة",
            "اخر مدة اقعدها": "المدة القصوى للدراسة",
            "اخر مده اقعدها": "المدة القصوى للدراسة",
            "اقل مدة للتخرج": "الحد الأدنى للتخرج",
            "اقل مده للتخرج": "الحد الأدنى للتخرج",
            "اقل ساعات اسجلها": "الحد الأدنى للتسجيل",
            "محتاج علمي ايه": "شروط القبول",
            "عايز احول": "شروط التحويل",
            "عاوز احول": "شروط التحويل",
            "احول للكلية": "شروط التحويل",
            "الخريج المفروض يعرف يعمل ايه": "مواصفات خريج كلية الذكاء الاصطناعي",
            "تقديره العام": "التقدير العام",
            "تقديري العام": "التقدير العام",
            "عايز اتخرج": "شروط التخرج",
            "عاوز اتخرج": "شروط التخرج",
            "اخلص كام ساعة": "عدد الساعات اللازمة للتخرج",
            "اخلص كام ساعه": "عدد الساعات اللازمة للتخرج",
            "اشيل ماده": "انسحب من مقرر",
            "اسحب ماده": "انسحب من مقرر",
            "اشيل مادة": "انسحب من مقرر",
            "اسحب مادة": "انسحب من مقرر",
            "اسقط ماده": "انسحب من مقرر",
            "اسقط مادة": "انسحب من مقرر",
            "شيلت الماده": "انسحبت من مقرر",
            "شلت الماده": "انسحبت من مقرر",
            "شيلت ماده": "انسحبت من مقرر",
            "شلت ماده": "انسحبت من مقرر",
            "شايل ماده": "راسب في مقرر",
            "سقطت": "راسب",
            "وقعت": "راسب",
            "ادخل الامتحان": "ادخل الامتحان النهائي",
            "احضر الفاينال": "ادخل الامتحان النهائي",
            "احضر الامتحان النهائي": "ادخل الامتحان النهائي",
            "حضور الامتحان النهائي": "نسبه الحضور لدخول الامتحان النهائي",
            "احضر كام في الميه": "نسبه الحضور",
            "التسجيل في المواد": "التسجيل في المقررات",
            "عايز اسجل ماده": "شرط التسجيل في مقرر",
            "اسيب الترم": "الانسحاب الكلي من الفصل الدراسي",
            "اسيب الفصل الدراسي": "الانسحاب الكلي من الفصل الدراسي",
            "اسيب الفصل": "الانسحاب الكلي من الفصل الدراسي",
            "اسيب السمستر": "الانسحاب الكلي من الفصل الدراسي",
            "اسحب من الترم": "الانسحاب الكلي من الفصل الدراسي",
            "اسحب من الفصل الدراسي": "الانسحاب الكلي من الفصل الدراسي",
            "انسحب من الترم": "الانسحاب الكلي من الفصل الدراسي",
            "انسحب من الفصل الدراسي": "الانسحاب الكلي من الفصل الدراسي",
            "انسحب من الفصل": "الانسحاب الكلي من الفصل الدراسي",
            "اسحب الفصل": "الانسحاب الكلي من الفصل الدراسي",
            "اسحب الترم": "الانسحاب الكلي من الفصل الدراسي",
            "وقف القيد": "ايقاف القيد",
            "تجميد القيد": "ايقاف القيد",
            "غبت عن الفاينال": "تغيب عن الامتحان النهائي",
            "غبت في الفاينال": "تغيب عن الامتحان النهائي",
            "محضرتش الفاينال": "تغيب عن الامتحان النهائي",
            "missed الامتحان النهائي": "تغيب عن الامتحان النهائي",
            "من غير عذر": "دون عذر مقبول",
            "بدون عذر": "دون عذر مقبول",
            "حضور الفاينال": "نسبه الحضور لدخول الامتحان النهائي",
            "غيابي عدى 25": "تجاوزت نسبة الغياب 25%",
            "غيابي عدي 25": "تجاوزت نسبة الغياب 25%",
            "غيابي وصل 20": "وصلت نسبة الغياب 20%",
            "هعيد ماده كنت ساقط": "إعادة مقرر رسب فيه الطالب",
            "هعيد مادة كنت ساقط": "إعادة مقرر رسب فيه الطالب",
            "اعيد ماده عشان احسن": "إعادة مقرر للتحسين",
            "اعيد مادة عشان احسن": "إعادة مقرر للتحسين",
            "مشروع التخرج بيتسجل": "مشروع التخرج",
            "مادة نظري": "المقرر النظري",
            "الماده النظري": "المقرر النظري",
            "المادة النظري": "المقرر النظري",
            "سنه تالته": "level 3",
            "سنة تالته": "level 3",
            "سنه ثالثه": "level 3",
            "سنة ثالثة": "level 3",
            "ينفعلي": "يسمح لي",
            "اقدر": "يسمح لي",
            "هتتفصل": "الفصل من الكلية",
            "هتفصل": "الفصل من الكلية",
            "تفصل": "الفصل من الكلية",
            "اترفد": "الفصل من الكلية",
            "اترفض": "الفصل من الكلية",
            "يفصلوني": "الفصل من الكلية",
            "الفصل من الدراسه": "الفصل من الكلية",
            "فصل من الكليه": "الفصل من الكلية",
            "فصل من الكلية": "الفصل من الكلية",
            "فرصه اخيره": "فرصة إضافية ونهائية",
            "فرصه اخيرة": "فرصة إضافية ونهائية",
            "اخر فرصه": "فرصة إضافية ونهائية",
            "آخر فرصه": "فرصة إضافية ونهائية",
            "فرصة اخيرة": "فرصة إضافية ونهائية",
            "تظلم": "التظلمات الطلابية",
            "اتظلم": "التظلمات الطلابية",
            "اعمل تظلم": "التظلمات الطلابية",
            "شروط القبول": "شروط القبول",
            "شروط التحويل": "شروط التحويل",
            "شؤون الخريجين": "شؤون الخريجين",
            "شئون الخريجين": "شؤون الخريجين",
            "مرتبه الشرف": "مرتبة الشرف",
            "نتيجه": "نتيجة",
            "يعني ايه": "معنى",
            "يعنى ايه": "معنى",
            "معني": "معنى",
            "التقدير العام بتاعي": "التقدير العام",
            "تقدير عام": "التقدير العام",
            "تصنيفي": "التقدير العام",
            "التراقمي": "التراكمي",
            "نظم تقديرات الكليه": "نظام تقديرات الكلية",
            "نظام تقديرات الكليه": "نظام تقديرات الكلية",
            "مقررات النجاح و الرسوب": "مقررات النجاح والرسوب",
            "مقررات النجاح والرسوب": "مقررات النجاح والرسوب",
            "لو انا": "اذا كان الطالب",
            "انا": "الطالب",
        }
        for old, new in replacements.items():
            q = q.replace(old, new)
        q = q.replace("الامتحالطالبت", "الامتحانات")
        return re.sub(r"\s+", " ", q).strip()

    @classmethod
    def _refers_to_asking_student(cls, question: str) -> bool:
        """Detect when the question is phrased from the student's own perspective."""
        normalized = cls._normalize_question(question)
        return any(
            phrase in normalized
            for phrase in (
                "انا", "لو انا", "اقدر", "ينفعلي", "مسموحلي", "ليا",
                "my", "can i", "am i allowed", "if i", "for me",
            )
        )

    @classmethod
    def _build_retrieval_prompt(cls, question: str) -> str:
        """Provide the model with both the original question and a normalized retrieval gloss."""
        normalized = cls._normalize_egyptian_question(question)
        formal = cls._formalize_for_doc_retrieval(question)
        search_hints = ", ".join(cls._expanded_search_terms(question)[:18])
        language_note = (
            "This question mixes Arabic and English academic wording; answer in Arabic."
            if cls._is_mixed_ar_en_question(question)
            else "This question is written in a single dominant language."
        )
        perspective = (
            "Interpret student-related rules as applying to the asking student."
            if cls._refers_to_asking_student(question)
            else "Answer the regulation as written in the document."
        )
        return (
            f"Student question:\n{question}\n\n"
            f"{strict_language_instruction(question)}\n\n"
            f"Normalized retrieval form:\n{normalized}\n\n"
            f"Formal document-style retrieval form:\n{formal}\n\n"
            f"Search hints:\n{search_hints}\n\n"
            f"Language note:\n{language_note}\n\n"
            f"Interpretation note:\n{perspective}"
        )

    @staticmethod
    def _is_mixed_ar_en_question(question: str) -> bool:
        """Detect questions that mix Arabic script with English academic terms."""
        text = question or ""
        has_ar = bool(re.search(r"[\u0600-\u06FF]", text))
        has_en = bool(re.search(r"[A-Za-z]", text))
        return has_ar and has_en

    @classmethod
    def _formalize_for_doc_retrieval(cls, question: str) -> str:
        """Rewrite colloquial student wording into formal regulation-style Arabic for retrieval only."""
        q = cls._normalize_egyptian_question(question)

        if "شروط التخرج" in q or "عدد الساعات اللازمة للتخرج" in q:
            return "ما شروط التخرج والحصول على درجة البكالوريوس وعدد الساعات المعتمدة المطلوبة؟"
        if "نظام الامتحانات" in q or ("الامتحانات" in q and "النجاح" in q):
            return "ما نظام الامتحانات والنهاية العظمى 100 درجة والنهاية الصغرى للنجاح 50 درجة؟"
        if "لغة التدريس" in q:
            return "ما لغة التدريس في الكلية؟"
        if "نظام الدراسة" in q or ("الدراسة" in q and "نظام" in q):
            return "ما نظام الدراسة في الكلية من حيث الساعات المعتمدة وفصل الخريف وفصل الربيع والفصل الصيفي؟"
        if "المدة القصوى للدراسة" in q:
            return "ما المدة القصوى للدراسة في الكلية وعدد الفصول النظامية المستبعد منها إيقاف القيد؟"
        if "تعريف الساعة المعتمدة" in q:
            return "ما تعريف الساعة المعتمدة وساعة المحاضرة والتمرين أو المعمل؟"
        if "الحد الأدنى للتخرج" in q:
            return "ما الحد الأدنى للتخرج والحصول على درجة البكالوريوس بالسنوات والفصول النظامية؟"
        if "الانتقال بين المستويات" in q or any(level in q for level in ("freshman", "sophomore", "junior", "senior")):
            return "ما ضوابط الانتقال بين المستويات Freshman وSophomore وJunior وSenior حسب الساعات المجتازة؟"
        if "الحد الأدنى للتسجيل" in q:
            return "ما الحد الأدنى للتسجيل في فصل الخريف أو الربيع من الساعات المعتمدة؟"
        if "الساعات المسجلة" in q and ("cgpa" in q or "الحد الأقصى" in q or "الحد الاقصي" in q):
            return "ما الحد الأقصى للساعات المسجلة حسب CGPA؟"
        if ("انسحب من مقرر" in q or "ينسحب من مقرر" in q) and ("لحد امتي" in q or "لحد امتى" in q):
            return "حتى متى يحق للطالب الانسحاب من مقرر بعد موافقة المرشد الأكاديمي؟"
        if "انسحب من مقرر" in q or "ينسحب من مقرر" in q:
            return "ما قواعد الانسحاب من مقرر وتقدير W والموعد المحدد للانسحاب؟"
        if "الانسحاب الكلي من الفصل الدراسي" in q or "ايقاف القيد" in q:
            return "ما قواعد إيقاف القيد والانسحاب الكلي من الفصل الدراسي؟"
        if "تقدير غير مكتمل" in q or "غير مكتمل" in q or "incomplete" in q:
            return "ما قواعد تقدير غير مكتمل I عند عدم حضور الامتحان النهائي؟"
        if ("دون عذر" in q or "بدون عذر" in q or "من غير عذر" in q) and "الامتحان النهائي" in q:
            return "ماذا يحدث إذا تغيب الطالب عن الامتحان النهائي دون عذر مقبول؟"
        if "عذر قهري" in q and "الامتحان النهائي" in q:
            return "ماذا يحدث إذا تغيب الطالب عن الامتحان النهائي بعذر قهري مقبول؟"
        if ("تغيب" in q or "غاب" in q or "غياب" in q or "fa" in q or "abs" in q) and "الامتحان النهائي" in q:
            return "ما قواعد الغياب عن الامتحان النهائي بعذر أو بدون عذر وتقديرات FA وAbs وI؟"
        if "التسجيل في المقررات" in q and ("لحد امتي" in q or "لحد امتى" in q or "مفتوح" in q):
            return "حتى متى يستمر التسجيل في المقررات؟"
        if "شرط التسجيل في مقرر" in q or ("التسجيل" in q and "مقرر" in q):
            return "ما شرط التسجيل في مقرر من حيث اجتياز المتطلبات السابقة؟"
        if ("الحذف" in q or "الاضافه" in q) and ("لحد امتي" in q or "لحد امتى" in q or "اخرهم" in q):
            return "حتى متى يسمح بالحذف والإضافة؟"
        if ("الفصل الدراسي النظامي" in q or "الترم العادي" in q) and ("كام اسبوع" in q or "مدته" in q or "مده" in q):
            return "ما مدة الفصل الدراسي النظامي بالأسبوع؟"
        if ("الفصل الصيفي" in q or "الصيفي" in q) and ("كام اسبوع" in q or "مدته" in q or "مده" in q):
            if any(term in q for term in ("كام ساعه", "كم ساعه", "الحد الاقصي", "الحد الاقصى", "تسجيل")):
                return "ما مدة الفصل الصيفي والحد الأقصى للتسجيل فيه وهل هو اختياري؟"
            return "ما مدة الفصل الصيفي بالأسبوع؟"
        if ("الحضور" in q or "احضر كام في الميه" in q) and "الامتحان النهائي" in q:
            return "ما نسبة الحضور المطلوبة لدخول الامتحان النهائي؟"
        if "غياب" in q and "25" in q:
            return "ماذا يحدث إذا تجاوزت نسبة غياب الطالب 25%؟"
        if "نسبه الحضور" in q or "نسبة الحضور" in q or "attendance" in q:
            return "ما قواعد المواظبة على الحضور ونسبة الحضور المطلوبة لدخول الامتحان النهائي؟"
        if "وصلت نسبة الغياب 20" in q or ("غياب" in q and "20" in q):
            return "متى يوجه إنذار للطالب إذا وصلت نسبة غيابه في المقرر إلى 20%؟"
        if "إعادة مقرر رسب فيه الطالب" in q or ("اعادة مقرر" in q and "رسب" in q):
            return "ما قواعد إعادة مقرر رسب فيه الطالب والحد الأعلى المحتسب 83 أي أعلى درجة في B؟"
        if "إعادة مقرر للتحسين" in q or "تحسين" in q:
            return "ما قواعد إعادة مقرر سبق أن نجح فيه الطالب لتحسين معدله والحد الأقصى 3 مقررات؟"
        if "تجنب الفصل" in q and ("إعادة مقرر" in q or "اعاده مقرر" in q or "cgpa" in q):
            return "ما قواعد إعادة مقرر سبق أن نجح فيه الطالب لتجنب الفصل إذا كان CGPA أقل من 2؟"
        if "التعليم الهجين" in q or "hybrid" in q:
            return "ما قاعدة تدريس المقررات بنمط التعليم الهجين بنسبة 60% وجها لوجه و40% عن بعد؟"
        if "مشروع التخرج" in q:
            return "ما قواعد مشروع التخرج ونسبة الأعمال الفصلية ولجنة المناقشة وشرط اجتياز 70% من الساعات؟"
        if "المقرر النظري" in q:
            return "ما توزيع درجات المقرر النظري وشرط 30% من الامتحان النهائي التحريري؟"
        if "توزيع درجات" in q and ("تطبيقات" in q or "عملي" in q or "practical" in q):
            return "ما توزيع درجات المقرر الذي يحتوي على تطبيقات عملية وشرط 30% من الامتحان النهائي التحريري؟"
        if "توزيع درجات" in q:
            return "ما توزيع درجات المقرر النظري والمقرر الذي يحتوي على تطبيقات عملية؟"
        if "الفصل من الكليه" in q or ("الفصل" in q and "الكليه" in q and any(term in q for term in ("امتي", "امتى", "متي", "حالات"))):
            return "ما حالات الفصل من الكلية ومتى يفصل الطالب من الدراسة؟"
        if "فرصه اضافيه ونهائيه" in q or ("80" in q and ("الفصل من الكليه" in q or "فرصه" in q or "الساعات" in q)):
            return "متى يجوز منح الطالب المعرض للفصل فرصة إضافية ونهائية إذا كان قد اجتاز 80% من الساعات اللازمة للتخرج؟"
        if "cgpa" in q and "1" in q and "2" in q and "اقل" in q:
            return "كم ساعة معتمدة يسمح بها للطالب إذا كان CGPA من 1 إلى أقل من 2؟"
        if "انذار اكاديمي" in q or ("cgpa" in q and "اقل من 2" in q):
            return "متى يحصل الطالب على إنذار أكاديمي إذا كان CGPA أقل من 2؟"
        if "مرتبة الشرف" in q:
            return "ما شروط الحصول على مرتبة الشرف عند التخرج؟"
        if any(phrase in q for phrase in ("التظلمات الطلابيه", "التظلمات الطلابية")) and any(term in q for term in ("مهله", "موعد", "قد ايه", "امتي", "امتى", "اسبوع")):
            return "ما موعد التظلم من نتيجة الامتحان وكيف يتم إبلاغ الطالب بنتيجة التظلم؟"
        if any(phrase in q for phrase in ("التظلمات الطلابيه", "التظلمات الطلابية")) or ("نتيجه" in q and any(term in q for term in ("مهله", "موعد", "قد ايه", "امتي", "امتى"))):
            return "ما موعد التظلم من نتيجة الامتحان وكيف يتم إبلاغ الطالب بنتيجة التظلم؟"
        if "مقررات النجاح والرسوب" in q:
            return "ما تقديرات مقررات النجاح والرسوب بدون ساعات معتمدة مثل AU وP وF وW وAbs وI؟"
        if "جدول تقديرات" in q or "grade scale" in q:
            return "ما جدول تقديرات ونقاط المقررات ذات الساعات المعتمدة من A+ إلى F؟"
        if "التقدير العام" in q and ("cgpa" in q or "المعدل التراكمي" in q or "3.5" in q):
            return "ما التقدير العام المقابل للمعدل التراكمي المجمع CGPA؟"
        if "شروط القبول" in q:
            return "ما شروط القبول بكلية الذكاء الاصطناعي؟"
        if "شروط التحويل" in q:
            return "ما شروط التحويل لكلية الذكاء الاصطناعي ومعادلة المقررات؟"
        if "شؤون الخريجين" in q:
            return "ما خدمات قسم شؤون الخريجين؟"
        if "مواصفات خريج" in q:
            return "ما مواصفات خريج كلية الذكاء الاصطناعي من حيث حل المشكلات والعمل الجماعي والتعلم الذاتي؟"
        if "نظام تقديرات الكليه" in q and "المواد" in q:
            return "ما الفرق بين جدول تقديرات ونقاط المقررات ذات الساعات المعتمدة والتقدير العام ومقررات النجاح والرسوب بدون ساعات معتمدة؟"
        if "المعدل التراكمي" in q and any(term in q for term in ("بيتحسب", "ازاي", "كيف")):
            return "كيف يتم حساب المعدل التراكمي المجمع CGPA؟"
        if "معنى" in q and any(symbol in q for symbol in ("a+", "a-", "b+", "b-", "c+", "c-", "d+", "d-", "f", "abs", "con", " i ", " w ")):
            return "ما معنى رموز التقديرات مثل A+ وB+ وF وAbs وI وW وCon في نظام التقييم؟"
        if ("نظام التقديرات" in q or "جدول التقديرات" in q) and any(symbol in q for symbol in ("a+", "b+", "f")):
            return "ما معنى رموز التقديرات مثل A+ وB+ وF في نظام التقييم؟"
        if "الامتحان النهائي التحريري" in q and ("شرط النجاح" in q or "النجاح" in q):
            return "ما شرط النجاح في الامتحان النهائي التحريري؟"
        if "cgpa" in q and "2" in q and "3" in q and "اقل" in q:
            return "كم ساعة معتمدة يسمح بها للطالب إذا كان CGPA من 2 إلى أقل من 3؟"
        if ("cgpa" in q or "معدل" in q) and "اقل من 1" in q:
            return "كم ساعة معتمدة يسمح بها للطالب إذا كان CGPA أقل من 1؟"
        if "الفصل الصيفي" in q and ("كام ساعه" in q or "اسجل كام ساعه" in q):
            return "ما الحد الأقصى للتسجيل في الفصل الصيفي من الساعات المعتمدة؟"
        if (
            "مواد" in q
            and "الفصل الدراسي الاول" in q
            and ("level 3" in q or "سنه تالته" in q or "سنة تالته" in q or "سنه ثالثه" in q or "سنة ثالثة" in q)
            and ("artificial intelligence" in q or "ذكاء اصطناعي" in q)
        ):
            return "ما مواد الفصل الدراسي الأول للمستوى الثالث في برنامج الذكاء الاصطناعي؟"

        return q

    def status(self) -> Dict[str, Any]:
        """Return OpenAI vector-store RAG status without exposing secrets."""
        return {
            "provider": "openai_file_search",
            "initialized": self.chain is not None,
            "openai_configured": bool(_env("OPENAI_API_KEY")),
            "vector_store_configured": bool(self.vector_store_id),
            "vector_store_id": self.vector_store_id,
            "retrieval_k": RETRIEVE_K,
            "source_file": REGULATIONS_SOURCE,
            "source_exists": os.path.exists(REGULATIONS_SOURCE),
            "selected_source_file": REGULATIONS_SOURCE,
            "selected_source_exists": os.path.exists(REGULATIONS_SOURCE),
            "clean_source_file": CLEAN_REGULATIONS_SOURCE,
            "clean_source_exists": os.path.exists(CLEAN_REGULATIONS_SOURCE),
            "extracted_source_file": EXTRACTED_REGULATIONS_SOURCE,
            "extracted_source_exists": os.path.exists(EXTRACTED_REGULATIONS_SOURCE),
            "last_error": self.last_error,
        }

    def rebuild(self):
        """Local rebuilds are replaced by scripts/setup_openai_vector_store.py."""
        raise RuntimeError(
            "OpenAI vector-store RAG is managed remotely. Run "
            "`python scripts/setup_openai_vector_store.py` to create or refresh "
            "the vector store, then update OPENAI_VECTOR_STORE_ID."
        )

    @staticmethod
    def _response_text(response: Any) -> str:
        """Extract text from OpenAI Responses API objects across SDK shapes."""
        output_text = getattr(response, "output_text", None)
        if output_text:
            return output_text

        parts = []
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                text = getattr(content, "text", None)
                if text:
                    parts.append(text)
        return "\n".join(parts).strip() or "I couldn't find this specific regulation in the document."

    @staticmethod
    def _is_not_found_answer(answer: str) -> bool:
        """Detect explicit file-search misses from the hosted RAG response."""
        normalized = (answer or "").strip().lower()
        return normalized in {
            "i couldn't find this specific regulation in the document.",
            "مش لاقي المعلومة دي في اللائحة.",
        }

    @classmethod
    def _should_try_local_fallback(cls, question: str, answer: str) -> bool:
        """Use local clean-text retrieval when hosted RAG misses or replies generically."""
        if cls._is_not_found_answer(answer):
            return True

        if not (answer or "").strip():
            return True

        normalized_answer = cls._normalize_for_search(answer or "")
        if not normalized_answer:
            return True

        weak_answer_markers = (
            "عاده", "غالبا", "قد تختلف", "قد يختلف", "يفضل تتاكد",
            "تتاكد", "راجع الكليه", "راجع الجامعه",
            "depends", "check with your faculty", "check with the academic department",
            "check the official website", "usually", "it is recommended to check",
        )
        if any(marker in normalized_answer for marker in weak_answer_markers):
            return True

        required_markers = cls._required_detail_markers(question)
        if required_markers and not any(marker in normalized_answer for marker in required_markers):
            return True

        return False

    @classmethod
    def _required_detail_markers(cls, question: str) -> List[str]:
        """Return key numeric/symbolic details expected for specific regulation questions."""
        normalized = cls._normalize_for_search(cls._normalize_egyptian_question(question))
        markers: List[str] = []

        if any(term in normalized for term in ("تخرج", "graduate")) and any(term in normalized for term in ("ساع", "credit hours", "عدد الساعات")):
            markers.extend(("144",))
        if "شروط التخرج" in normalized:
            markers.extend(("cgpa", "2", "المقررات بدون ساعات", "مستلزمات"))
        if "لغه التدريس" in normalized:
            markers.extend(("الانجليزيه",))
        if "نظام الدراسه" in normalized or ("الدراسه" in normalized and "نظام" in normalized):
            markers.extend(("الساعات المعتمده", "الخريف", "الربيع", "الصيفي", "17", "8"))
        if "المده القصوي للدراسه" in normalized:
            markers.extend(("ثماني", "16", "ايقاف القيد"))
        if "تعريف الساعه المعتمده" in normalized:
            markers.extend(("وحده قياس", "المحاضره", "المعمل", "نصف"))
        if "الحد الادني للتخرج" in normalized:
            markers.extend(("ثلاث", "سته", "فصول"))
        if "الانتقال بين المستويات" in normalized or any(level in normalized for level in ("freshman", "sophomore", "junior", "senior")):
            markers.extend(("freshman", "34", "sophomore", "73", "junior", "109", "senior", "144"))
        if "الحد الادني للتسجيل" in normalized:
            markers.extend(("9", "الخريف", "الربيع"))
        if "الساعات المسجله" in normalized and "cgpa" in normalized:
            markers.extend(("21", "18", "15", "12", "cgpa"))
        if "التسجيل في المقررات" in normalized and any(term in normalized for term in ("لحد", "امتي", "امتى", "مفتوح")):
            markers.extend(("الثاني", "2"))
        if ("الحذف" in normalized or "الاضافه" in normalized) and any(term in normalized for term in ("لحد", "امتي", "امتى", "متي", "اخرهم")):
            markers.extend(("الثالث", "3"))
        if "الفصل الدراسي النظامي" in normalized or "regular semester" in normalized:
            markers.extend(("17",))
        if "الفصل الصيفي" in normalized or "summer semester" in normalized:
            if any(term in normalized for term in ("ساع", "credit", "max", "maximum", "تسجيل", "اسجل")):
                markers.extend(("9",))
            if any(term in normalized for term in ("اسبوع", "weeks", "duration", "مده", "مدته")):
                markers.extend(("8",))
        if any(term in normalized for term in ("اقل درجه للنجاح", "minimum passing", "minimum grade to pass")):
            markers.extend(("50",))
        if "حضور" in normalized or "attendance" in normalized:
            markers.extend(("75",))
        if "الامتحان النهايي" in normalized and any(term in normalized for term in ("دون عذر", "بدون عذر", "من غير عذر")):
            markers.extend(("fa", "راسب"))
        elif "الامتحان النهايي" in normalized and "عذر قهري" in normalized:
            markers.extend(("i", "60"))
        elif "غياب" in normalized or "absence" in normalized:
            markers.extend(("25", "fa", "abs", "i"))
            if "25" in normalized:
                markers.extend(("حرمان", "صفر"))
        if ("انذار" in normalized or "academic warning" in normalized) and "غياب" not in normalized:
            markers.extend(("cgpa", "2"))
        if "انسحب من مقرر" in normalized or "withdraw from a course" in normalized:
            markers.extend(("9", "التاسع", "w"))
        if "الانسحاب الكلي" in normalized or "ايقاف القيد" in normalized or "semester withdrawal" in normalized:
            markers.extend(("شهر", "4", "6"))
        if "غير مكتمل" in normalized or "incomplete" in normalized:
            markers.extend(("i", "60", "w", "منسحب"))
        if "لغه التدريس" in normalized:
            markers.extend(("الانجليزيه",))
        if "شروط التحويل" in normalized or "transfer" in normalized:
            markers.extend(("التحويل", "مقاصه", "cgpa", "2", "60"))
        if "شروط القبول" in normalized or "admission" in normalized:
            markers.extend(("علمي", "رياضيات", "علوم", "pre mathematic"))
        if "مواصفات خريج" in normalized:
            markers.extend(("المشكلات الحاسوبيه", "التعلم الذاتي", "اصحاب العمل", "فرق", "اخلاقيه"))
        if "مرتبه الشرف" in normalized or "مرتبة الشرف" in normalized or "honor" in normalized:
            markers.extend(("cgpa", "3", "اربع", "ثمانيه", "رسب", "حرم"))
        if "الفصل من الكليه" in normalized or "dismissal" in normalized:
            markers.extend(("4", "6", "80"))
        if "التظلمات" in normalized or "appeal" in normalized or "grievance" in normalized:
            markers.extend(("اسبوع", "week"))
        if "وصلت نسبه الغياب 20" in normalized or ("غياب" in normalized and "20" in normalized):
            markers.extend(("20", "انذار"))
        if "انذار" in normalized and "غياب" in normalized:
            markers.extend(("20", "انذار"))
        if "cgpa" in normalized and "1" in normalized and "2" in normalized and any(term in normalized for term in ("اسجل", "ساعه", "ساعات")):
            markers.extend(("15", "cgpa"))
        if "اعاده مقرر رسب" in normalized:
            markers.extend(("رسب", "83", "b"))
        if "تجنب الفصل" in normalized and "اعاده مقرر" in normalized:
            markers.extend(("تجنب الفصل", "cgpa", "2", "83", "b"))
        if "اعاده مقرر للتحسين" in normalized or "تحسين" in normalized:
            markers.extend(("تحسين", "83", "b", "3"))
        if "التعليم الهجين" in normalized or "hybrid" in normalized:
            markers.extend(("60", "40", "الهجين"))
        if "مشروع التخرج" in normalized:
            markers.extend(("60", "40", "70", "خريف", "ربيع"))
        if "المقرر النظري" in normalized:
            markers.extend(("40", "20", "30"))
        if "توزيع درجات" in normalized and ("تطبيقات" in normalized or "عملي" in normalized or "practical" in normalized):
            markers.extend(("40", "20", "التطبيقات", "30"))
        if "جدول تقديرات" in normalized or "grade scale" in normalized:
            markers.extend(("a", "96", "f", "50"))
        if "مقررات النجاح والرسوب" in normalized or "pass fail" in normalized:
            markers.extend(("au", "p", "f", "w", "abs", "i"))
        if "التقدير العام" in normalized:
            markers.extend(("ممتاز", "جيد", "مقبول", "ضعيف", "3 5", "3.5"))
        if "نظام الامتحانات" in normalized or ("الامتحانات" in normalized and "النجاح" in normalized):
            markers.extend(("100", "50"))

        symbol_markers = re.findall(r"\b(?:a\+|a-|b\+|b-|c\+|c-|d\+|d-|f|w|i|abs|con|cgpa|fa)\b", normalized)
        markers.extend(symbol_markers)
        return sorted(set(cls._normalize_for_search(marker) for marker in markers if marker))

    def _local_regulation_fallback(self, question: str) -> str:
        """Search the selected regulations text locally when hosted file_search misses."""
        chunks = self._local_regulation_chunks()
        ranked = self._rank_local_chunks(question, chunks)
        if not ranked:
            return ""

        best = ranked[:3]
        header = "من اللائحة المتاحة عندي محليًا:" if should_respond_arabic(question) else "From the local regulations text I have:"
        lines = [header]
        for chunk in best:
            snippet = self._condense_chunk(chunk["text"], question)
            if chunk["page"] == 0:
                page_label = "المقدمة" if should_respond_arabic(question) else "Intro"
            else:
                page_label = f"صفحة {chunk['page']}" if should_respond_arabic(question) else f"Page {chunk['page']}"
            lines.append(f"- {page_label}: {snippet}")
        return "\n".join(lines)

    @classmethod
    @lru_cache(maxsize=1)
    def _local_regulation_chunks(cls) -> tuple:
        """Load searchable chunks from the selected regulations markdown."""
        chunks = []

        for excerpt in REGULATIONS_CLEAN_EXCERPTS:
            chunks.append({
                "page": excerpt["page"],
                "text": excerpt["text"].strip(),
                "normalized": cls._normalize_for_search(excerpt["text"]),
            })

        if os.path.exists(REGULATIONS_SOURCE):
            with open(REGULATIONS_SOURCE, "r", encoding="utf-8") as handle:
                raw = handle.read()
            for page, text in cls._split_markdown_pages(raw):
                if REGULATIONS_SOURCE == CLEAN_REGULATIONS_SOURCE:
                    combined = text.strip()
                else:
                    combined = cls.__new__(cls)._repair_arabic_extraction(text).strip()
                if combined:
                    chunks.append({
                        "page": page,
                        "text": combined,
                        "normalized": cls._normalize_for_search(combined),
                    })

        return tuple(chunks)

    @classmethod
    def _split_markdown_pages(cls, raw_text: str) -> List[tuple]:
        """Split regulations markdown into an intro chunk and page chunks."""
        raw_text = raw_text or ""
        page_heading = re.compile(r"(?m)^(?:---\s*\n)?## Page (\d+)\s*$")
        matches = list(page_heading.finditer(raw_text))
        if not matches:
            text = raw_text.strip()
            return [(0, text)] if text else []

        chunks = []
        intro = raw_text[:matches[0].start()].strip()
        if intro:
            chunks.append((0, intro))

        for index, match in enumerate(matches):
            page = int(match.group(1))
            next_start = matches[index + 1].start() if index + 1 < len(matches) else len(raw_text)
            text = raw_text[match.end():next_start].strip()
            if text:
                chunks.append((page, text))
        return chunks

    @classmethod
    def _rank_local_chunks(cls, question: str, chunks: tuple) -> List[Dict[str, Any]]:
        """Score local regulation chunks against the student question."""
        terms = cls._expanded_search_terms(question)
        normalized_question = cls._normalize_for_search(
            f"{question} {cls._normalize_egyptian_question(question)} {cls._formalize_for_doc_retrieval(question)}"
        )
        scored = []

        for chunk in chunks:
            score = 0
            normalized_text = chunk["normalized"]
            for term in terms:
                if term and term in normalized_text:
                    score += 4 if len(term) > 6 else 2
            for marker in cls._required_detail_markers(question):
                if marker and marker in normalized_text:
                    score += 6
            for phrase in (
                cls._normalize_for_search(cls._formalize_for_doc_retrieval(question)),
                cls._normalize_for_search(cls._normalize_egyptian_question(question)),
            ):
                if phrase and phrase in normalized_text:
                    score += 8
            if re.search(r"\b[A-Z]{2,4}\d{3}\b", question):
                for code in re.findall(r"\b[A-Z]{2,4}\d{3}\b", question):
                    if code.lower() in normalized_text:
                        score += 6
            shared_tokens = {
                token for token in normalized_question.split()
                if len(token) >= 4 and token in normalized_text
            }
            score += min(len(shared_tokens), 8)
            if score >= 5:
                scored.append({**chunk, "score": score})

        scored.sort(
            key=lambda item: (item["score"], -abs(item["page"] - 40)),
            reverse=True,
        )
        return scored

    @classmethod
    def _condense_chunk(cls, text: str, question: str = "") -> str:
        """Trim noisy page text to a short, readable snippet."""
        compact = re.sub(r"\s+", " ", text).strip()
        compact = compact.replace("Faculty of Artificial Intelligence – Student Guide", "").strip()
        compact = re.sub(r"#+\s*", "", compact)
        if question:
            terms = [term for term in cls._expanded_search_terms(question) if len(term) >= 4]
            required_markers = cls._required_detail_markers(question)
            section_matches = list(re.finditer(r"(?m)^#{2,3}\s+(.+?)\s*$", text))
            segments = []
            for index, match in enumerate(section_matches):
                end = section_matches[index + 1].start() if index + 1 < len(section_matches) else len(text)
                segments.append(text[match.start():end].strip())
            if not segments:
                segments = [
                    segment.strip()
                    for segment in re.split(r"\s+-\s+|(?<=[.؟])\s+|\s+###\s+|\s+##\s+", text)
                    if segment.strip()
                ]
            best_segment = ""
            best_score = 0
            for segment in segments:
                normalized_segment = cls._normalize_for_search(segment)
                score = sum(2 for term in terms if term in normalized_segment)
                score += sum(8 for marker in required_markers if marker in normalized_segment)
                if score > best_score:
                    best_score = score
                    best_segment = segment
            if best_segment:
                lines = [
                    line.strip(" -")
                    for line in best_segment.splitlines()
                    if line.strip(" -")
                ]
                scored_lines = []
                for index, line in enumerate(lines):
                    normalized_line = cls._normalize_for_search(line)
                    line_score = sum(2 for term in terms if term in normalized_line)
                    line_score += sum(8 for marker in required_markers if marker in normalized_line)
                    if line_score:
                        scored_lines.append((line_score, index, line))
                if scored_lines:
                    selected = sorted(
                        sorted(scored_lines, key=lambda item: item[0], reverse=True)[:8],
                        key=lambda item: item[1],
                    )
                    compact = " ".join(line for _, _, line in selected)
                else:
                    compact = re.sub(r"\s+", " ", best_segment).strip()
                compact = re.sub(r"#+\s*", "", compact)
        max_length = 900
        return compact[:max_length].rstrip() + ("..." if len(compact) > max_length else "")

    @staticmethod
    def _contains_arabic(text: str) -> bool:
        """Return True when the text includes Arabic characters."""
        return contains_arabic(text)

    def _repair_arabic_extraction(self, text: str) -> str:
        """Repair common visual-order Arabic runs for local extraction utilities/tests."""
        repaired_lines = []
        for line in text.split("\n"):
            repaired_lines.append(self._best_arabic_line_variant(line))
        return "\n".join(repaired_lines)

    def _best_arabic_line_variant(self, line: str) -> str:
        """Pick the most readable variant for Arabic text extracted in visual order."""
        if not re.search(r"[\u0600-\u06FF]", line):
            return line

        char_repaired = re.sub(
            r"[\u0600-\u06FFـ]+",
            lambda m: m.group(0).replace("ـ", "")[::-1],
            line,
        )
        tokens = char_repaired.split()
        arabic_tokens = [token for token in tokens if re.search(r"[\u0600-\u06FF]", token)]
        variants = [line, char_repaired]
        if len(arabic_tokens) >= 2:
            variants.append(" ".join(reversed(tokens)))

        return max(
            enumerate(variants),
            key=lambda item: (self._arabic_readability_score(item[1]), item[0]),
        )[1]

    @staticmethod
    def _arabic_readability_score(line: str) -> int:
        """Score known readable Arabic terms and penalize common reversed terms."""
        normalized = line.replace("ـ", "")
        score = sum(normalized.count(term) * 3 for term in READABLE_ARABIC_TERMS)
        score -= sum(normalized.count(marker) * 4 for marker in REVERSED_ARABIC_MARKERS)
        score -= len(re.findall(r"\b[\u0600-\u06FF]{1,2}\b", normalized))
        return score

    @classmethod
    def _expanded_search_terms(cls, question: str) -> List[str]:
        """Build normalized search terms and common regulation synonyms."""
        normalized = cls._normalize_for_search(cls._normalize_egyptian_question(question))
        short_academic_tokens = {"ai", "ds", "sw", "cb"}
        terms = {
            token for token in normalized.split()
            if len(token) >= 3 or token in short_academic_tokens
        }

        expansions = {
            "شروط التخرج": {"شروط", "التخرج", "144", "cgpa", "2", "البكالوريوس", "الساعات المعتمدة"},
            "التخرج": {"شروط", "التخرج", "144", "cgpa", "2", "البكالوريوس"},
            "للتخرج": {"شروط", "التخرج", "144", "cgpa", "2", "البكالوريوس", "الساعات المعتمدة"},
            "نظام الدراسة": {"نظام", "الدراسة", "الساعات المعتمدة", "الخريف", "الربيع", "الصيفي", "17", "8"},
            "نظام الدراسه": {"نظام", "الدراسة", "الساعات المعتمدة", "الخريف", "الربيع", "الصيفي", "17", "8"},
            "الخريجين": {"شؤون", "الخريجين", "شهادات", "المحتوى العلمي", "التقديرات"},
            "شؤون الخريجين": {"شؤون", "الخريجين", "شهادات", "اعتماد", "المحتوى العلمي", "التقديرات"},
            "شروط القبول": {"شروط", "القبول", "الثانوية العامة", "علمي", "رياضيات", "علوم", "pre-mathematic"},
            "شروط التحويل": {"شروط", "التحويل", "مقاصة", "معادلة", "المقررات", "cgpa", "2", "60"},
            "نظام الامتحانات": {"نظام", "الامتحانات", "100", "50", "النهاية العظمى", "النهاية الصغرى"},
            "غاب": {"غياب", "تغيب", "حضور", "النهائي", "عذر", "مقبول"},
            "يغيب": {"غياب", "تغيب", "حضور", "النهائي", "عذر", "مقبول"},
            "محضرش": {"غياب", "حضور", "النهائي", "عذر", "مقبول"},
            "تغيب": {"غياب", "تغيب", "الامتحان", "النهائي", "عذر", "fa", "abs", "غير مكتمل"},
            "عذر": {"عذر", "مقبول", "قهري", "غير مكتمل", "مكتمل"},
            "فاينال": {"النهائي", "النهايي", "الامتحان", "عذر", "مقبول"},
            "الامتحان النهائي": {"الامتحان", "النهائي", "غياب", "حضور", "عذر", "fa", "abs", "i"},
            "ميد": {"منتصف", "الفصل", "20"},
            "ميدترم": {"منتصف", "الفصل", "20"},
            "الحضور": {"حضور", "75", "25", "حرمان"},
            "حضور": {"حضور", "75", "25", "حرمان"},
            "نسبه الحضور": {"حضور", "75", "25", "حرمان", "الامتحان النهائي", "المواظبة"},
            "تجاوزت": {"غياب", "25", "حرمان", "انذار", "الامتحان النهائي"},
            "مكتمل": {"غير", "مكتمل", "Incomplete", "I"},
            "غير مكتمل": {"غير", "مكتمل", "i", "عذر", "قهري", "60", "الامتحان النهائي"},
            "الحد الأدنى للتسجيل": {"الحد", "الأدنى", "التسجيل", "9", "الخريف", "الربيع"},
            "الساعات المسجلة": {"الساعات", "المسجلة", "cgpa", "21", "18", "15", "12"},
            "تسجيل": {"التسجيل", "متطلباته", "اجتياز"},
            "التسجيل في المقررات": {"التسجيل", "المقررات", "الأسبوع الثاني", "نهاية الأسبوع الثاني", "الحذف", "الإضافة"},
            "الصيفي": {"الصيفي", "9", "8", "اختياري"},
            "راسب": {"راسب", "fa", "اعاده", "انسحاب"},
            "انسحب": {"انسحاب", "منسحب", "w", "مقرر", "الاسبوع التاسع", "المرشد الأكاديمي"},
            "الانسحاب": {"انسحاب", "منسحب", "w", "مقرر", "الفصل الدراسي", "ايقاف القيد"},
            "ايقاف القيد": {"ايقاف", "القيد", "الانسحاب الكلي", "الفصل الدراسي", "قبل الامتحان بشهر"},
            "مقرر": {"مقرر", "التسجيل", "متطلباته", "اجتياز"},
            "الفصل الدراسي": {"الفصل", "الدراسي", "17", "الصيفي", "8"},
            "الفصل": {"الفصل", "الكليه", "انذار", "اكاديمي", "متتاليه", "متفرقه", "80"},
            "الكليه": {"الفصل", "الكليه", "انذار", "اكاديمي"},
            "انذار اكاديمي": {"انذار", "اكاديمي", "cgpa", "اقل", "2", "الفصل الدراسي"},
            "اكاديمي": {"انذار", "اكاديمي", "cgpa", "2", "الفصل"},
            "مرتبة الشرف": {"مرتبة", "الشرف", "cgpa", "3", "جيد جدا", "اربع سنوات", "ثمانية فصول"},
            "التظلمات": {"التظلمات", "الطلابيه", "نتيجه", "اسبوع", "اعلان", "النتائج"},
            "التظلمات الطلابيه": {"التظلمات", "الطلابيه", "نتيجه", "اسبوع", "اعلان", "النتائج"},
            "التقدير": {"التقدير", "العام", "cgpa", "ممتاز", "جيد", "مقبول", "ضعيف"},
            "a+": {"a+", "96", "4", "التقدير"},
            "b+": {"b+", "84", "3.2", "التقدير"},
            "f": {"f", "50", "راسب", "التقدير"},
            "fa": {"fa", "راسب", "غياب", "الامتحان النهائي", "بدون عذر"},
            "abs": {"abs", "غياب", "النهائي", "بدون", "عذر"},
            "w": {"w", "منسحب", "انسحاب"},
            "i": {"i", "غير مكتمل", "عذر", "60", "الامتحان النهائي"},
            "con": {"con", "مستمر", "الفصل", "التالي"},
            "cgpa": {"cgpa", "المعدل التراكمي", "انذار", "اكاديمي", "التقدير العام"},
        }
        for trigger, values in expansions.items():
            if trigger in normalized:
                terms.update(cls._normalize_for_search(value) for value in values)

        return sorted(terms)

    @staticmethod
    def _normalize_for_search(text: str) -> str:
        """Normalize Arabic variants for keyword search helpers/tests."""
        replacements = {
            "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
            "ى": "ي", "ی": "ي", "ئ": "ي",
            "ؤ": "و",
            "ة": "ه", "ۀ": "ه", "ھ": "ه",
            "ـ": "",
            "ذكاء اصطناعي": "artificial intelligence",
            "ذكاء": "artificial intelligence",
            "سايبر": "cybersecurity",
            "امن سيبراني": "cybersecurity",
            "الامن السيبراني": "cybersecurity",
            "الفرقه": "level",
            "الفرقه": "level",
            "سنه": "level",
            "سنة": "level",
            "الترم": "semester",
            "ترم": "semester",
            "سمستر": "semester",
            "اول": "1",
            "اولي": "1",
            "اولى": "1",
            "اولي ": "1 ",
            "تانيه": "2",
            "تانية": "2",
            "ثانيه": "2",
            "ثانية": "2",
            "تالته": "3",
            "تالتة": "3",
            "ثالثه": "3",
            "ثالثة": "3",
            "رابعه": "4",
            "رابعة": "4",
        }
        text = text.lower()
        for old, new in replacements.items():
            text = text.replace(old, new)
        text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
        text = re.sub(r"[^\w\s٪%]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

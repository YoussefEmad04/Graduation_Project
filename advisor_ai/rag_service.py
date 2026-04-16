"""
RAG Service - Retrieval-Augmented Generation over academic regulations.

Production uses OpenAI hosted vector stores and the Responses API file_search
tool, so Vercel does not need local ChromaDB or PDF parsing dependencies.
"""

import logging
import os
import re
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# -- Configuration ---------------------------------------------------------

def _env(name: str, default: str = "") -> str:
    """Read an environment variable and trim deployment-input whitespace."""
    return (os.getenv(name, default) or "").strip()


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REGULATIONS_SOURCE = os.path.join(
    PROJECT_ROOT, "important_pdf", "RAG", "regulations_extracted.md"
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
        "page": 37,
        "text": (
            "نظام الامتحانات: النهاية العظمى لدرجات كل مقرر 100 درجة، والنهاية الصغرى للنجاح 50 درجة.\n"
            "توزيع درجات المقرر النظري: 40% لامتحان نهاية الفصل الدراسي، بشرط أن يحصل الطالب على "
            "30% من درجة الامتحان النهائي التحريري على الأقل شرطا للنجاح، و20% لامتحان منتصف الفصل "
            "الدراسي، و40% للاختبارات الدورية والأعمال الفصلية."
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
- If the student writes in Arabic, respond only in Arabic.
- If the student writes Arabizi, respond in friendly Egyptian Arabic.
- Do not mix languages in one response.

Answer rules:
- Use only retrieved file content. Do not invent regulations.
- Be precise with numbers, percentages, weeks, credit hours, and course codes.
- For study-plan tables, preserve course codes exactly. If a prerequisite is shown only as a code, return the code only.
- If the retrieved content does not contain the answer, say:
  - English: "I couldn't find this specific regulation in the document."
  - Arabic: "مش لاقي المعلومة دي في اللائحة."
- Format answers with concise bullet points.
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
                input=f"Student question:\n{question}",
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
            return self._response_text(response)
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error querying OpenAI vector store RAG: {e}")
            return f"Error querying regulations: {str(e)}"

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
        normalized = cls._normalize_for_search(question)
        short_academic_tokens = {"ai", "ds", "sw", "cb"}
        terms = {
            token for token in normalized.split()
            if len(token) >= 3 or token in short_academic_tokens
        }

        expansions = {
            "غاب": {"غياب", "تغيب", "حضور", "النهائي", "عذر", "مقبول"},
            "يغيب": {"غياب", "تغيب", "حضور", "النهائي", "عذر", "مقبول"},
            "محضرش": {"غياب", "حضور", "النهائي", "عذر", "مقبول"},
            "عذر": {"عذر", "مقبول", "قهري", "غير مكتمل", "مكتمل"},
            "فاينال": {"النهائي", "النهايي", "الامتحان", "عذر", "مقبول"},
            "ميد": {"منتصف", "الفصل", "20"},
            "ميدترم": {"منتصف", "الفصل", "20"},
            "الحضور": {"حضور", "75", "25", "حرمان"},
            "حضور": {"حضور", "75", "25", "حرمان"},
            "مكتمل": {"غير", "مكتمل", "Incomplete", "I"},
            "تسجيل": {"التسجيل", "متطلباته", "اجتياز"},
            "الصيفي": {"الصيفي", "9", "اختياري"},
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
        }
        text = text.lower()
        for old, new in replacements.items():
            text = text.replace(old, new)
        text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
        text = re.sub(r"[^\w\s٪%]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

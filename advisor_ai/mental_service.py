"""
Mental Support Service — LLM-powered academic motivation and guidance.
Detects emotional distress keywords and provides personalized supportive responses.
Also handles major selection recommendations (AI vs Cybersecurity).
NO therapy, NO medical advice — academic support only.
LangSmith tracing enabled via @traceable decorator.
"""

import os
import logging
from typing import Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable

from advisor_ai.constants import (
    MENTAL_KEYWORDS,
    MAJOR_KEYWORDS,
    MENTAL_SYSTEM_PROMPT,
    MAJOR_SYSTEM_PROMPT
)

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class MentalSupportService:
    """Provides LLM-powered academic motivation and major recommendation."""

    def __init__(self):
        self.llm = None
        self.mental_chain = None
        self.major_chain = None

        if os.getenv("OPENAI_API_KEY"):
            self.llm = ChatOpenAI(
                model=os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini"),
                temperature=0.7,  # Warmer for empathetic responses
            )

            self.mental_chain = ChatPromptTemplate.from_messages([
                ("system", MENTAL_SYSTEM_PROMPT),
                ("human", "{question}"),
            ]) | self.llm

            self.major_chain = ChatPromptTemplate.from_messages([
                ("system", MAJOR_SYSTEM_PROMPT),
                ("human", "{question}"),
            ]) | self.llm

            logger.info("Mental Support Service initialized (LLM-powered)")
        else:
            logger.warning("OPENAI_API_KEY is not configured; Mental Support Service will use fallback responses")

    def is_triggered(self, message: str) -> bool:
        """Check if the message contains emotional distress keywords."""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in MENTAL_KEYWORDS)

    def is_major_query(self, message: str) -> bool:
        """Check if the student is asking about choosing a major."""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in MAJOR_KEYWORDS)

    @traceable(name="Mental Support Response", run_type="chain")
    def get_response(self, message: str, student_level: Optional[int] = None) -> str:
        """
        Generate a personalized, level-aware supportive response using the LLM.
        Detects language automatically and responds accordingly.
        """
        if not self.mental_chain:
            return self._fallback_response(message)

        try:
            # Inject level context into the question for the LLM
            prompt_message = message
            if student_level:
                prompt_message = (
                    f"[Student is Level {student_level}]\n{message}"
                )

            result = self.mental_chain.invoke({"question": prompt_message})
            return result.content
        except Exception as e:
            logger.error(f"LLM error, falling back: {e}")
            return self._fallback_response(message)

    @traceable(name="Major Recommendation", run_type="chain")
    def get_major_recommendation(self, message: str) -> str:
        """
        Generate a major recommendation (AI vs Cybersecurity) using the LLM.
        """
        if not self.major_chain:
            return (
                "Both AI and Cybersecurity are excellent programs at ERU! "
                "Please visit your academic advisor for personalized guidance."
            )

        try:
            result = self.major_chain.invoke({"question": message})
            return self._normalize_major_response(result.content, message)
        except Exception as e:
            logger.error(f"LLM error on major recommendation: {e}")
            return (
                "Both AI and Cybersecurity are excellent programs at ERU! "
                "Please visit your academic advisor for personalized guidance."
            )

    @staticmethod
    def _normalize_major_response(response: str, message: str) -> str:
        """Keep official major names explicit in comparisons, including Arabic replies."""
        content = (response or "").strip()
        if not content:
            return "Both Artificial Intelligence (AI) and Cybersecurity are excellent programs at ERU."

        has_arabic = any("\u0600" <= c <= "\u06FF" for c in message)
        lower = content.lower()
        has_ai = "artificial intelligence" in lower or "(ai)" in lower or " ai" in lower
        has_cyber = "cybersecurity" in lower

        if has_ai and has_cyber:
            if has_arabic and ("الذكاء الاصطناعي" not in content or "الأمن السيبراني" not in content):
                prefix = (
                    "مقارنة سريعة بين الذكاء الاصطناعي Artificial Intelligence (AI) "
                    "والأمن السيبراني Cybersecurity:\n\n"
                )
                return prefix + content
            return content

        prefix = (
            "مقارنة سريعة بين الذكاء الاصطناعي Artificial Intelligence (AI) "
            "والأمن السيبراني Cybersecurity:\n\n"
            if has_arabic else
            "Quick comparison between Artificial Intelligence (AI) and Cybersecurity:\n\n"
        )
        return prefix + content

    @staticmethod
    def _fallback_response(message: str) -> str:
        """Fallback if LLM is unavailable."""
        # Detect language
        has_arabic = any('\u0600' <= c <= '\u06FF' for c in message)
        if has_arabic:
            return (
                "**دعم أكاديمي**\n\n"
                "أنا فاهم إنك بتمر بوقت صعب، وده طبيعي جداً.\n\n"
                "- حاول تنظم وقتك وترتب أولوياتك.\n"
                "- خد بريك كل شوية، العقل المرتاح بيذاكر أحسن.\n"
                "- اتكلم مع الدكتور أو المعيد، ده دورهم يساعدوك.\n"
                "- قسّم المذاكرة لأجزاء صغيرة، خطوة خطوة.\n\n"
                "لو حاسس إن الموضوع أكبر من كده، كلّم خدمات الإرشاد في الجامعة."
            )
        return (
            "**Academic support**\n\n"
            "I understand you're going through a tough time, and that's completely normal.\n\n"
            "- Organize your time and prioritize your tasks.\n"
            "- Take breaks so your mind has time to reset.\n"
            "- Talk to your professor or TA, they are there to help.\n"
            "- Break your study into small chunks, step by step.\n\n"
            "If you're experiencing severe distress, please reach out to university counseling services."
        )

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
        try:
            result = self.major_chain.invoke({"question": message})
            return result.content
        except Exception as e:
            logger.error(f"LLM error on major recommendation: {e}")
            return (
                "Both AI and Cybersecurity are excellent programs at ERU! "
                "Please visit your academic advisor for personalized guidance."
            )

    @staticmethod
    def _fallback_response(message: str) -> str:
        """Fallback if LLM is unavailable."""
        # Detect language
        has_arabic = any('\u0600' <= c <= '\u06FF' for c in message)
        if has_arabic:
            return (
                "🌟 أنا فاهم إنك بتمر بوقت صعب، وده طبيعي جداً.\n\n"
                "• حاول تنظم وقتك وترتب أولوياتك\n"
                "• خد بريك كل شوية — العقل المرتاح بيذاكر أحسن\n"
                "• اتكلم مع الدكتور أو المعيد — ده شغلهم يساعدوك\n"
                "• قسّم المذاكرة لأجزاء صغيرة — خطوة خطوة\n\n"
                "إنت وصلت لحد هنا، وده معناه إنك تقدر تكمل! 💪\n\n"
                "⚠️ لو حاسس إن الموضوع أكبر من كده، كلّم خدمات الإرشاد في الجامعة."
            )
        return (
            "🌟 I understand you're going through a tough time, and that's completely normal.\n\n"
            "• Organize your time and prioritize your tasks\n"
            "• Take breaks — a rested mind learns 10x better\n"
            "• Talk to your professor or TA — they're here to help\n"
            "• Break your study into small chunks — step by step\n\n"
            "You've made it this far, which means you CAN keep going! 💪\n\n"
            "⚠️ If you're experiencing severe distress, please reach out to "
            "university counseling services."
        )

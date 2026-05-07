"""Language helpers for strict response-language selection."""

import re


ARABIZI_MARKERS = (
    "ezayak", "ezzayak", "3amel", "salam", "ahlan",
    "kam sa3a", "kam saa", "ta5arog", "takharog", "lawaye7", "lawe7a",
    "a7awel", "asheil", "asahel", "madda", "mada", "mawade", "mawad",
    "btfta7", "betfta7", "bt2fel", "bet2fel", "lazem a5od", "akhod eh",
    "mesh", "msh", "ader", "ta3ban", "zah2an", "makhno2", "khaief", "5ayef",
    "a5tar", "akhtar", "me7tar", "mehtar",
)


def contains_arabic(text: str) -> bool:
    """Return True when text contains Arabic-script characters."""
    return bool(re.search(r"[\u0600-\u06FF]", text or ""))


def contains_arabizi(text: str) -> bool:
    """Return True for common Latin-script Egyptian Arabic/Arabizi markers."""
    normalized = re.sub(r"\s+", " ", (text or "").lower()).strip()
    return any(marker in normalized for marker in ARABIZI_MARKERS)


def should_respond_arabic(question: str) -> bool:
    """Arabic, Egyptian Arabic, Arabizi, and Arabic-English mixed questions answer in Arabic."""
    return contains_arabic(question) or contains_arabizi(question)


def strict_language_instruction(question: str) -> str:
    """Instruction snippet for LLM prompts."""
    if should_respond_arabic(question):
        return (
            "Response language: Arabic only. The student wrote Arabic, Egyptian Arabic, "
            "Arabizi, or mixed Arabic-English. Answer in Arabic; if the wording is colloquial, "
            "use natural Egyptian Arabic. Preserve official course codes, course names, CGPA, W, I, FA, "
            "and program names in English when needed."
        )
    return "Response language: English only. The student wrote in English, so answer only in English."

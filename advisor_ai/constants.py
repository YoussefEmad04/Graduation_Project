"""
Centralized constants for the Smart Academic Advisor.
Contains keywords for routing, greetings, and configuration.
"""

# ── Routing Keywords ────────────────────────────────────────────────

RAG_KEYWORDS = [
    "regulation", "regulations", "rule", "rules", "policy", "policies",
    "graduation", "credit hour", "credit hours", "gpa", "grade",
    "academic standing", "probation", "dismissal", "transfer",
    "bylaw", "bylaws", "requirement", "requirements", "withdraw",
    "withdrawal", "drop", "add", "warning",
    "grading", "mark", "marks", "score", "scores",
    "change major", "transfer program",
    "exam", "exams", "midterm", "mid term", "final", "absence",
    "absent", "excuse", "medical excuse", "missed exam",
    # Arabic (فصحى)
    "لائحة", "قوانين", "تخرج", "ساعات", "معدل", "تحويل", "نقل",
    "إنذار", "فصل", "متطلبات التخرج", "انسحاب", "حذف", "إضافة",
    "تقدير", "درجات", "نقاط", "حول", "احول", "غيرت",
    "امتحان", "امتحانات", "اختبار", "منتصف الفصل", "نهائي",
    "غياب", "عذر", "أعذار", "اعذار", "حضور",
    # Egyptian Arabic (عامية مصرية)
    "عايز اتخرج", "كام ساعة", "معدلي", "معدلي وقع", "هيفصلوني",
    "هيطردوني", "اسيب مادة", "سابها", "مش طايق", "شيل مادة",
    "زود مادة", "حذف مادة", "انقل", "رسبت", "سقطت", "وقعت في مادة",
    "عايز ارفع معدلي", "القوانين", "اللوايح", "الدرجات",
    "تحذير", "إنذار أكاديمي", "نظام الساعات", "درجاتي",
    "ميد", "ميدترم", "ميد ترم", "فاينال", "محضرش", "يحضر",
    "حصلو ظرف", "حصل له ظرف", "ظرف", "عذر مرضي",
    # Arabizi / Latin Arabic
    "kam sa3a", "kam saa", "el gpa", "gpa eh", "ta5arog", "takharog",
    "lawaye7", "lawe7a", "enazar", "enzar", "fasl", "drop subject",
    "asheil mada", "asahel mada", "a7awel", "a3la el gpa",
]

KG_KEYWORDS = [
    "course", "courses", "prerequisite", "prerequisites", "prereq",
    "study plan", "study path", "curriculum", "syllabus",
    "program", "ai program", "cybersecurity program",
    "level", "semester", "before", "need to take",
    "math", "mathematics", "statistics", "probability", "algorithms",
    "cs", "computer science", "ai", "artificial intelligence",
    "opens", "unlocks", "leads to", "after", "future courses",
    # Arabic (فصحى)
    "ماده", "مادة", "مواد", "مقرر", "مقررات", "متطلب", "متطلبات",
    "خطة دراسية", "منهج", "برنامج", "تفتح", "يفتح", "بعدها",
    # Egyptian Arabic (عامية مصرية)
    "كورس", "كورسات", "محتاج اخد ايه الاول", "لازم اخد ايه قبلها",
    "ايه المواد", "مواد السنة", "مواد الترم", "الخطة", "ايه اللي قبلها",
    "عايز اعرف المواد", "ايه البريريك", "لازم اعدي ايه",
    "هتفتحلي ايه", "ايه اللي بعدها", "تقفلي", "هتقفل", "مش هعرف افتح",
    "رياضة", "ماث", "علوم اساسية", "بيزك", "basic science", "math elective",
    # Arabizi / Latin Arabic
    "madda", "mada", "mawade", "mawad", "kors", "course bta3",
    "prereq", "pre req", "el pre", "btfta7", "betfta7", "bt2fel",
    "bet2fel", "lazem a5od", "akhod eh abl", "khota", "leveli",
    "zakaa", "zeka", "saiber", "cyber security", "baramg",
]

ELECTIVE_KEYWORDS = [
    "elective", "electives", "optional", "available courses",
    "choose", "selection", "this term", "this semester",
    # Arabic (فصحى)
    "اختيارية", "اختياري", "المتاحة", "الفصل الحالي",
    # Egyptian Arabic (عامية مصرية)
    "مواد اختياري", "ايه المواد المتاحة", "الترم ده فيه ايه",
    "اختار ايه", "ايه الاختياري", "مواد الترم ده",
    "ekhtiyari", "e5tiary", "available electives", "term da",
    "a5tar eh", "akhtar eh",
]

MENTAL_KEYWORDS = [
    "stress", "stressed", "afraid", "scared", "overwhelmed",
    "anxious", "anxiety", "depressed",
    "hopeless", "give up", "drop out", "can't do this",
    "too hard", "struggling", "worried", "pressure",
    "burned out", "burnout", "exhausted", "lost",
    # Arabic (فصحى)
    "ضغط", "خايف", "خائف", "قلق", "محبط", "صعب",
    "تعب", "مرهق", "ضايع", "يأس",
    # Egyptian Arabic (عامية مصرية)
    "مش قادر", "تعبت", "زهقت", "مش طايق", "هسيب الكلية",
    "مش عارف اعمل ايه", "حاسس اني فاشل", "مفيش فايدة",
    "كل حاجة صعبة", "مش لاحق", "ضغط نفسي", "محتاج مساعدة",
    "مكتئب", "حزين", "خايف ارسب", "مش هعرف اعديها",
    "مخنوق", "مش عارف", "نفسيتي", "تعبان", "دمرت",
    "mesh ader", "msh ader", "ta3ban", "zah2an", "makhno2",
    "khaief", "5ayef", "mota3ab", "msh la7e2", "nafseyty",
]

MAJOR_KEYWORDS = [
    "which major", "choose major", "ai or cyber", "cyber or ai",
    "which program", "what should i study", "which specialization",
    "recommendation", "recommend",
    # Arabic
    "اختار ايه", "اختار تخصص", "ايه التخصص", "ذكاء ولا سايبر",
    "سايبر ولا ذكاء", "انهي تخصص", "تخصص ايه", "ادخل ايه",
    "محتار", "محتار بين", "اختار برنامج", "انهي برنامج",
    "عايز اعرف الفرق", "الفرق بين", "ايهم احسن",
    "ai wala cyber", "cyber wala ai", "a5tar takhasos",
    "akhtar takhasos", "me7tar", "mehtar", "anhi program",
]

PATH_KEYWORDS = [
    "schedule", "plan", "courses", "subjects", "what should i take",
    "my list", "curriculum", "roadmap", "my courses",
    "المواد", "الجدول", "الخطة", "اخد ايه", "كورساتي",
    "mawade", "gdwal", "gedwal", "khota", "akhod eh", "korsaty",
]

GREETINGS = {
    "hi", "hello", "hey", "sup", "yo", "hii", "hiii",
    "مرحبا", "اهلا", "ازيك", "سلام", "هاي", "يا هلا",
    "السلام عليكم", "ahlan", "salam", "ezayak", "ezzayak",
    "3amel eh", "عامل ايه",
}

GREETING_RESPONSE = (
    "Hello! Welcome to the Smart Academic Advisor.\n\n"
    "I can help you with:\n"
    "  • Course information and prerequisites\n"
    "  • Academic regulations\n"
    "  • Available electives\n"
    "  • Study guidance and academic support\n\n"
    "How can I assist you today?"
)

KG_SYNTHESIS_PROMPT = """You are a helpful academic advisor for an AI & Cybersecurity program.
Use the following 'Context' to answer the 'User Question'.

Context:
{context}

User Question:
{question}

Instructions:
1. Answer naturally: If the context says 'is a prerequisite for', say 'X opens Y'. If it says 'Prerequisites for X are Y', say 'You need Y before X'.
2. If the user asks 'Can I take X?', look at the Context to see if it has prereqs. If empty, say 'Yes, it has no prerequisites'.
3. Keep the response in the SAME LANGUAGE as the User Question (Arabic or English).
4. If the student writes Arabic with Latin letters (Arabizi), respond in friendly Egyptian Arabic.
5. CRITICAL: Course codes [CS101] and names (e.g. Algorithms) MUST remain in English.
6. Use a friendly student-facing tone, but do not overuse emojis.

SPECIAL RULE FOR CATEGORIES & REQUIREMENTS:
- If the user asks about a specific Category (e.g. "Math Electives", "AI Electives", "University Requirements"):
  - Use the "Context" to find the list of courses.
  - State the "Required Hours" and "Type" (Compulsory/Elective) clearly.
  - List the courses with their codes.
  - **For Elective Categories**: Explicitly say "You can choose from these courses."

SPECIFIC CATEGORY RULES:
1. **Math & Basic Science**:
   - Compulsory: 21 CH.
   - Elective: 3 CH (1 course). Say: "You can take any Math Elective (MTH201, MTH202, etc) as they have no prerequisites."
2. **Basic Computer Science**:
   - Compulsory: 39 CH.
3. **University Requirements**:
   - Compulsory: 10 CH.
   - Elective: 2 CH (choose 1 course).
4. **AI Major**:
   - Requirements: 48 CH (Compulsory).
   - Electives: 21 CH (Select from list).
5. **Cybersecurity Major**:
   - Requirements: 48 CH (Compulsory).
   - Electives: 21 CH (Select from list).

قواعد الرد بالعربية:
- لو السؤال 'المادة بتفتح إيه؟' جاوب بـ 'المادة بتفتح كذا وكذا' بناءً على الـ Context.
- لو السؤال 'أقدر أخد المادة؟' أو 'إيه شروطها؟' وضح المتطلبات المسبقة.
- حافظ على أسماء المواد وأكوادها بالإنجليزية.
- **لو السؤال عن مجموعة (Category):**
  - اذكر عدد الساعات المطلوبة ونوعها (إجباري/اختياري).
  - اعرض قائمة المواد المتاحة في الـ Context (الاسم والكود).
  - بالنسبة للمواد الاختيارية (Electives) زي Math Elective أو AI Elective: وضح إن الطالب يقدر يختار منها.
  - **للرياضة (Math Electives)**: أكد إنه يقدر يختار أي مادة لأن ملهمش متطلبات (No Prereqs).
- لو الطالب سأل بالعربي، رد بالعربي (عامية مصرية لطيفة)."""

# ── Mental Support Prompts ──────────────────────────────────────────

MENTAL_SYSTEM_PROMPT = """You are the Mental Support Advisor for the Faculty of Artificial Intelligence at the Egyptian Russian University (ERU).

Your role: Provide ACADEMIC motivation, study tips, and emotional support to students who are stressed, anxious, or struggling.

STRICT RULES:
1. You are NOT a therapist. NEVER give medical or psychological advice.
2. ALWAYS stay within academic support: study tips, time management, motivation, exam preparation.
3. If the student seems severely distressed, recommend they visit the university counseling services.
4. Be warm, empathetic, and encouraging. Use emojis sparingly (🌟, 💪, 📚).
5. Give practical, actionable tips (3-5 bullet points).
6. Reference ERU resources when relevant (professors, TAs, academic advisor, counseling services).

STRICT LANGUAGE RULES:
- If the student writes in English → respond ONLY in English.
- If the student writes in Arabic (فصحى or عامية مصرية) → respond ONLY in Arabic.
- If عامية: use Egyptian dialect naturally (e.g., "متقلقش", "إنت تقدر", "خطوة خطوة").
- If the student writes Arabic with Latin letters (Arabizi), respond in friendly Egyptian Arabic.
- NEVER mix languages in the same response.

DYNAMIC GUIDANCE:
- Tailor your advice to the student's context if provided (Level/Major), but do NOT be rigid.
- **If the student's level is unknown, ask them naturally: "What year/level are you in?" before giving level-specific advice.**
- If Level 1: Focus on transition, new system, making friends.
- If Level 2: Focus on specialization choice (AI vs Cyber).
- If Level 3+: Focus on heavy workload, projects, career prep.
- ALWAYS allow for open-ended questions. Answer anything fully and supportively.
- Be a friendly "Study Buddy" + "Mentor".

Structure your response:
1.  Warm, empathetic opening (essential).
2.  Practical, actionable advice (bullet points).
3.  Encouraging closing."""

MAJOR_SYSTEM_PROMPT = """You are the Academic Advisor for the Faculty of Artificial Intelligence at the Egyptian Russian University (ERU).

A Level 2 student is asking about choosing between the two available programs:
1. **Artificial Intelligence (AI)**
2. **Cybersecurity**

STRICT LANGUAGE RULES:
- If the student writes in English → respond ONLY in English.
- If the student writes in Arabic (فصحى or عامية مصرية) → respond ONLY in Arabic.
- If عامية: use Egyptian dialect naturally.
- If the student writes Arabic with Latin letters (Arabizi), respond in friendly Egyptian Arabic.
- NEVER mix languages in the same response.

Provide a helpful comparison covering:

### About AI Program:
- Focuses on: Machine Learning, Deep Learning, NLP, Computer Vision, Pattern Recognition, Robotics
- Career paths: ML Engineer, Data Scientist, AI Researcher, NLP Engineer, Computer Vision Engineer
- Best for students who love: Math, algorithms, building intelligent systems, research
- Market demand: Very high globally, growing rapidly in Egypt and the Middle East
- Key skills: Python, TensorFlow/PyTorch, statistics, linear algebra

### About Cybersecurity Program:
- Focuses on: Network Security, Ethical Hacking, Cryptography, Digital Forensics, Penetration Testing
- Career paths: Security Analyst, Penetration Tester, SOC Analyst, Security Consultant, Forensics Investigator
- Best for students who love: Problem-solving, puzzles, protecting systems, networking
- Market demand: Critical shortage worldwide, extremely high demand in banking/government/enterprise
- Key skills: Networking, Linux, security tools (Wireshark, Metasploit, Burp Suite)

### Your recommendation approach:
1. Ask the student what they enjoy (if they haven't said)
2. Compare both programs concisely
3. Highlight that BOTH are excellent career paths
4. Mention that the shared Level 1-2 courses mean they already have foundation in both
5. Give honest pros/cons without bias
6. If the student mentions specific interests, recommend accordingly

Keep response concise (not more than 15-20 lines). Use bullet points."""

# ── Elective Service Prompts ────────────────────────────────────────

ELECTIVE_QUERY_PROMPT = """You are the Elective Advisor for the Faculty of Artificial Intelligence at the Egyptian Russian University (ERU).

You help students with questions about available elective courses for the current term.

CURRENT TERM DATA:
{term_data}

STRICT LANGUAGE RULES:
- If the student writes in English → respond ONLY in English.
- If the student writes in Arabic (فصحى or عامية مصرية) → respond ONLY in Arabic.
- If عامية: use Egyptian dialect naturally.
- If the student writes Arabic with Latin letters (Arabizi), respond in friendly Egyptian Arabic.
- NEVER mix languages in the same response.

RESPONSE RULES:
1. Only recommend electives from the CURRENT TERM DATA above.
2. If a student asks about a course NOT in the list, say it's not available this term.
3. Be helpful — suggest electives based on the student's interests if they ask.
4. Keep responses concise and well-formatted with bullet points.
5. Include course codes, names, and any available details (instructor, time, credits)."""

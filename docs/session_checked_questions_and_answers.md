# Session Checked Questions And Answers

Date: May 1, 2026

This report includes:
- all questions I explicitly tested in this session
- which ones were checked by automated regression tests
- which ones were checked live against the deployed Vercel app
- whether mental-health or study-support responses were validated

## 1. Infra And Health Checks

### User request
`check the status of kg and rag and supabase and vercel and openai`

### Verified result
- `KG`: connected
- `RAG`: connected
- `Supabase`: initially not connected, later rechecked as connected
- `Vercel`: linked, deployed, reachable
- `OpenAI`: configured and reachable

### User follow-up
`what is from these not connected`

### Answer at that time
- `Supabase` was the only one not connected at that moment

### User update
`i now resumed subabase`

### Recheck result
- `Supabase`: connected
- `KG`: connected
- `RAG`: connected
- `OpenAI`: working through RAG

## 2. Validation Commands Run

### Commands
- `.venv/bin/python -m unittest discover -s tests`
- `.venv/bin/python -m compileall advisor_ai scripts tests`

### Result
- tests passed
- compile check passed

### Final suite result after the new chatbot regression tests were added
- total tests: `44`
- result: `OK`

## 3. Full Question Bank Tested In Code

These were added as automated regression tests in `tests/test_advisor_smoke.py`.

## 3.1 KG Questions Tested

### English
- `What are the prerequisites for Deep Learning?`
- `What courses does Data Structures open for me?`
- `Is Introduction to AI an elective or a core course?`
- `Can I register for AI301 if I failed CS203?`

### Arabic
- `ايه متطلبات تسجيل مادة Image Processing؟`
- `لو نجحت في مادة Data Structures، ايه المواد اللي هتفتحلي الترم الجاي؟`
- `هي مادة Neural Networks دي اختياري ولا اجباري؟`
- `ينفع اسجل AI301 لو انا شايل مادة البرمجة؟`

### What was verified
- these route to KG logic correctly
- typo-tolerant matching still works for course-related questions

## 3.2 RAG Questions Tested

### English
- `What is the maximum number of credit hours I can take in a regular semester?`
- `What is the passing grade for graduation projects?`
- `How is my GPA calculated?`
- `Are there any penalties for missing more than 25% of lectures?`
- `What is the procedure if I want to withdraw from a course after the add/drop deadline?`
- `Can I repeat a course to improve my GPA?`

### Arabic
- `الحد الأقصى للتسجيل في الترم العادي كام ساعة معتمدة؟`
- `ازاي بيتم حساب المعدل التراكمي (GPA)؟`
- `لو غبت اكتر من 25% من المحاضرات ايه اللي هيحصل؟`
- `ايه الاجراءات لو عايز اسحب مادة بعد فترة الحذف والاضافة؟`
- `ينفع اعيد مادة عشان احسن المجموع بتاعي؟`
- `لو جبت مقبول في مادة، هل ممكن اعيدها؟`

### What was verified
- these route to RAG logic correctly

## 3.3 Elective Questions Tested

### English
- `What are the available elective courses for this semester?`

### Arabic
- `ايه المواد الاختيارية المتاحة ليا اسجلها الترم ده؟`

### What was verified
- these route to the elective service correctly

## 3.4 Curriculum / Study-Plan Questions Tested

### English
- `What are the second-term courses for a level 3 Artificial Intelligence student?`

### Arabic
- `ايه هي مواد الترم التاني لسنة رابعة قسم ذكاء اصطناعي؟`

### What was verified
- these route to RAG/study-plan handling correctly

## 3.5 Conversational Follow-Ups Tested

### KG-context follow-ups

Initial context:
- `What are the prerequisites for AI301?`

Follow-ups tested:
- `Is it a core course?`
- `And what does it open?`
- `هي المادة دي اجباري؟`
- `طيب والمادة دي بتفتح ايه؟`

### RAG-context follow-ups

Initial context:
- `What is the maximum credit load for the regular semester?`

Follow-ups tested:
- `What about if my GPA is above 3.5?`
- `And for the summer semester?`
- `Is this the same for graduating students?`
- `طيب لو ال GPA بتاعي اعلى من 3.5؟`
- `طيب وبالنسبة للترم الصيفي؟`
- `هل الكلام ده ينطبق على خريجين الترم ده؟`

### What was verified
- short vague follow-ups keep the previous route/context correctly

## 3.6 Typo-Tolerance Questions Tested

- `What are the prequesits for Deep Learnng?`
- `ايه ال prequesits بتاعة مادة Image Processing؟`

### What was verified
- typo normalization improved routing and course detection

## 3.7 Out-Of-Scope Questions Tested

- `Who is the dean of the faculty?`
- `مين عميد الكلية؟`

### Expected fallback
- English: `I couldn't find this specific question in our course data or regulation documents.`
- Arabic: `مش لاقي السؤال ده في بيانات المواد أو مستندات اللوايح عندي.`

### What was verified
- out-of-scope questions now return the standard fallback instead of generic chat

## 3.8 Unsupported Course-Metadata Follow-Ups Tested

Initial context:
- `What are the prerequisites for AI301?`

Follow-up:
- `Who teaches it this semester?`

Initial context:
- `ايه متطلبات تسجيل مادة Image Processing؟`

Follow-up:
- `مين الدكتور بتاعها الترم ده؟`

### What was verified
- unsupported teacher/instructor questions return the standard fallback

## 3.9 Unknown-Course Fallback Tested

- `What are the prerequisites for Quantum Cooking 101?`

### What was verified
- internal KG not-found responses are converted into the standard fallback

## 3.10 Mental Support Questions Tested

### English
- `I am afraid I will fail this semester`
- `I am stressed and need study tips`

### Arabic
- `انا خايف اسقط الترم ده`
- `محتاج نصايح للمذاكرة`

### What was verified
- these route to the mental-support service correctly

## 3.11 Major Selection Questions Tested

### English
- `Which major should I choose, AI or Cybersecurity?`

### Arabic
- `اختار AI ولا Cyber؟`

### What was verified
- these route to major-guidance handling correctly

## 4. Live Answers Checked Against The Deployed App

These were actually sent to the production deployment after the fixes.

## 4.1 KG Live Checks

### Question
`What are the prerequisites for Deep Learning?`

### Live answer
`You need Machine Learning [AI301] before Deep Learning [AI403]. If you have any more questions about the courses or their prerequisites, feel free to ask!`

### Question
`What are the prequesits for Deep Learnng?`

### Live answer
`You need Machine Learning [AI301] before Deep Learning [AI403]. If you have any other questions or need further clarification, feel free to ask!`

### Question
`What are the prerequisites for AI301?`

### Live answer
`You need Introduction to Artificial Intelligence [AI201] and Probability and Statistics 1 [MTH104] before AI301.`

## 4.2 RAG Live Check

### Question
`How is my GPA calculated?`

### Live answer
`Your GPA (Grade Point Average) is calculated using the following formula:

- **CGPA = (Σ (Grade Point * Number of Credit Hours)) / (Σ Number of Credit Hours)**

Where:
- **Grade Point** corresponds to the letter grades you receive (e.g., A = 4.0, B = 3.0, etc.).
- **Number of Credit Hours** is the credit value assigned to each course.

For example, if you have the following grades and credit hours:
- A (3 credit hours) = 4.0
- B (3 credit hours) = 3.0

The calculation would be:
- CGPA = [(4.0 * 3) + (3.0 * 3)] / (3 + 3) = (12 + 9) / 6 = 3.5.`

## 4.3 Out-Of-Scope Live Checks

### Question
`Who is the dean of the faculty?`

### Live answer
`I couldn't find this specific question in our course data or regulation documents.`

### Question
`مين عميد الكلية؟`

### Live answer
`مش لاقي السؤال ده في بيانات المواد أو مستندات اللوايح عندي.`

## 4.4 Unsupported Follow-Up Live Check

### Initial question
`What are the prerequisites for AI301?`

### Follow-up
`Who teaches it this semester?`

### Live answer
`I couldn't find this specific question in our course data or regulation documents.`

## 4.5 Mental Support Live Checks

### Question
`I am afraid I will fail this semester`

### Live answer
`I'm really sorry to hear that you're feeling this way. It's completely normal to feel overwhelmed at times, but remember that you have the strength to get through this! 🌟 Let's focus on some steps to help you regain your confidence and tackle this semester head-on.

Here are some practical tips:

- **Create a Study Schedule**: Break down your subjects and allocate specific times for each one. This will help you manage your time effectively and ensure you're covering all your material.
- **Reach Out for Help**: Don’t hesitate to contact your professors or TAs if you’re struggling with certain topics. They’re there to support you and can provide valuable guidance.
- **Form Study Groups**: Connecting with classmates can make studying more enjoyable and effective. You can share insights and help each other understand difficult concepts.
- **Stay Organized**: Keep track of deadlines, assignments, and exams with a planner or app. This way, you won’t miss anything important and can prioritize your tasks.
- **Take Care of Yourself**: Make sure to take breaks, eat well, and get enough sleep. Your mental and physical health play a big role in your academic performance.

Remember, you’re not alone in this! It's okay to ask for help, and I believe in your ability to turn things around. If you continue to feel overwhelmed, consider visiting the university counseling services for additional support. You've got this! 💪 If you have any specific concerns or questions, feel free to share.`

### Question
`محتاج نصايح للمذاكرة`

### Live answer
`أهلاً بيك! متقلقش، المذاكرة ممكن تكون تحدي، لكن مع شوية تنظيم وتركيز هتقدر تحقق أهدافك. إليك بعض النصايح اللي ممكن تساعدك:

- **حدد أهداف واضحة**: قبل ما تبدأ مذاكرة كل مادة، حدد إيه اللي عاوز تحققه في كل جلسة. مثلاً، ممكن تقرر تذاكر فصل معين أو موضوع محدد.
- **استخدم تقنيات المذاكرة الفعالة**: جرب تقنيات زي "مخططات ذهنية" أو "البطاقات التعليمية" (Flashcards) لتسهيل المعلومات وحفظها.
- **خصص وقت للمذاكرة**: حاول تقسم وقتك بشكل جيد، مثلاً 25 دقيقة مذاكرة ثم 5 دقائق راحة (تقنية بومودورو). ده هيساعدك تحافظ على التركيز.
- **ابحث عن مصادر إضافية**: لو عندك استفسارات أو محتاج دعم، مترددش تسأل أساتذتك أو زملائك. ممكن كمان تستفيد من المكتبة أو الموارد الإلكترونية في الجامعة.
- **تواصل مع زملائك**: التعاون مع زملائك في الدراسة ممكن يفتح لك مجالات جديدة للفهم. جرب تشكل مجموعة مذاكرة صغيرة.

أنا متأكد إنك تقدر تذاكر وتحقق نتائج ممتازة! لو عندك أي أسئلة أو محتاج دعم إضافي، أنا هنا. بالتوفيق! 🌟`

## 4.6 Major Selection Live Checks

### Question
`Which major should I choose, AI or Cybersecurity?`

### Live answer
`To help you choose between AI and Cybersecurity, let’s consider a few points:

### What do you enjoy?
- What subjects excite you? Do you prefer working with algorithms and intelligent systems, or do you find problem-solving and protecting systems more engaging?

### AI Program:
- **Focuses on:** Machine Learning, Deep Learning, NLP, Computer Vision, Robotics
- **Career paths:** ML Engineer, Data Scientist, AI Researcher, NLP Engineer
- **Best for:** Students who love math, algorithms, and research
- **Market demand:** Very high globally; rapidly growing in Egypt and the Middle East
- **Key skills:** Python, TensorFlow/PyTorch, statistics

### Cybersecurity Program:
- **Focuses on:** Network Security, Ethical Hacking, Cryptography, Digital Forensics
- **Career paths:** Security Analyst, Penetration Tester, Security Consultant
- **Best for:** Students who enjoy problem-solving and protecting systems
- **Market demand:** Critical shortage worldwide; especially high in banking and government sectors
- **Key skills:** Networking, Linux, security tools

### Summary:
- Both programs are excellent career paths.
- You already have a foundation in both due to shared Level 1-2 courses.
- If you enjoy math and research, AI may be a better fit.
- If you prefer puzzles and protecting information, Cybersecurity could be the way to go.

Feel free to share your interests further, and I can help you decide!`

### Question
`اختار AI ولا Cyber؟`

### Live answer
`قبل ما أقولك، ممكن تقولي إنت بتحب إيه أكتر أو إيه الحاجات اللي بتحب تشتغل عليها؟

هقول لك عن كل برنامج:

### برنامج الذكاء الاصطناعي (AI):
- **التركيز:** تعلم الآلة، التعلم العميق، معالجة اللغة الطبيعية، رؤية الكمبيوتر، التعرف على الأنماط، الروبوتات.
- **مسارات العمل:** مهندس تعلم آلة، عالم بيانات، باحث في AI، مهندس NLP، مهندس رؤية الكمبيوتر.
- **أفضل للطلاب اللي بيحبوا:** الرياضيات، الخوارزميات، بناء أنظمة ذكية، البحث.
- **طلب السوق:** مرتفع جداً عالمياً، وبيزداد بسرعة في مصر والشرق الأوسط.
- **المهارات الرئيسية:** بايثون، TensorFlow/PyTorch، الإحصاء، الجبر الخطي.

### برنامج الأمن السيبراني:
- **التركيز:** أمن الشبكات، الاختراق الأخلاقي، التشفير، الطب الشرعي الرقمي، اختبار الاختراق.
- **مسارات العمل:** محلل أمان، مختبر اختراق، محلل SOC، مستشار أمان، محقق في الجرائم الرقمية.
- **أفضل للطلاب اللي بيحبوا:** حل المشكلات، الألغاز، حماية الأنظمة، الشبكات.
- **طلب السوق:** نقص حاد عالمياً، طلب عالي جداً في البنوك والحكومة والشركات.
- **المهارات الرئيسية:** الشبكات، لينكس، أدوات الأمان (Wireshark، Metasploit، Burp Suite).

### نصيحتي:
- **كلا البرنامجين ممتازين ومساراتهم واعدة.**
- **الدورات المشتركة في المستوى 1-2 بتديك أساس قوي في الاتنين.**
- **لو بتحب الرياضيات وبناء أنظمة ذكية، يمكن AI يكون أفضل.**
- **أما لو بتحب حماية الأنظمة وحل الألغاز، Cybersecurity هيكون مناسب ليك.**

اختر بناءً على اهتماماتك، وأنا هنا لو محتاج مساعدة أكتر!`

## 5. Mental Health / Study Support Validation Status

### Short answer
- Yes, mental-support and major-selection prompts are now validated in this session.

### What was validated
- routing for stress/fear/study-tips prompts
- routing for major-selection prompts
- live production responses in English and Arabic
- responses stayed within academic support and study guidance
- major-selection responses stayed on AI vs Cybersecurity comparison

### Residual note
- I checked representative prompts, not every possible mental-support wording
- if you want broader coverage, I can add a larger mental-support prompt bank next

## 6. Production Health After Deployment

### Verified result
- production alias: `https://smart-academic-advisor-api.vercel.app`
- `/health`: `200 OK`
- `kg`: connected
- `rag`: connected
- `history`: connected

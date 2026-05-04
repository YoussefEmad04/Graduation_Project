# PDF Grounded Chatbot Report

- Timestamp UTC: `2026-05-01T22:59:07.998565+00:00`
- Base URL: `https://smart-academic-advisor-api.vercel.app`

## Summary

- `RAG`: 30/30 passed
- `KG`: 30/30 passed
- `GENERAL`: 30/30 passed

## RAG

### PASS - كام ساعة معتمدة لازم الطالب يجتازها عشان يتخرج؟

- Response:

```text
- يجب على الطالب اجتياز 144 ساعة معتمدة كحد أدنى للتخرج.
```

### PASS - الدراسة في الكلية ماشية بأي نظام؟

- Response:

```text
- الدراسة في الكلية بنظام الساعات المعتمدة.
```

### PASS - مدة الفصل الدراسي النظامي كام أسبوع؟

- Response:

```text
- مدة الفصل الدراسي النظامي 17 أسبوعًا متضمنة فترة الامتحانات.
```

### PASS - الفصل الصيفي مدته كام أسبوع؟

- Response:

```text
- الفصل الصيفي مدته 8 أسابيع متضمنة فترة الامتحانات.
```

### PASS - هل الفصل الصيفي إجباري ولا اختياري؟

- Response:

```text
- الفصل الصيفي اختياري للطالب.
```

### PASS - الحد الأقصى للتسجيل في الفصل الصيفي كام ساعة؟

- Response:

```text
- الحد الأقصى للتسجيل في الفصل الصيفي هو 9 ساعات معتمدة.
```

### PASS - أقل عدد ساعات للتسجيل في فصل خريف أو ربيع كام؟

- Response:

```text
- أقل عدد ساعات للتسجيل في فصل الخريف أو الربيع هو 9 ساعات معتمدة، إلا إذا كانت الساعات المتبقية للتخرج أقل من ذلك.
```

### PASS - الطالب صاحب CGPA أعلى من أو يساوي 3 يقدر يسجل كام ساعة؟

- Response:

```text
- الطالب صاحب CGPA أعلى من أو يساوي 3 يقدر يسجل 21 ساعة معتمدة، وكذلك الطالب الذي سيتخرج في نفس الفصل.
```

### PASS - الطالب صاحب CGPA من 2 إلى أقل من 3 يقدر يسجل كام ساعة؟

- Response:

```text
- الطالب صاحب CGPA من 2 إلى أقل من 3 يقدر يسجل 18 ساعة معتمدة.
```

### PASS - الطالب صاحب CGPA من 1 إلى أقل من 2 يقدر يسجل كام ساعة؟

- Response:

```text
- الطالب صاحب CGPA من 1 إلى أقل من 2 يقدر يسجل 15 ساعة معتمدة.
```

### PASS - الطالب صاحب CGPA أقل من 1 يقدر يسجل كام ساعة؟

- Response:

```text
- الطالب صاحب CGPA أقل من 1 يقدر يسجل 12 ساعة معتمدة.
```

### PASS - التسجيل في المقررات يستمر لحد إمتى؟

- Response:

```text
- التسجيل في المقررات يستمر حتى نهاية الأسبوع الثاني.
```

### PASS - الحذف والإضافة بيكونوا لحد إمتى؟

- Response:

```text
- الحذف والإضافة يكونان حتى نهاية الأسبوع الثالث بعد موافقة المرشد الأكاديمي.
```

### PASS - إيه شرط التسجيل في مقرر؟

- Missing any-match keywords: `اجتياز المتطلبات`
- Response:

```text
- يسمح للطالب بالتسجيل في أي مقرر بعد اجتياز متطلباته السابقة.
```

### PASS - هل رأي المرشد الأكاديمي إلزامي؟

- Response:

```text
- رأي المرشد الأكاديمي استشاري، والطالب مسؤول عن المقررات التي يسجلها.
```

### PASS - الطالب يقدر ينسحب من مقرر لحد إمتى؟

- Response:

```text
- الطالب يقدر ينسحب من مقرر حتى نهاية الأسبوع التاسع بعد موافقة المرشد الأكاديمي ومراعاة الحد الأدنى للساعات.
```

### PASS - لو الطالب انسحب في الميعاد، هل يعتبر راسب؟

- Response:

```text
- لو الطالب انسحب في الميعاد المحدد لا يعتبر راسبًا، ويُحتسب له تقدير منسحب W فقط.
```

### PASS - لو الطالب انسحب بعد الفترة المحددة دون عذر قهري مقبول، يحصل إيه؟

- Response:

```text
- لو الطالب انسحب بعد الفترة المحددة دون عذر قهري مقبول، يحتسب له تقدير راسب في المقررات التي انسحب منها.
```

### PASS - الدرجة النهائية لأي مقرر من كام؟

- Response:

```text
- الدرجة النهائية لأي مقرر هي 100 درجة.
```

### PASS - أقل درجة للنجاح في أي مقرر كام؟

- Response:

```text
- أقل درجة للنجاح في أي مقرر هي 50 درجة.
```

### PASS - توزيع درجات المقرر النظري إيه؟

- Response:

```text
- توزيع درجات المقرر النظري: 40% للامتحان النهائي، 20% لامتحان منتصف الفصل، 40% للاختبارات الدورية والأعمال الفصلية.
```

### PASS - امتحان الميدترم عليه كام في المقرر النظري؟

- Response:

```text
- امتحان منتصف الفصل في المقرر النظري عليه 20%.
```

### PASS - شرط النجاح المرتبط بالامتحان النهائي التحريري إيه؟

- Response:

```text
- من شروط النجاح أن يحصل الطالب على 30% على الأقل من درجة الامتحان النهائي التحريري.
```

### PASS - توزيع درجات المقرر الذي يحتوي على تطبيقات عملية إيه؟

- Response:

```text
- توزيع درجات المقرر الذي يحتوي على تطبيقات عملية: 40% نهائي، 20% منتصف الفصل، 20% اختبارات دورية وأعمال فصلية، 20% تطبيقات عملية.
```

### PASS - زمن امتحان نهاية الفصل لأي مقرر كام؟

- Missing any-match keywords: `2`
- Response:

```text
- زمن امتحان نهاية الفصل لأي مقرر هو ساعتان.
```

### PASS - نسبة الحضور المطلوبة لدخول الامتحان النهائي كام؟

- Response:

```text
- نسبة الحضور المطلوبة لدخول الامتحان النهائي لا تقل عن 75% من المحاضرات والتطبيقات.
```

### PASS - لو نسبة غياب الطالب تجاوزت 25% يحصل إيه؟

- Missing any-match keywords: `حرمانه`
- Response:

```text
- إذا تجاوزت نسبة الغياب 25% يجوز لمجلس الكلية حرمان الطالب من دخول الامتحان النهائي بعد إنذاره كتابيًا.
```

### PASS - لو الطالب غاب عن الامتحان النهائي بدون عذر مقبول يحصل إيه؟

- Missing any-match keywords: `abs`
- Response:

```text
- إذا غاب الطالب عن الامتحان النهائي بدون عذر مقبول يعطى تقدير راسب FA.
```

### PASS - لو الطالب غاب عن الامتحان النهائي بعذر قهري مقبول يحصل إيه؟

- Response:

```text
- إذا غاب الطالب عن الامتحان النهائي بعذر قهري مقبول يحتسب له تقدير غير مكتمل I بشرط حصوله على 60% على الأقل من درجات الأعمال الفصلية وألا يكون محروماً من الامتحان.
```

### PASS - ما معنى تقدير غير مكتمل I؟

- Response:

```text
- تقدير غير مكتمل I يُمنح لطالب لم يحضر الامتحان النهائي بعذر قهري مقبول مع استيفاء شرط 60% من الأعمال الفصلية.
```


## KG

### PASS - مادة Algorithms (CS205) محتاجة إيه قبلها عشان أقدر أسجلها؟

- Response:

```text
عشان تسجل في مادة Algorithms (CS205)، محتاج قبلها تأخذ مادة Structured Programming (CS102). يعني لازم تكون خلصت CS102 قبل ما تسجل في CS205.
```

### PASS - مادة Data Structures تتفتح بإيه؟

- Response:

```text
مادة Data Structures [CS203] تتفتح بإيه؟ 

المادة بتفتح بعد ما تكون أخدت Object Oriented Programming [CS201].
```

### PASS - إيه هي سلسلة المواد اللي محتاجها كلها بالكامل عشان أوصل لمشروع التخرج 2 في الـ AI؟

- Response:

```text
عشان توصل لمشروع التخرج 2 [AI407] في الـ AI، هتحتاج تاخد السلسلة التالية من المواد:

1. [AI404] Graduation Project 1
2. [AI401] Intelligent Algorithms
3. [AI402] Computational Cognitive Systems
4. [AI403] Deep Learning
5. [AI405] Multi Agent Systems
6. [AI406] AI Applications

لازم تكمل المواد دي قبل ما تقدر تاخد مشروع التخرج 2. لو محتاج أي مساعدة تانية، أنا هنا!
```

### PASS - مادة Introduction to Computer Science (CS101) بتفتح إيه في المستويات اللي بعد كده؟

- Response:

```text
مادة Introduction to Computer Science (CS101) بتفتح مادة Structured Programming (CS102) في المستويات اللي بعد كده.
```

### PASS - لو شلت مادة Math 1 لا قدر الله، دي بتقفل إيه؟

- Response:

```text
لو شلت مادة [MTH101] Mathematics 1، ده هيقفل عليك [MTH103] Mathematics 2 و[MTH104] Probability and Statistics 1. يعني مش هتقدر تاخدهم من غير ما تكون أخدت [MTH101].
```

### PASS - مادة Human Rights بتفتح إيه؟

- Missing any-match keywords: `not a prerequisite, ليست متطلب, is not a prerequisite, مش متطلب`
- Response:

```text
مادة Human Rights & Anticorruption مش مرتبطة بأي مواد تانية، يعني هي مش شرط لأخذ مواد مستقبلية.
```

### PASS - إيه هي المواد المقترحة لسنة تالتة في برنامج الأمن السيبراني؟

- Response:

```text
المواد المقترحة لسنة تالتة في برنامج الأمن السيبراني هي:

1. Blockchain & Cryptocurrencies [CB311] — 3 credits (Prerequisites: Cryptography)
2. Computer Architecture [CB302] — 3 credits
3. Computer Networks [CB301] — 3 credits (Prerequisites: Object Oriented Programming)
4. Cryptography [CB303] — 3 credits (Prerequisites: Linear Algebra)
5. Cyber Security for Internet of Things [CB312] — 3 credits (Prerequisites: Computer Networks)
6. Data Mining & Big Data Analysis [DS301] — 3 credits
7. Hardware Security [CB309] — 3 credits (Prerequisites: Logic Design)
8. Internet of Things [IS306] — 3 credits
9. Introduction to Cyber Attacks [CB307] — 3 credits (Prerequisites: Introduction to Cyber-Security)
10. Introduction to Cyber-Security [CB304] — 3 credits (Prerequisites: Computer Networks)
11. Network Security [CB305] — 3 credits (Prerequisites: Computer Networks, Introduction to Cyber-Security)
12. Operations Research [STA301] — 3 credits
13. Real-Time Auditing & Defense [CB308] — 3 credits (Prerequisites: Network Security)
14. Reverse Engineering & Disassemblers [CB313] — 3 credits (Prerequisites: Introduction to Cyber-Security)
15. Software Security [CB306] — 3 credits (Prerequisites: Object Oriented Programming, Introduction to Cyber-Security)
16. Threat Detection and Mitigation [CB314] — 3 credits (Prerequisites: Network Security)
17. Usable Security [CB310] — 3 credits (Prerequisites: Introduction to Cyber-Security)

لو عندك أي استفسار عن مادة معينة أو متطلبات، أنا هنا للمساعدة!
```

### PASS - عاوز خطة الدراسة للفرقة الأولى عامةً.

- Missing any-match keywords: `Level 1`
- Response:

```text
بالنسبة لخطة الدراسة للفرقة الأولى، هنا المواد الموصى بها:

### متطلبات الرياضيات والعلوم الأساسية:
- **إجباري**: 21 ساعة معتمدة.
- **اختياري**: 3 ساعات معتمدة (مادة واحدة).
  - يمكنك اختيار أي مادة من الرياضيات الاختيارية (MTH201، MTH202، إلخ) لأنها ملهاش متطلبات مسبقة.

### متطلبات علوم الكمبيوتر الأساسية:
- **إجباري**: 39 ساعة معتمدة.
  - المواد:
    - Discrete Structure [CS103] — 3 credits
    - Fundamentals of Information Systems [IS101] — 3 credits
    - Introduction to Computer Science [CS101] — 3 credits
    - Structured Programming [CS102] — 3 credits (Prerequisites: Introduction to Computer Science)
    - Mathematics 1 [MTH101] — 3 credits
    - Mathematics 2 [MTH103] — 3 credits (Prerequisites: Mathematics 1)
    - Linear Algebra [MTH102] — 3 credits
    - Probability and Statistics 1 [MTH104] — 3 credits (Prerequisites: Mathematics 1)
    - Electronics [ELC101] — 3 credits
    - Physics [PH101] — 3 credits

### متطلبات الجامعة:
- **إجباري**: 10 ساعات معتمدة.
- **اختياري**: 2 ساعات معتمدة (اختر مادة واحدة).

### ملاحظات:
- تأكد من متابعة المتطلبات المسبقة لكل مادة، خاصة المواد اللي فيها prerequisites. لو عندك أي استفسار تاني، أنا هنا للمساعدة!
```

### PASS - إيه هي متطلبات الجامعة الإجبارية؟

- Response:

```text
المتطلبات الجامعية الإجبارية هي 10 ساعات معتمدة. المواد المتاحة هي:

- [HM001] English Language 1 (2 CH)
- [HM002] English Language 2 (2 CH)
- [HM003] Human Rights & Anticorruption (2 CH)
- [HM004] Russian Language 1 (2 CH)
- [HM005] Russian Language 2 (2 CH)

كل المواد دي إجباري.
```

### PASS - قوللي مواد العلوم الأساسية والاختيارية بتاعت الرياضة؟

- Response:

```text
بالنسبة لمواد العلوم الأساسية والاختيارية بتاعت الرياضة، عندك:

- **عدد الساعات المطلوبة**: 3 ساعات
- **النوع**: اختياري

تقدر تختار من المواد دي:
- [MTH201] Mathematics 3 (3 CH)
- [MTH202] Probability and Statistics 2 (3 CH)
- [MTH203] Numerical Analysis (3 CH)

تقدر تختار أي مادة من المواد دي، لأنها ملهاش متطلبات مسبقة.
```

### PASS - كلمني عن مادة الـ ML

- Response:

```text
مادة الـ ML، أو [AI301] Machine Learning، هي مادة أساسية في البرنامج. عدد الساعات المعتمدة لها هو 3 ساعات، وهي في المستوى الثالث. المادة بتغطي أساسيات تعلم الآلة وتعتبر جزء مهم من دراسة الذكاء الاصطناعي. لو عندك أي استفسارات تانية عن المادة أو محتاج معلومات إضافية، أنا هنا للمساعدة!
```

### PASS - عاوز اعرف معلومات عن مادة رياضه 2

- Missing any-match keywords: `Mathematics 2`
- Response:

```text
مادة رياضه 2 (MTH103) هي مادة أساسية بمستوى 1، وبتدي 3 ساعات معتمدة. المادة دي تعتبر جزء من المقررات الأساسية في البرنامج. لو عندك أي استفسار تاني عن المادة أو محتاج معلومات إضافية، أنا هنا للمساعدة!
```

### PASS - ما متطلب Mathematics 2 [MTH103] في Level 1؟

- Response:

```text
عشان تاخد Mathematics 2 [MTH103]، محتاج تكون خلصت Mathematics 1 [MTH101] الأول. يعني لازم تخلص MTH101 قبل ما تبدأ MTH103.
```

### PASS - ما متطلب Probability and Statistics 1 [MTH104]؟

- Response:

```text
عشان تاخد مادة Probability and Statistics 1 [MTH104]، لازم تكون أخدت مادة Mathematics 1 [MTH101] قبلها.
```

### PASS - ما متطلب Structured Programming [CS102]؟

- Response:

```text
عشان تاخد مادة Structured Programming [CS102]، لازم تكون أخدت مادة Introduction to Computer Science [CS101] قبلها. يعني، تحتاج [CS101] قبل ما تاخد [CS102].
```

### PASS - ما متطلب Signal and System [CS202] في Level 2؟

- Response:

```text
المتطلب المسبق لمادة Signal and System [CS202] في Level 2 هو Mathematics 2 [MTH103]. يعني لازم تكون أخدت MTH103 قبل ما تقدر تسجل في CS202.
```

### PASS - ما متطلب Algorithms [CS205]؟

- Response:

```text
عشان تاخد مادة Algorithms [CS205]، لازم تكون أخدت مادة Structured Programming [CS102] قبلها. يعني، محتاج [CS102] قبل [CS205].
```

### PASS - ما متطلب Data Structure [CS203]؟

- Response:

```text
عشان تاخد مادة Data Structures [CS203]، لازم تكون أخدت مادة Object Oriented Programming [CS201] قبلها. يعني، تحتاج [CS201] قبل [CS203].
```

### PASS - ما متطلب Introduction to Artificial Intelligence [AI201]؟

- Response:

```text
عشان تاخد مادة Introduction to Artificial Intelligence [AI201]، لازم تكون أخدت Linear Algebra [MTH102] قبلها. يعني، تحتاج MTH102 قبل AI201.
```

### PASS - اذكر مواد AI program في Level 4 Semester 1.

- Response:

```text
مواد برنامج الذكاء الاصطناعي في المستوى 4، الفصل الدراسي الأول هي:

- **AI402**: Computational Cognitive Systems
- **AI403**: Deep Learning
- **AI404**: Graduation Project 1
- **AI401**: Intelligent Algorithms
- **Major elective 4**: upon the selection
- **Major elective 5**: upon the selection.
```

### PASS - ما متطلب AI406 AI Applications؟

- Response:

```text
عشان تاخد مادة [AI406] AI Applications، محتاج تكون خلصت المواد المسبقة: [AI304] Computer Vision و[AI401] Intelligent Algorithms. يعني لازم تكون عندك الأساسيات دي قبل ما تبدأ في [AI406].
```

### PASS - ما متطلب AI407 Graduation Project 2؟

- Response:

```text
متطلب AI407 Graduation Project 2 هو:

- **المتطلب السابق**: AI404 Graduation Project 1.
```

### PASS - اذكر بعض مواد AI elective courses.

- Missing any-match keywords: `STA301, DS307, CB310, CB311`
- Response:

```text
بالنسبة لمواد AI elective courses، عندك 21 ساعة اختيارية. تقدر تختار من المواد دي:

- [AI307] Computational Learning Theory (3 CH)
- [AI308] Language Modeling (3 CH)
- [AI309] User Models (3 CH)
- [AI310] Handwriting Recognition (3 CH)
- [AI311] Expert Systems (3 CH)
- [AI312] Architecture of Intelligence (3 CH)
- [AI314] Artificial Intelligence in Games (3 CH)
- [AI408] Cognitive Modeling (3 CH)
- [AI409] Cognitive Engineering (3 CH)
- [AI410] Cognitive Natural Networks (3 CH)
- [AI411] Language and Speech Technology (3 CH)
- [AI412] Statistical Language Modeling (3 CH)
- [AI413] AI for Robotics (3 CH)
- [AI415] Selected Topic in AI 1 (3 CH)
- [AI416] Selected Topic in AI 2 (3 CH)
- [CS301] Operations Research (3 CH)
- [CS303] Image Processing (3 CH)
- [CS307] Computer Graphics (3 CH)
- [CS309] Embedded Systems (3 CH)
- [CS403] Advanced Knowledge Representation and Reasoning (3 CH)
- [ROB302] Fundamental of Cognitive Interaction with Robots (3 CH)
- [SW305] Software Development for Mobile Devices (3 CH)
- [SW401] Software Testing & Quality Assurance (3 CH)

تقدر تختار من المواد دي حسب اهتماماتك.
```

### PASS - اذكر مواد Data Science Level 3 Semester 1.

- Response:

```text
مواد Data Science Level 3 Semester 1 هي:

- **DS304**: Data Visualization
- **DS303**: Exploratory Data Analysis
- **DS302**: Fundamental of Data Science
- **AI301**: Machine Learning
- **Major elective 1**: (اختياري)
- **Major elective 2**: (اختياري)
```

### PASS - ما متطلب DS306 Advanced Database Systems؟

- Missing any-match keywords: `IS201`
- Response:

```text
المادة DS306 Advanced Database Systems متطلباتها المسبقة مش موجودة في الـ Context. يعني، أقدر أقول لك إنك ممكن تاخدها من غير أي متطلبات مسبقة.
```

### PASS - ما متطلب DS407 Graduation Project 2؟

- Response:

```text
- متطلب **DS407 Graduation Project 2** هو **DS406 Graduation Project 1** .
```

### PASS - اذكر مواد Cybersecurity Level 3 Semester 1.

- Response:

```text
مواد Cybersecurity Level 3 Semester 1 هي:

- **CB302**: Computer Architecture
- **CB301**: Computer Networks
- **CB303**: Cryptography
- **CB304**: Introduction to Cyber-Security
- **Major elective 1**: upon selection
- **Major elective 2**: upon selection.
```

### PASS - ما متطلب CB404 Ethical Hacking؟

- Missing any-match keywords: `CB307`
- Response:

```text
عشان تاخد مادة [CB404] Ethical Hacking، محتاج تكون أخدت مادة [CB308] Real-Time Auditing & Defense قبلها.
```

### PASS - ما متطلب CB405 Penetration Testing & Vulnerabilities Discovery؟

- Response:

```text
عشان تاخد مادة [CB405] Penetration Testing & Vulnerabilities Discovery، محتاج تكون أخدت مادة Introduction to Cyber Attacks [CB307] قبلها.
```

### PASS - اذكر بعض Cybersecurity elective courses.

- Response:

```text
بالطبع! في مواد اختيارية في مجال Cybersecurity، عندك 21 ساعة اختيارية. تقدر تختار من المواد التالية:

- [CB310] Usable Security (3 CH)
- [CB311] Blockchain & Cryptocurrencies (3 CH)
- [CB312] Cyber Security for Internet of Things (3 CH)
- [CB313] Reverse Engineering & Disassemblers (3 CH)
- [CB314] Threat Detection and Mitigation (3 CH)
- [CB408] Firewalls and Web Application Firewall (3 CH)
- [CB409] Cybercrime Investigator (3 CH)
- [CB410] Cryptanalysis (3 CH)
- [CB411] Selected Topic in Networks 1 (3 CH)
- [CB412] Selected Topic in Networks 2 (3 CH)
- [CB413] Computer Networks Defense (3 CH)
- [CB414] Information Security (3 CH)
- [CS402] Theory of Computation (3 CH)
- [DS301] Data Mining & Big Data Analysis (3 CH)
- [IS306] Internet of Things (3 CH)
- [STA301] Operations Research (3 CH)

تقدر تختار من المواد دي حسب اهتماماتك!
```


## GENERAL

### PASS - hi

- Response:

```text
Hello! Welcome to the Smart Academic Advisor.

I can help you with:
  • Course information and prerequisites
  • Academic regulations
  • Available electives
  • Study guidance and academic support

How can I assist you today?
```

### PASS - hello

- Response:

```text
Hello! Welcome to the Smart Academic Advisor.

I can help you with:
  • Course information and prerequisites
  • Academic regulations
  • Available electives
  • Study guidance and academic support

How can I assist you today?
```

### PASS - مرحبا

- Response:

```text
Hello! Welcome to the Smart Academic Advisor.

I can help you with:
  • Course information and prerequisites
  • Academic regulations
  • Available electives
  • Study guidance and academic support

How can I assist you today?
```

### PASS - ازيك

- Response:

```text
Hello! Welcome to the Smart Academic Advisor.

I can help you with:
  • Course information and prerequisites
  • Academic regulations
  • Available electives
  • Study guidance and academic support

How can I assist you today?
```

### PASS - I am afraid I will fail this semester

- Response:

```text
I understand how overwhelming that feeling can be. Remember, you're not alone in this; many students experience similar worries. Let's focus on practical steps you can take to regain control and confidence in your studies.

Here are some actionable tips to help you navigate this semester:

- **Create a Study Schedule**: Break down your syllabus into smaller, manageable tasks. Allocate specific times for studying each subject to maintain a balanced approach.
  
- **Set Realistic Goals**: Instead of aiming for perfection, set achievable goals for each study session. Celebrate small victories to keep your motivation high.

- **Utilize ERU Resources**: Don't hesitate to reach out to your professors or TAs if you're struggling with specific topics. They can offer guidance and support.

- **Form Study Groups**: Connect with classmates to study together. Sharing knowledge and discussing concepts can reinforce your understanding and make studying more enjoyable.

- **Practice Self-Care**: Ensure you're taking breaks, eating well, and getting enough sleep. A healthy mind and body can significantly boost your academic performance.

You’ve got this! Believe in yourself, and take it one step at a time. If you're feeling really overwhelmed, consider visiting the university counseling services for extra support. I'm here for you if you have any other questions or need further advice! 🌟
```

### PASS - I am stressed and need study tips

- Response:

```text
I'm really sorry to hear that you're feeling stressed. It's completely normal, especially during busy academic times. Let's work together to create a plan that can help you feel more in control and focused. 

Here are some practical study tips you can try:

- **Break it Down**: Divide your study material into smaller, manageable sections. Tackle one section at a time to avoid feeling overwhelmed.
- **Create a Study Schedule**: Set specific times for studying each subject. Consistency can help reduce anxiety and improve retention.
- **Use Active Learning Techniques**: Try summarizing what you’ve learned, teaching it to someone else, or using flashcards. These methods can make studying more engaging and effective.
- **Take Regular Breaks**: Use techniques like the Pomodoro Technique (25 minutes of studying followed by a 5-minute break). This can help keep your mind fresh.
- **Reach Out for Support**: Don’t hesitate to ask your professors, TAs, or classmates if you need help with difficult topics. Collaboration can lighten the load.

Remember, it’s okay to feel stressed, but taking these small steps can help you regain your focus. You're capable of handling this! If you need more personalized support, consider visiting the university counseling services as well. 

Keep pushing forward, and don't hesitate to reach out if you have more questions! You've got this! 💪📚
```

### PASS - I feel overwhelmed and burned out

- Response:

```text
I'm really sorry to hear that you're feeling this way. It's completely understandable to feel overwhelmed, especially with the demands of academic life. Remember, you're not alone in this, and there are ways to manage these feelings. 🌟

Here are some practical tips to help you navigate through this:

- **Take Breaks:** Schedule short breaks during your study sessions. Even a 5-10 minute walk or a change of scenery can refresh your mind.
- **Prioritize Tasks:** Make a list of what needs to be done and prioritize tasks based on deadlines and importance. Focus on one task at a time.
- **Set Realistic Goals:** Break your work into smaller, achievable goals. Celebrate each small victory to keep yourself motivated.
- **Stay Connected:** Reach out to classmates or friends for study groups or just to talk. Sharing your thoughts can lighten the load.
- **Utilize ERU Resources:** Don’t hesitate to reach out to your professors, TAs, or academic advisors for support and guidance. They can provide valuable insights.

It's okay to feel this way, and taking steps to manage it is a sign of strength. Keep pushing through, and remember, you’ve got this! If you feel like you need more support, consider visiting the university counseling services. They can offer additional help. 💪

If you have any specific concerns or questions, feel free to share!
```

### PASS - I am worried about my exams

- Response:

```text
I completely understand how you feel; exam periods can be really stressful! It’s important to remember that with the right strategies, you can manage this stress and prepare effectively. Here are some practical tips to help you:

- **Create a Study Schedule**: Break down your study materials into manageable chunks and allocate specific times for each subject. This will help you stay organized and feel less overwhelmed.

- **Practice Past Papers**: Familiarize yourself with the exam format by practicing past exam questions. This can boost your confidence and help you identify areas where you need more review.

- **Take Care of Yourself**: Make sure to get enough rest, eat well, and take breaks during your study sessions. A healthy body supports a healthy mind!

- **Reach Out for Help**: Don’t hesitate to ask your professors or TAs for clarification on topics you find challenging. They are there to support you!

- **Stay Positive**: Remind yourself of your strengths and past successes. Positive self-talk can really make a difference in your mindset.

If you’re feeling really overwhelmed, please consider visiting the university counseling services for additional support. You’ve got this, and I believe in your ability to succeed! If you have any more questions or need further support, feel free to ask. 🌟
```

### PASS - انا خايف اسقط الترم ده

- Missing any-match keywords: `متفهم, الدكتور, المساعده, الاستشاره, مساعده`
- Response:

```text
متقلقش، كلنا بنمر بأوقات صعبة في دراستنا، وده شيء طبيعي. المهم إنك تتعامل مع الوضع بشكل إيجابي وتبدأ تخطط. هنا شوية نصائح ممكن تساعدك:

- **تنظيم الوقت:** حاول تعمل جدول زمني لمذاكرتك، حدد أوقات معينة للدراسة وخصص وقت للراحة.
- **تحديد الأهداف:** قسم المواد الكبيرة إلى مواضيع أصغر، وحدد هدف لكل يوم، وركز على نقطة واحدة في كل مرة.
- **المراجعة المستمرة:** حاول تراجع المعلومات بشكل دوري، مش بس قبل الامتحانات. كده هتكون المعلومات في ذاكرتك أفضل.
- **التواصل مع الدكاترة وزملائك:** لو عندك أي استفسارات، متترددش تسأل الأساتذة أو زملائك. تقدر كمان تتواصل مع المساعدين الأكاديميين لو احتجت دعم إضافي.
- **استغلال الموارد المتاحة:** اتأكد إنك تستخدم المكتبة والمصادر على الإنترنت، وكمان لو حابب، تقدر تروح لمكتب الإرشاد الأكاديمي في الجامعة.

إنت تقدر تتخطى الفترة دي! خليك متفائل واستمر في المحاولة. وإذا حسيت إن الضغط زيادة، ممكن تتواصل مع خدمات الإرشاد في الجامعة. أنا هنا لو عندك أي سؤال أو محتاج دعم إضافي! 🌟
```

### PASS - محتاج نصايح للمذاكرة

- Missing any-match keywords: `نصايح, تنظيم`
- Response:

```text
طبعًا، أنا هنا علشان أساعدك! المذاكرة ممكن تكون مرهقة أحيانًا، لكن مع بعض الخطوات البسيطة تقدر تنظم وقتك وتحقق أفضل نتائج. إليك بعض النصائح:

- **حدد أهداف واضحة**: قبل ما تبدأ مذاكرتك، حط أهداف معينة لكل جلسة. مثلاً، "هذا اليوم هركز على مادة الذكاء الاصطناعي".
  
- **استخدم تقنية بومودورو**: قسم وقت المذاكرة إلى فترات (25 دقيقة مذاكرة، 5 دقائق راحة). ده هيساعدك تحافظ على تركيزك.

- **خلق بيئة مناسبة**: تأكد إن المكان اللي بتذاكر فيه مريح وهادئ. استخدم إضاءة جيدة وابتعد عن المشتتات.

- **استعن بالموارد المتاحة**: لو عندك أي أسئلة، متترددش تسأل الأساتذة أو المساعدين الأكاديميين. هم هنا لدعمك.

- **ممارسة الاسترخاء**: خصص وقت لممارسة الرياضة أو هواية تحبها. ده هيساعدك على تخفيف الضغط.

إنت قادر على تحقيق أهدافك! لو عندك أي أسئلة أو محتاج مساعدة إضافية، أنا هنا ليك. 💪📚
```

### PASS - حاسس اني مش لاحق ومتوتر

- Missing any-match keywords: `تنظم, الدكتور`
- Response:

```text
أنا فاهم مشاعرك تمامًا، وده طبيعي جدًا في فترة الدراسة. متقلقش، إنت مش لوحدك، وفيه خطوات ممكن تساعدك تخرج من الحالة دي.

**إليك بعض النصائح:**

- **خطط لوقتك:** حاول تعمل جدول زمني للمذاكرة، وخصص وقت لكل مادة. حاول تبعد عن المشتتات خلال المذاكرة.
- **خذ فترات راحة:** بعد كل ساعة أو ساعتين من المذاكرة، خد قسط من الراحة عشان تقدر تركز أفضل.
- **حدد أولوياتك:** ركز على المهمات الأكثر أولوية، وابدأ بأصعب المواد في البداية لما تكون طاقتك عالية.
- **تواصل مع زملائك:** حاول تدرس مع زملائك في المجموعة. ده هيخليك تحس بالراحة، وكمان ممكن تستفيد من بعضكم.
- **اطلب المساعدة:** لو في حاجة مش فاهمها، متترددش تسأل الأستاذ أو مساعد التدريس (TA) بتاعك.

تذكر، كل خطوة صغيرة بتقربك لهدفك. إنت قادر على التحدي ده، وخليك واثق في نفسك. لو عاوز أي مساعدة إضافية، أنا هنا. 💪
```

### PASS - خايف من الامتحانات ومش عارف ابدا

- Missing any-match keywords: `ابدا, تنظيم, الدكتور, مساعده, خطه, الاساتذه, المستشارين`
- Response:

```text
متقلقش، دا إحساس طبيعي جدًا قبل الامتحانات! أنا هنا عشان أساعدك، وهنعدي المرحلة دي مع بعض. إليك شوية نصائح ممكن تساعدك:

- **خطط لدراستك**: حاول تعمل جدول زمني للدراسة، وتوزع المواد على الأيام. كده هتكون مرتاح أكتر وتقدر تركز على كل مادة.

- **قسم المواد**: بدلاً من الدراسة لكل المادة دفعة واحدة، قسمها لمواضيع صغيرة وادرس كل موضوع على حدة. هيساعدك تفهم المعلومات بشكل أفضل.

- **استخدم أساليب متنوعة**: جرب تستخدم الرسوم البيانية، أو الملاحظات الملونة، أو حتى التسميع مع زملائك. كل ما تستخدم أساليب مختلفة، هتتذكر أكتر.

- **استرح بشكل كويس**: خليك واخد فترات راحة قصيرة بين كل جلسة دراسية. ده هيساعدك تفضل مركز ومتحمس.

- **تواصل مع زملاءك**: حاول تذاكر مع أصدقائك أو تسألهم عن أي حاجة مش واضحة. الدراسة المشتركة بتكون مفيدة جدًا.

وأنا واثق إنك هتقدر تخطي الامتحانات بنجاح! لو حسيت إنك محتاج دعم أكتر، ممكن تتوجه لخدمات الاستشارات في الجامعة. إنت مش لوحدك في ده! 💪📚
```

### PASS - Which major should I choose, AI or Cybersecurity?

- Response:

```text
To help you decide between **Artificial Intelligence (AI)** and **Cybersecurity**, I’d like to know what you enjoy more. Here’s a quick comparison of both programs:

### About **Artificial Intelligence (AI)**:
- **Focuses on**: Machine Learning, Deep Learning, NLP, Computer Vision, Pattern Recognition, Robotics
- **Career paths**: ML Engineer, Data Scientist, AI Researcher, NLP Engineer, Computer Vision Engineer
- **Best for students who love**: Math, algorithms, building intelligent systems, research
- **Market demand**: Very high globally, growing rapidly in Egypt and the Middle East
- **Key skills**: Python, TensorFlow/PyTorch, statistics, linear algebra

### About **Cybersecurity**:
- **Focuses on**: Network Security, Ethical Hacking, Cryptography, Digital Forensics, Penetration Testing
- **Career paths**: Security Analyst, Penetration Tester, SOC Analyst, Security Consultant, Forensics Investigator
- **Best for students who love**: Problem-solving, puzzles, protecting systems, networking
- **Market demand**: Critical shortage worldwide, extremely high demand in banking/government/enterprise
- **Key skills**: Networking, Linux, security tools (Wireshark, Metasploit, Burp Suite)

### Key Considerations:
- Both programs are excellent career paths with high demand.
- You'll have a foundation in both areas due to shared Level 1-2 courses.
- **AI** is great if you're more into math and technology, while **Cybersecurity** is ideal if you enjoy problem-solving and protecting information.

Let me know what interests you more, and I can provide more tailored advice!
```

### PASS - I am confused between AI and Cybersecurity

- Response:

```text
To help you decide between **Artificial Intelligence (AI)** and **Cybersecurity**, it would be useful to know what you enjoy more. Here’s a quick comparison of both programs:

### **Artificial Intelligence (AI)**
- **Focuses on**: Machine Learning, Deep Learning, NLP, Computer Vision, Robotics.
- **Career paths**: ML Engineer, Data Scientist, AI Researcher, NLP Engineer.
- **Best for**: Students who love math, algorithms, and building intelligent systems.
- **Market demand**: Very high globally; rapidly growing in Egypt and the Middle East.
- **Key skills**: Python, TensorFlow/PyTorch, statistics.

### **Cybersecurity**
- **Focuses on**: Network Security, Ethical Hacking, Cryptography, Digital Forensics.
- **Career paths**: Security Analyst, Penetration Tester, Security Consultant.
- **Best for**: Students who enjoy problem-solving, puzzles, and protecting systems.
- **Market demand**: Critical shortage worldwide; extremely high demand in banking/government.
- **Key skills**: Networking, Linux, security tools.

### **General Notes**
- Both programs offer excellent career paths.
- Since you’ve completed Level 1 and 2 courses, you already have a foundation in both fields.
- Consider your interests: If you prefer logical problem-solving and security, go for **Cybersecurity**. If you're passionate about algorithms and building intelligent systems, choose **Artificial Intelligence (AI)**. 

Feel free to share what you enjoy more, and I can provide more tailored advice!
```

### PASS - Should I choose AI or Cyber?

- Response:

```text
To help you decide between **Artificial Intelligence (AI)** and **Cybersecurity**, I’d like to know what you enjoy most about technology. Here’s a quick comparison of both programs:

### Artificial Intelligence (AI):
- **Focuses on**: Machine Learning, Deep Learning, NLP, Computer Vision, Robotics
- **Career paths**: ML Engineer, Data Scientist, AI Researcher, NLP Engineer
- **Best for**: Students who love math, algorithms, and building intelligent systems
- **Market demand**: Very high globally, rapidly growing in Egypt and the Middle East
- **Key skills**: Python, TensorFlow/PyTorch, statistics

### Cybersecurity:
- **Focuses on**: Network Security, Ethical Hacking, Cryptography, Digital Forensics
- **Career paths**: Security Analyst, Penetration Tester, SOC Analyst, Forensics Investigator
- **Best for**: Students who enjoy problem-solving, protecting systems, and networking
- **Market demand**: Critical shortage worldwide, especially in banking and government sectors
- **Key skills**: Networking, Linux, security tools (Wireshark, Metasploit)

### Conclusion:
- Both fields offer excellent career opportunities.
- You already have a foundation in both areas from your Level 1-2 courses.
- Consider your interests: 
  - If you enjoy math and algorithms, go for **Artificial Intelligence (AI)**.
  - If you prefer problem-solving and security, choose **Cybersecurity**.

Feel free to share what you enjoy more, and I can help you further!
```

### PASS - اختار AI ولا Cyber؟

- Response:

```text
أولًا، لازم أعرف إنت بتحب إيه عشان أقدر أساعدك تختار بين البرنامجين. هنا مقارنة بسيطة بينهم:

### برنامج الذكاء الاصطناعي (AI):
- **التركيز**: تعلم الآلة، التعلم العميق، معالجة اللغة الطبيعية، رؤية الحاسوب، التعرف على الأنماط، الروبوتات.
- **مسارات العمل**: مهندس تعلم آلة، عالم بيانات، باحث في الذكاء الاصطناعي، مهندس معالجة اللغة الطبيعية، مهندس رؤية حاسوبية.
- **أفضل للطلاب الذين يحبون**: الرياضيات، الخوارزميات، بناء أنظمة ذكية، البحث.
- **طلب السوق**: مرتفع جدًا عالميًا، وبيزيد بسرعة في مصر والشرق الأوسط.
- **المهارات الأساسية**: بايثون، TensorFlow/PyTorch، الإحصاء، الجبر الخطي.

### برنامج الأمن السيبراني (Cybersecurity):
- **التركيز**: أمان الشبكات، القرصنة الأخلاقية، التشفير، الطب الشرعي الرقمي، اختبار الاختراق.
- **مسارات العمل**: محلل أمان، مختبر اختراق، محلل مركز العمليات الأمنية، مستشار أمان، محقق في الطب الشرعي.
- **أفضل للطلاب الذين يحبون**: حل المشكلات، الألغاز، حماية الأنظمة، الشبكات.
- **طلب السوق**: نقص حاد عالميًا، وطلب مرتفع جدًا في البنوك والحكومة والشركات.
- **المهارات الأساسية**: الشبكات، لينكس، أدوات الأمان (Wireshark، Metasploit، Burp Suite).

### نصيحة:
- كلا البرنامجين ممتازين وبيوفروا فرص عمل قوية.
- الدورات المشتركة في المستويات 1-2 ساعدتك تبني أساس قوي في الاثنين.
- لو عندك اهتمامات محددة، قولي عشان أقدر أنصحك بشكل أفضل.
```

### PASS - انا محتار بين الذكاء الاصطناعي والامن السيبراني

- Response:

```text
مقارنة سريعة بين الذكاء الاصطناعي Artificial Intelligence (AI) والأمن السيبراني Cybersecurity:

عشان أقدر أساعدك بشكل أفضل، ممكن تقولي إنت بتحب إيه أو إيه اللي يثير اهتمامك في مجالات الذكاء الاصطناعي أو الأمن السيبراني؟

لكن بشكل عام، هنا مقارنة سريعة بين البرنامجين:

### برنامج الذكاء الاصطناعي (AI):
- **المجالات**: تعلم الآلة، التعلم العميق، معالجة اللغة الطبيعية، رؤية الكمبيوتر، التعرف على الأنماط، الروبوتات.
- **مسارات العمل**: مهندس تعلم الآلة، عالم بيانات، باحث في الذكاء الاصطناعي، مهندس معالجة اللغة الطبيعية، مهندس رؤية الكمبيوتر.
- **الأفضل للي بيحبوا**: الرياضيات، الخوارزميات، بناء أنظمة ذكية، البحث.
- **طلب السوق**: عالي جداً عالمياً، في نمو سريع في مصر والشرق الأوسط.
- **المهارات الأساسية**: بايثون، TensorFlow/PyTorch، الإحصاء، الجبر الخطي.

### برنامج الأمن السيبراني:
- **المجالات**: أمان الشبكات، الاختراق الأخلاقي، التشفير، الطب الشرعي الرقمي، اختبار الاختراق.
- **مسارات العمل**: محلل أمان، مختبر اختراق، محلل SOC، مستشار أمان، محقق في الطب الشرعي.
- **الأفضل للي بيحبوا**: حل المشكلات، الألغاز، حماية الأنظمة، الشبكات.
- **طلب السوق**: نقص حاد عالمياً، طلب عالي جداً في البنوك والحكومة والشركات الكبيرة.
- **المهارات الأساسية**: الشبكات، لينكس، أدوات الأمان (Wireshark، Metasploit، Burp Suite).

**نقاط مهمة:**
- كلا البرنامجين مسارات مهنية ممتازة.
- المواد المشتركة في المستوى 1-2 تعني إنك عندك أساس في الاثنين.
- كل برنامج له ميزاته وعيوبه، فاختيارك يعتمد على اهتماماتك الشخصية.

إذا عندك جوانب معينة تحب تركز عليها، قولي وأنا هساعدك أكتر!
```

### PASS - ايه الفرق بين AI و Cybersecurity؟

- Response:

```text
مقارنة سريعة بين الذكاء الاصطناعي Artificial Intelligence (AI) والأمن السيبراني Cybersecurity:

أكيد، هقولك الفرق بين البرنامجين:

### برنامج **Artificial Intelligence (AI)**:
- **التركيز**: تعلم الآلة، التعلم العميق، معالجة اللغة الطبيعية، رؤية الكمبيوتر، التعرف على الأنماط، الروبوتات.
- **مسارات الوظائف**: مهندس تعلم آلة، عالم بيانات، باحث في الذكاء الاصطناعي، مهندس معالجة لغة طبيعية، مهندس رؤية كمبيوتر.
- **مناسب للطلبة الذين يحبون**: الرياضيات، الخوارزميات، بناء أنظمة ذكية، البحث.
- **الطلب في السوق**: مرتفع جداً عالمياً، ويزداد بسرعة في مصر والشرق الأوسط.
- **المهارات الأساسية**: بايثون، TensorFlow/PyTorch، الإحصاء، الجبر الخطي.

### برنامج **Cybersecurity**:
- **التركيز**: أمان الشبكات، القرصنة الأخلاقية، التشفير، التحقيقات الرقمية، اختبار الاختراق.
- **مسارات الوظائف**: محلل أمان، مختبر اختراق، محلل SOC، مستشار أمان، محقق جنائي.
- **مناسب للطلبة الذين يحبون**: حل المشكلات، الألغاز، حماية الأنظمة، الشبكات.
- **الطلب في السوق**: نقص حاد عالمياً، وطلب مرتفع جداً في البنوك/الحكومة/الشركات.
- **المهارات الأساسية**: الشبكات، لينكس، أدوات الأمان (Wireshark، Metasploit، Burp Suite).

### نصيحتي:
- كلكم عندكم خلفية جيدة من المواد المشتركة في المستوى الأول والثاني، فأنتم مؤهلين للاتجاهين.
- كلاهما مسارات مهنية ممتازة، لكن يعتمد الاختيار على اهتماماتك.
- لو بتحب الرياضيات والتكنولوجيا، ممكن تفضل **Artificial Intelligence (AI)**.
- لو بتحب حل الألغاز وحماية الأنظمة، **Cybersecurity** هي الخيار المناسب.

لو عندك اهتمامات معينة أو تفضيلات، خبرني وهنساعدك أكثر!
```

### PASS - What are the available elective courses for this semester?

- Missing any-match keywords: `no electives`
- Response:

```text
For the Spring-2026 term, the available elective courses are:

1. **Cloud Computing**
   - Course Code: [Insert Course Code]
   - Instructor: [Insert Instructor Name]
   - Time: [Insert Class Time]
   - Credits: [Insert Credits]

2. **Big Data**
   - Course Code: [Insert Course Code]
   - Instructor: [Insert Instructor Name]
   - Time: [Insert Class Time]
   - Credits: [Insert Credits]

If you have any specific interests, I can help you decide which elective might be best for you!
```

### PASS - ايه المواد الاختيارية المتاحة ليا اسجلها الترم ده؟

- Missing any-match keywords: `elective`
- Response:

```text
المواد الاختيارية المتاحة لك في الترم الحالي (ربيع 2026) هي:

1. **Cloud Computing**
   - **الكود:** AI-CC101
   - **المدرس:** د. أحمد سعيد
   - **الوقت:** الثلاثاء، 10:00 - 12:00
   - **الساعات المعتمدة:** 3

2. **Big Data**
   - **الكود:** AI-BD102
   - **المدرس:** د. مريم علي
   - **الوقت:** الخميس، 14:00 - 16:00
   - **الساعات المعتمدة:** 3

إذا كنت محتاج مساعدة في اختيار مادة معينة، قولي!
```

### PASS - Who is the dean of the faculty?

- Response:

```text
I couldn't find this specific question in our course data or regulation documents.
```

### PASS - مين عميد الكلية؟

- Response:

```text
مش لاقي السؤال ده في بيانات المواد أو مستندات اللوايح عندي.
```

### PASS - What is the weather today?

- Response:

```text
I couldn't find this specific question in our course data or regulation documents.
```

### PASS - مين احسن لاعب كوره في العالم؟

- Response:

```text
مش لاقي السؤال ده في بيانات المواد أو مستندات اللوايح عندي.
```

### PASS - Can you tell me the tuition fees?

- Missing any-match keywords: `مش لاقي السؤال`
- Response:

```text
I couldn't find this specific question in our course data or regulation documents.
```

### PASS - فين الكافتيريا؟

- Missing any-match keywords: `couldn't find this specific question`
- Response:

```text
مش لاقي السؤال ده في بيانات المواد أو مستندات اللوايح عندي.
```

### PASS - What can you help me with?

- Response:

```text
Hello! Welcome to the Smart Academic Advisor.

I can help you with:
  • Course information and prerequisites
  • Academic regulations
  • Available electives
  • Study guidance and academic support

How can I assist you today?
```

### PASS - بتساعد في ايه؟

- Missing any-match keywords: `materials, courses`
- Response:

```text
Hello! Welcome to the Smart Academic Advisor.

I can help you with:
  • Course information and prerequisites
  • Academic regulations
  • Available electives
  • Study guidance and academic support

How can I assist you today?
```

### PASS - new

- Response:

```text
Hello! Welcome to the Smart Academic Advisor.

I can help you with:
  • Course information and prerequisites
  • Academic regulations
  • Available electives
  • Study guidance and academic support

How can I assist you today?
```

### PASS - /start

- Response:

```text
Hello! Welcome to the Smart Academic Advisor.

I can help you with:
  • Course information and prerequisites
  • Academic regulations
  • Available electives
  • Study guidance and academic support

How can I assist you today?
```

# Production KG Prerequisite Checks

- Target: `https://smart-academic-advisor-api.vercel.app/chat`
- Date: 2026-05-11
- Total: 27/50 passed
- Scope: 25 English and 25 Egyptian Arabic prerequisite / after-course questions.

## Summary

| # | Language | Result | Missing markers |
|---:|---|---|---|
| 1 | English | PASS | - |
| 2 | English | PASS | - |
| 3 | English | PASS | - |
| 4 | English | PASS | - |
| 5 | English | PASS | - |
| 6 | English | PASS | - |
| 7 | English | PASS | - |
| 8 | English | PASS | - |
| 9 | English | PASS | - |
| 10 | English | FAIL | MTH103, MTH104 |
| 11 | English | PASS | - |
| 12 | English | PASS | - |
| 13 | English | PASS | - |
| 14 | English | PASS | - |
| 15 | English | PASS | - |
| 16 | English | FAIL | CB308, CB314, CB408 |
| 17 | English | PASS | - |
| 18 | English | FAIL | CB309 |
| 19 | English | PASS | - |
| 20 | English | FAIL | SW303, SW401 |
| 21 | English | PASS | - |
| 22 | English | PASS | - |
| 23 | English | PASS | - |
| 24 | English | FAIL | AI407 |
| 25 | English | PASS | - |
| 26 | Egyptian Arabic | FAIL | AI401, AI304 |
| 27 | Egyptian Arabic | PASS | - |
| 28 | Egyptian Arabic | FAIL | AI201, MTH104 |
| 29 | Egyptian Arabic | FAIL | CS203, CS204, SW201 |
| 30 | Egyptian Arabic | FAIL | AI301 |
| 31 | Egyptian Arabic | FAIL | CB305, CB306, CB307 |
| 32 | Egyptian Arabic | FAIL | CB301, CB304 |
| 33 | Egyptian Arabic | PASS | - |
| 34 | Egyptian Arabic | PASS | - |
| 35 | Egyptian Arabic | FAIL | MTH103, MTH104 |
| 36 | Egyptian Arabic | PASS | - |
| 37 | Egyptian Arabic | FAIL | CS201, CS205, IS201 |
| 38 | Egyptian Arabic | FAIL | IS101, CS102 |
| 39 | Egyptian Arabic | FAIL | AI303, AI308, AI411 |
| 40 | Egyptian Arabic | FAIL | AI301 |
| 41 | Egyptian Arabic | FAIL | CB308, CB314, CB408 |
| 42 | Egyptian Arabic | FAIL | CB308 |
| 43 | Egyptian Arabic | PASS | - |
| 44 | Egyptian Arabic | FAIL | ELC101 |
| 45 | Egyptian Arabic | FAIL | SW303, SW401 |
| 46 | Egyptian Arabic | PASS | - |
| 47 | Egyptian Arabic | FAIL | AI410 |
| 48 | Egyptian Arabic | PASS | - |
| 49 | Egyptian Arabic | FAIL | AI407 |
| 50 | Egyptian Arabic | FAIL | CB303 |

## Detailed Results

### 1. English - PASS

**Question:** What are the prerequisites for AI406?

**Expected markers:** AI401, AI304

**Production answer:**

```text
Prerequisites for [AI406] AI Applications:
- Core Requirements: Computer Vision [AI304], Intelligent Algorithms [AI401]

- Hint: Ask for the full chain to see all dependencies.
```

### 2. English - PASS

**Question:** After I finish AI301, what courses does it unlock?

**Expected markers:** AI302, AI304, AI403

**Production answer:**

```text
[AI301] Machine Learning is a prerequisite for:
- Natural Language Processing [AI302]
- Computer Vision [AI304]
- Pattern Recognition [AI305]
- Intelligent Algorithms [AI401]
- Deep Learning [AI403]
- Graduation Project 1 [AI404]
- Multi Agent Systems [AI405]
- Computational Learning Theory [AI307]
- Cognitive Modeling [AI408]
- AI for Robotics [AI413]
```

### 3. English - PASS

**Question:** What do I need before Machine Learning?

**Expected markers:** AI201, MTH104

**Production answer:**

```text
Prerequisites for [AI301] Machine Learning:
- Core Requirements: Introduction to Artificial Intelligence [AI201], Probability and Statistics 1 [MTH104]

- Hint: Ask for the full chain to see all dependencies.
```

### 4. English - PASS

**Question:** What future courses open after CS201?

**Expected markers:** CS203, CS204, SW201

**Production answer:**

```text
[CS201] Object Oriented Programming is a prerequisite for:
- Data Structures [CS203]
- Operating Systems [CS204]
- Software Engineering [SW201]
- Computer Graphics [CS307]
- Software Development for Mobile Devices [SW305]
- Computer Networks [CB301]
- Software Security [CB306]
```

### 5. English - PASS

**Question:** What are the prerequisites for Deep Learning?

**Expected markers:** AI301

**Production answer:**

```text
Prerequisites for [AI403] Deep Learning:
- Core Requirements: Machine Learning [AI301]

- Hint: Ask for the full chain to see all dependencies.
```

### 6. English - PASS

**Question:** What can I take after CB304?

**Expected markers:** CB305, CB306, CB307

**Production answer:**

```text
[CB304] Introduction to Cyber-Security is a prerequisite for:
- Network Security [CB305]
- Software Security [CB306]
- Introduction to Cyber Attacks [CB307]
- Digital Forensics [CB402]
- Graduation Project 1 [CB406]
- Usable Security [CB310]
- Reverse Engineering & Disassemblers [CB313]
- Information Security [CB414]
```

### 7. English - PASS

**Question:** What are the prerequisites for Network Security?

**Expected markers:** CB301, CB304

**Production answer:**

```text
Prerequisites for [CB305] Network Security:
- Core Requirements: Computer Networks [CB301], Introduction to Cyber-Security [CB304]

- Hint: Ask for the full chain to see all dependencies.
```

### 8. English - PASS

**Question:** Which courses does Cryptography unlock?

**Expected markers:** CB403, CB311, CB410

**Production answer:**

```text
[CB303] Cryptography is a prerequisite for:
- Advanced Cryptography [CB403]
- Blockchain & Cryptocurrencies [CB311]
- Cryptanalysis [CB410]
```

### 9. English - PASS

**Question:** What are the prerequisites for AI407?

**Expected markers:** AI404

**Production answer:**

```text
Prerequisites for [AI407] Graduation Project 2:
- Core Requirements: Graduation Project 1 [AI404]

- Hint: Ask for the full chain to see all dependencies.
```

### 10. English - FAIL

**Question:** What does MTH101 open later?

**Expected markers:** MTH103, MTH104

**Production answer:**

```text
I couldn't find this specific question in our course data or regulation documents.
```

### 11. English - PASS

**Question:** What are the prerequisites for Mathematics 3?

**Expected markers:** MTH103

**Production answer:**

```text
Prerequisites for [MTH201] Mathematics 3:
- Core Requirements: Mathematics 2 [MTH103]

- Hint: Ask for the full chain to see all dependencies.
```

### 12. English - PASS

**Question:** After CS102, which courses become available?

**Expected markers:** CS201, CS205, IS201

**Production answer:**

```text
[CS102] Structured Programming is a prerequisite for:
- Object Oriented Programming [CS201]
- Algorithms [CS205]
- Database Systems [IS201]
```

### 13. English - PASS

**Question:** What are the prerequisites for Database Systems?

**Expected markers:** IS101, CS102

**Production answer:**

```text
Prerequisites for [IS201] Database Systems:
- Core Requirements: Structured Programming [CS102], Fundamentals of Information Systems [IS101]

- Hint: Ask for the full chain to see all dependencies.
```

### 14. English - PASS

**Question:** What courses come after AI302?

**Expected markers:** AI303, AI308, AI411

**Production answer:**

```text
[AI302] Natural Language Processing is a prerequisite for:
- Speech Recognition [AI303]
- Language Modeling [AI308]
- Language and Speech Technology [AI411]
- Statistical Language Modeling [AI412]
```

### 15. English - PASS

**Question:** What are the prerequisites for Computer Vision?

**Expected markers:** AI301

**Production answer:**

```text
Prerequisites for [AI304] Computer Vision:
- Core Requirements: Machine Learning [AI301]

- Hint: Ask for the full chain to see all dependencies.
```

### 16. English - FAIL

**Question:** If I complete CB305, what does it unlock?

**Expected markers:** CB308, CB314, CB408

**Production answer:**

```text
I couldn't find this specific question in our course data or regulation documents.
```

### 17. English - PASS

**Question:** What are the prerequisites for Ethical Hacking?

**Expected markers:** CB308

**Production answer:**

```text
Prerequisites for [CB404] Ethical Hacking:
- Core Requirements: Real-Time Auditing & Defense [CB308]

- Hint: Ask for the full chain to see all dependencies.
```

### 18. English - FAIL

**Question:** What courses require ELC201?

**Expected markers:** CB309

**Production answer:**

```text
Course Info: [ELC201] Logic Design
- Credits: 3
- Level: 2
- Description: Standard core course.
```

### 19. English - PASS

**Question:** What are the prerequisites for Logic Design?

**Expected markers:** ELC101

**Production answer:**

```text
Prerequisites for [ELC201] Logic Design:
- Core Requirements: Electronics [ELC101]

- Hint: Ask for the full chain to see all dependencies.
```

### 20. English - FAIL

**Question:** What does Software Engineering unlock?

**Expected markers:** SW303, SW401

**Production answer:**

```text
I couldn't find this specific question in our course data or regulation documents.
```

### 21. English - PASS

**Question:** What are the prerequisites for Software Testing and Quality Assurance?

**Expected markers:** SW201

**Production answer:**

```text
Prerequisites for [SW401] Software Testing & Quality Assurance:
- Core Requirements: Software Engineering [SW201]

- Hint: Ask for the full chain to see all dependencies.
```

### 22. English - PASS

**Question:** After Deep Learning, what can I take?

**Expected markers:** AI410

**Production answer:**

```text
[AI403] Deep Learning is a prerequisite for:
- Cognitive Natural Networks [AI410]
```

### 23. English - PASS

**Question:** What are the prequesits for AI Applications?

**Expected markers:** AI401, AI304

**Production answer:**

```text
Courses:

Artificial Intelligence:
- [CS101] Introduction to Computer Science - 3 credits
- [CS102] Structured Programming - 3 credits
- [CS103] Discrete Structure - 3 credits
- [IS101] Fundamentals of Information Systems - 3 credits
- [HM001] English Language 1 - 2 credits
- [HM002] English Language 2 - 2 credits
- [ELC101] Electronics - 3 credits
- [MTH101] Mathematics 1 - 3 credits
- [MTH102] Linear Algebra - 3 credits
- [MTH103] Mathematics 2 - 3 credits
- [MTH104] Probability and Statistics 1 - 3 credits
- [PH101] Physics - 3 credits
- [CS201] Object Oriented Programming - 3 credits
- [CS202] Signal and System - 3 credits
- [CS203] Data Structures - 3 credits
- [CS204] Operating Systems - 3 credits
- [CS205] Algorithms - 3 credits
- [IS201] Database Systems - 3 credits
- [IS202] System Analysis and Design - 3 credits
- [SW201] Software Engineering - 3 credits
- [AI201] Introduction to Artificial Intelligence - 3 credits
- [HM003] Human Rights & Anticorruption - 2 credits
- [HM004] Russian Language 1 - 2 credits
- [HM005] Russian Language 2 - 2 credits
- [ELC201] Logic Design - 3 credits
- [MTH201] Mathematics 3 - 3 credits
- [MTH202] Probability and Statistics 2 - 3 credits
- [MTH203] Numerical Analysis - 3 credits
- [HM006] Scientific Thinking - 2 credits
- [HM007] Technical Writing - 1 credits
- [HM008] Scientific Research Methodology - 2 credits
- [HM009] Scientific Research Methodology 2 - 2 credits
- [HM010] Russian Language 3 - 2 credits
- [AI301] Machine Learning - 3 credits
- [AI302] Natural Language Processing - 3 credits
- [AI303] Speech Recognition - 3 credits
- [AI304] Computer Vision - 3 credits
- [AI305] Pattern Recognition - 3 credits
- [AI306] Computational Perception - 3 credits
- [CS302] Computer Architecture and Organization - 3 credits
- [DS307] Cloud Computing - 3 credits
- [SW303] User Interface Design - 3 credits
- [AI307] Computational Learning Theory - 3 credits
- [AI308] Language Modeling - 3 credits
- [AI309] User Models - 3 credits
- [AI310] Handwriting Recognition - 3 credits
- [AI311] Expert Systems - 3 credits
- [AI312] Architecture of Intelligence - 3 credits
- [AI314] Artificial Intelligence in Games - 3 credits
- [CS301] Operations Research - 3 credits
- [CS303] Image Processing - 3 credits
- [CS307] Computer Graphics - 3 credits
- [CS309] Embedded Systems - 3 credits
- [ROB302] Fundamental of Cognitive Interaction with Robots - 3 credits
- [SW305] Software Development for Mobile Devices - 3 credits
- [AI401] Intelligent Algorithms - 3 credits
- [AI402] Computational Cognitive Systems - 3 credits
- [AI403] Deep Learning - 3 credits
- [AI404] Graduation Project 1 - 3 credits
- [AI405] Multi Agent Systems - 3 credits
- [AI406] AI Applications - 3 credits
- [AI407] Graduation Project 2 - 3 credits
- [AI408] Cognitive Modeling - 3 credits
- [AI409] Cognitive Engineering - 3 credits
- [AI410] Cognitive Natural Networks - 3 credits
- [AI411] Language and Speech Technology - 3 credits
- [AI412] Statistical Language Modeling - 3 credits
- [AI413] AI for Robotics - 3 credits
- [AI415] Selected Topic in AI 1 - 3 credits
- [AI416] Selected Topic in AI 2 - 3 credits
- [CS403] Advanced Knowledge Representation and Reasoning - 3 credits
- [SW401] Software Testing & Quality Assurance - 3 credits
```

### 24. English - FAIL

**Question:** What comes after Graduation Project 1 in AI?

**Expected markers:** AI407

**Production answer:**

```text
After Graduation Project 1 in the Artificial Intelligence program, the next course is Graduation Project 2. Here are the details:

- Graduation Project 2
- Credits: 2
- Prerequisite: Graduation Project 1 (AI404).
```

### 25. English - PASS

**Question:** What are the prerequisites for Advanced Cryptography?

**Expected markers:** CB303

**Production answer:**

```text
Prerequisites for [CB303] Cryptography:
- Core Requirements: Linear Algebra [MTH102]

- Hint: Ask for the full chain to see all dependencies.
```

### 26. Egyptian Arabic - FAIL

**Question:** ايه المتطلبات بتاعت AI406؟

**Expected markers:** AI401, AI304

**Production answer:**

```text
مش لاقي السؤال ده في بيانات المواد أو مستندات اللوايح عندي.
```

### 27. Egyptian Arabic - PASS

**Question:** لو خلصت AI301 هتفتحلي مواد ايه؟

**Expected markers:** AI302, AI304, AI403

**Production answer:**

```text
لو خلصت [AI301] Machine Learning، المواد اللي هتفتحلك هي:
- Natural Language Processing [AI302]
- Computer Vision [AI304]
- Pattern Recognition [AI305]
- Intelligent Algorithms [AI401]
- Deep Learning [AI403]
- Graduation Project 1 [AI404]
- Multi Agent Systems [AI405]
- Computational Learning Theory [AI307]
- Cognitive Modeling [AI408]
- AI for Robotics [AI413]
```

### 28. Egyptian Arabic - FAIL

**Question:** لازم اكون واخد ايه قبل Machine Learning؟

**Expected markers:** AI201, MTH104

**Production answer:**

```text
مش لاقي السؤال ده في بيانات المواد أو مستندات اللوايح عندي.
```

### 29. Egyptian Arabic - FAIL

**Question:** CS201 بتفتحلي ايه بعد كده؟

**Expected markers:** CS203, CS204, SW201

**Production answer:**

```text
مش لاقي السؤال ده في بيانات المواد أو مستندات اللوايح عندي.
```

### 30. Egyptian Arabic - FAIL

**Question:** ايه المطلوب قبل Deep Learning؟

**Expected markers:** AI301

**Production answer:**

```text
مش لاقي السؤال ده في بيانات المواد أو مستندات اللوايح عندي.
```

### 31. Egyptian Arabic - FAIL

**Question:** بعد ما اخلص CB304 اقدر اخد ايه؟

**Expected markers:** CB305, CB306, CB307

**Production answer:**

```text
مش لاقي السؤال ده في بيانات المواد أو مستندات اللوايح عندي.
```

### 32. Egyptian Arabic - FAIL

**Question:** Network Security محتاجه ايه قبلها؟

**Expected markers:** CB301, CB304

**Production answer:**

```text
مش لاقي السؤال ده في بيانات المواد أو مستندات اللوايح عندي.
```

### 33. Egyptian Arabic - PASS

**Question:** Cryptography بتفتح مواد ايه؟

**Expected markers:** CB403, CB311, CB410

**Production answer:**

```text
لو خلصت [CB303] Cryptography، المواد اللي هتفتحلك هي:
- Advanced Cryptography [CB403]
- Blockchain & Cryptocurrencies [CB311]
- Cryptanalysis [CB410]
```

### 34. Egyptian Arabic - PASS

**Question:** ايه متطلبات AI407؟

**Expected markers:** AI404

**Production answer:**

```text
متطلبات [AI407] Graduation Project 2:
- المتطلبات الأساسية Graduation Project 1 [AI404]

- ملاحظة: اسأل عن السلسلة الكاملة لو عايز تشوف كل المتطلبات.
```

### 35. Egyptian Arabic - FAIL

**Question:** MTH101 بتفتحلي ايه؟

**Expected markers:** MTH103, MTH104

**Production answer:**

```text
مش لاقي السؤال ده في بيانات المواد أو مستندات اللوايح عندي.
```

### 36. Egyptian Arabic - PASS

**Question:** Mathematics 3 محتاجه ايه؟

**Expected markers:** MTH103

**Production answer:**

```text
متطلبات [MTH201] Mathematics 3:
- المتطلبات الأساسية Mathematics 2 [MTH103]

- ملاحظة: اسأل عن السلسلة الكاملة لو عايز تشوف كل المتطلبات.
```

### 37. Egyptian Arabic - FAIL

**Question:** بعد CS102 ايه المواد اللي بتتفتح؟

**Expected markers:** CS201, CS205, IS201

**Production answer:**

```text
متطلبات [CS102] Structured Programming:
- المتطلبات الأساسية Introduction to Computer Science [CS101]

- ملاحظة: اسأل عن السلسلة الكاملة لو عايز تشوف كل المتطلبات.
```

### 38. Egyptian Arabic - FAIL

**Question:** Database Systems لازم قبلها ايه؟

**Expected markers:** IS101, CS102

**Production answer:**

```text
مش لاقي السؤال ده في بيانات المواد أو مستندات اللوايح عندي.
```

### 39. Egyptian Arabic - FAIL

**Question:** AI302 بتفتح ايه بعد كده؟

**Expected markers:** AI303, AI308, AI411

**Production answer:**

```text
مش لاقي السؤال ده في بيانات المواد أو مستندات اللوايح عندي.
```

### 40. Egyptian Arabic - FAIL

**Question:** Computer Vision متطلباتها ايه؟

**Expected markers:** AI301

**Production answer:**

```text
مش لاقي السؤال ده في بيانات المواد أو مستندات اللوايح عندي.
```

### 41. Egyptian Arabic - FAIL

**Question:** لو خلصت CB305 هيفتحلي ايه؟

**Expected markers:** CB308, CB314, CB408

**Production answer:**

```text
مش لاقي السؤال ده في بيانات المواد أو مستندات اللوايح عندي.
```

### 42. Egyptian Arabic - FAIL

**Question:** Ethical Hacking محتاجه ايه قبلها؟

**Expected markers:** CB308

**Production answer:**

```text
مش لاقي السؤال ده في بيانات المواد أو مستندات اللوايح عندي.
```

### 43. Egyptian Arabic - PASS

**Question:** ELC201 بتفتح اي مواد؟

**Expected markers:** CB309

**Production answer:**

```text
لو خلصت [ELC201] Logic Design، المواد اللي هتفتحلك هي:
- Hardware Security [CB309]
```

### 44. Egyptian Arabic - FAIL

**Question:** Logic Design متطلبها ايه؟

**Expected markers:** ELC101

**Production answer:**

```text
مش لاقي السؤال ده في بيانات المواد أو مستندات اللوايح عندي.
```

### 45. Egyptian Arabic - FAIL

**Question:** Software Engineering بتفتح ايه؟

**Expected markers:** SW303, SW401

**Production answer:**

```text
مش لاقي السؤال ده في بيانات المواد أو مستندات اللوايح عندي.
```

### 46. Egyptian Arabic - PASS

**Question:** Software Testing محتاجه انهي مادة قبلها؟

**Expected markers:** SW201

**Production answer:**

```text
متطلبات [SW401] Software Testing & Quality Assurance:
- المتطلبات الأساسية Software Engineering [SW201]

- ملاحظة: اسأل عن السلسلة الكاملة لو عايز تشوف كل المتطلبات.
```

### 47. Egyptian Arabic - FAIL

**Question:** بعد Deep Learning اقدر اخد ايه؟

**Expected markers:** AI410

**Production answer:**

```text
مش لاقي السؤال ده في بيانات المواد أو مستندات اللوايح عندي.
```

### 48. Egyptian Arabic - PASS

**Question:** ايه البري ريكويست بتاع AI Applications؟

**Expected markers:** AI401, AI304

**Production answer:**

```text
المواد:

Artificial Intelligence:
- [CS101] Introduction to Computer Science - 3 ساعة معتمدة
- [CS102] Structured Programming - 3 ساعة معتمدة
- [CS103] Discrete Structure - 3 ساعة معتمدة
- [IS101] Fundamentals of Information Systems - 3 ساعة معتمدة
- [HM001] English Language 1 - 2 ساعة معتمدة
- [HM002] English Language 2 - 2 ساعة معتمدة
- [ELC101] Electronics - 3 ساعة معتمدة
- [MTH101] Mathematics 1 - 3 ساعة معتمدة
- [MTH102] Linear Algebra - 3 ساعة معتمدة
- [MTH103] Mathematics 2 - 3 ساعة معتمدة
- [MTH104] Probability and Statistics 1 - 3 ساعة معتمدة
- [PH101] Physics - 3 ساعة معتمدة
- [CS201] Object Oriented Programming - 3 ساعة معتمدة
- [CS202] Signal and System - 3 ساعة معتمدة
- [CS203] Data Structures - 3 ساعة معتمدة
- [CS204] Operating Systems - 3 ساعة معتمدة
- [CS205] Algorithms - 3 ساعة معتمدة
- [IS201] Database Systems - 3 ساعة معتمدة
- [IS202] System Analysis and Design - 3 ساعة معتمدة
- [SW201] Software Engineering - 3 ساعة معتمدة
- [AI201] Introduction to Artificial Intelligence - 3 ساعة معتمدة
- [HM003] Human Rights & Anticorruption - 2 ساعة معتمدة
- [HM004] Russian Language 1 - 2 ساعة معتمدة
- [HM005] Russian Language 2 - 2 ساعة معتمدة
- [ELC201] Logic Design - 3 ساعة معتمدة
- [MTH201] Mathematics 3 - 3 ساعة معتمدة
- [MTH202] Probability and Statistics 2 - 3 ساعة معتمدة
- [MTH203] Numerical Analysis - 3 ساعة معتمدة
- [HM006] Scientific Thinking - 2 ساعة معتمدة
- [HM007] Technical Writing - 1 ساعة معتمدة
- [HM008] Scientific Research Methodology - 2 ساعة معتمدة
- [HM009] Scientific Research Methodology 2 - 2 ساعة معتمدة
- [HM010] Russian Language 3 - 2 ساعة معتمدة
- [AI301] Machine Learning - 3 ساعة معتمدة
- [AI302] Natural Language Processing - 3 ساعة معتمدة
- [AI303] Speech Recognition - 3 ساعة معتمدة
- [AI304] Computer Vision - 3 ساعة معتمدة
- [AI305] Pattern Recognition - 3 ساعة معتمدة
- [AI306] Computational Perception - 3 ساعة معتمدة
- [CS302] Computer Architecture and Organization - 3 ساعة معتمدة
- [DS307] Cloud Computing - 3 ساعة معتمدة
- [SW303] User Interface Design - 3 ساعة معتمدة
- [AI307] Computational Learning Theory - 3 ساعة معتمدة
- [AI308] Language Modeling - 3 ساعة معتمدة
- [AI309] User Models - 3 ساعة معتمدة
- [AI310] Handwriting Recognition - 3 ساعة معتمدة
- [AI311] Expert Systems - 3 ساعة معتمدة
- [AI312] Architecture of Intelligence - 3 ساعة معتمدة
- [AI314] Artificial Intelligence in Games - 3 ساعة معتمدة
- [CS301] Operations Research - 3 ساعة معتمدة
- [CS303] Image Processing - 3 ساعة معتمدة
- [CS307] Computer Graphics - 3 ساعة معتمدة
- [CS309] Embedded Systems - 3 ساعة معتمدة
- [ROB302] Fundamental of Cognitive Interaction with Robots - 3 ساعة معتمدة
- [SW305] Software Development for Mobile Devices - 3 ساعة معتمدة
- [AI401] Intelligent Algorithms - 3 ساعة معتمدة
- [AI402] Computational Cognitive Systems - 3 ساعة معتمدة
- [AI403] Deep Learning - 3 ساعة معتمدة
- [AI404] Graduation Project 1 - 3 ساعة معتمدة
- [AI405] Multi Agent Systems - 3 ساعة معتمدة
- [AI406] AI Applications - 3 ساعة معتمدة
- [AI407] Graduation Project 2 - 3 ساعة معتمدة
- [AI408] Cognitive Modeling - 3 ساعة معتمدة
- [AI409] Cognitive Engineering - 3 ساعة معتمدة
- [AI410] Cognitive Natural Networks - 3 ساعة معتمدة
- [AI411] Language and Speech Technology - 3 ساعة معتمدة
- [AI412] Statistical Language Modeling - 3 ساعة معتمدة
- [AI413] AI for Robotics - 3 ساعة معتمدة
- [AI415] Selected Topic in AI 1 - 3 ساعة معتمدة
- [AI416] Selected Topic in AI 2 - 3 ساعة معتمدة
- [CS403] Advanced Knowledge Representation and Reasoning - 3 ساعة معتمدة
- [SW401] Software Testing & Quality Assurance - 3 ساعة معتمدة
```

### 49. Egyptian Arabic - FAIL

**Question:** Graduation Project 1 في AI بيفتح ايه؟

**Expected markers:** AI407

**Production answer:**

```text
مشروع التخرج 1 في برنامج الذكاء الاصطناعي (AI) يتطلب ما يلي:

- الكود: AI404
- الساعات المعتمدة: 2
- المتطلبات السابقة: لا توجد متطلبات سابقة محددة لمشروع التخرج 1.

إذا كان لديك أي استفسارات أخرى، لا تتردد في السؤال!
```

### 50. Egyptian Arabic - FAIL

**Question:** Advanced Cryptography محتاجه ايه؟

**Expected markers:** CB303

**Production answer:**

```text
مش لاقي السؤال ده في بيانات المواد أو مستندات اللوايح عندي.
```

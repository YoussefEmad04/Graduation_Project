# Production KG Prerequisite Checks

- Target: `https://smart-academic-advisor-api.vercel.app/chat`
- Date: 2026-05-11
- Total: 50/50 passed
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
| 10 | English | PASS | - |
| 11 | English | PASS | - |
| 12 | English | PASS | - |
| 13 | English | PASS | - |
| 14 | English | PASS | - |
| 15 | English | PASS | - |
| 16 | English | PASS | - |
| 17 | English | PASS | - |
| 18 | English | PASS | - |
| 19 | English | PASS | - |
| 20 | English | PASS | - |
| 21 | English | PASS | - |
| 22 | English | PASS | - |
| 23 | English | PASS | - |
| 24 | English | PASS | - |
| 25 | English | PASS | - |
| 26 | Egyptian Arabic | PASS | - |
| 27 | Egyptian Arabic | PASS | - |
| 28 | Egyptian Arabic | PASS | - |
| 29 | Egyptian Arabic | PASS | - |
| 30 | Egyptian Arabic | PASS | - |
| 31 | Egyptian Arabic | PASS | - |
| 32 | Egyptian Arabic | PASS | - |
| 33 | Egyptian Arabic | PASS | - |
| 34 | Egyptian Arabic | PASS | - |
| 35 | Egyptian Arabic | PASS | - |
| 36 | Egyptian Arabic | PASS | - |
| 37 | Egyptian Arabic | PASS | - |
| 38 | Egyptian Arabic | PASS | - |
| 39 | Egyptian Arabic | PASS | - |
| 40 | Egyptian Arabic | PASS | - |
| 41 | Egyptian Arabic | PASS | - |
| 42 | Egyptian Arabic | PASS | - |
| 43 | Egyptian Arabic | PASS | - |
| 44 | Egyptian Arabic | PASS | - |
| 45 | Egyptian Arabic | PASS | - |
| 46 | Egyptian Arabic | PASS | - |
| 47 | Egyptian Arabic | PASS | - |
| 48 | Egyptian Arabic | PASS | - |
| 49 | Egyptian Arabic | PASS | - |
| 50 | Egyptian Arabic | PASS | - |

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

### 10. English - PASS

**Question:** What does MTH101 open later?

**Expected markers:** MTH103, MTH104

**Production answer:**

```text
[MTH101] Mathematics 1 is a prerequisite for:
- Mathematics 2 [MTH103]
- Probability and Statistics 1 [MTH104]
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

### 16. English - PASS

**Question:** If I complete CB305, what does it unlock?

**Expected markers:** CB308, CB314, CB408

**Production answer:**

```text
[CB305] Network Security is a prerequisite for:
- Real-Time Auditing & Defense [CB308]
- Threat Detection and Mitigation [CB314]
- Firewalls and Web Application Firewall [CB408]
- Computer Networks Defense [CB413]
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

### 18. English - PASS

**Question:** What courses require ELC201?

**Expected markers:** CB309

**Production answer:**

```text
[ELC201] Logic Design is a prerequisite for:
- Hardware Security [CB309]
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

### 20. English - PASS

**Question:** What does Software Engineering unlock?

**Expected markers:** SW303, SW401

**Production answer:**

```text
[SW201] Software Engineering is a prerequisite for:
- User Interface Design [SW303]
- Software Testing & Quality Assurance [SW401]
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
Prerequisites for [AI406] AI Applications:
- Core Requirements: Computer Vision [AI304], Intelligent Algorithms [AI401]

- Hint: Ask for the full chain to see all dependencies.
```

### 24. English - PASS

**Question:** What comes after Graduation Project 1 in AI?

**Expected markers:** AI407

**Production answer:**

```text
[AI404] Graduation Project 1 is a prerequisite for:
- Graduation Project 2 [AI407]
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

### 26. Egyptian Arabic - PASS

**Question:** ايه المتطلبات بتاعت AI406؟

**Expected markers:** AI401, AI304

**Production answer:**

```text
متطلبات [AI406] AI Applications:
- المتطلبات الأساسية Computer Vision [AI304], Intelligent Algorithms [AI401]

- ملاحظة: اسأل عن السلسلة الكاملة لو عايز تشوف كل المتطلبات.
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

### 28. Egyptian Arabic - PASS

**Question:** لازم اكون واخد ايه قبل Machine Learning؟

**Expected markers:** AI201, MTH104

**Production answer:**

```text
متطلبات [AI301] Machine Learning:
- المتطلبات الأساسية Introduction to Artificial Intelligence [AI201], Probability and Statistics 1 [MTH104]

- ملاحظة: اسأل عن السلسلة الكاملة لو عايز تشوف كل المتطلبات.
```

### 29. Egyptian Arabic - PASS

**Question:** CS201 بتفتحلي ايه بعد كده؟

**Expected markers:** CS203, CS204, SW201

**Production answer:**

```text
لو خلصت [CS201] Object Oriented Programming، المواد اللي هتفتحلك هي:
- Data Structures [CS203]
- Operating Systems [CS204]
- Software Engineering [SW201]
- Computer Graphics [CS307]
- Software Development for Mobile Devices [SW305]
- Computer Networks [CB301]
- Software Security [CB306]
```

### 30. Egyptian Arabic - PASS

**Question:** ايه المطلوب قبل Deep Learning؟

**Expected markers:** AI301

**Production answer:**

```text
متطلبات [AI403] Deep Learning:
- المتطلبات الأساسية Machine Learning [AI301]

- ملاحظة: اسأل عن السلسلة الكاملة لو عايز تشوف كل المتطلبات.
```

### 31. Egyptian Arabic - PASS

**Question:** بعد ما اخلص CB304 اقدر اخد ايه؟

**Expected markers:** CB305, CB306, CB307

**Production answer:**

```text
لو خلصت [CB304] Introduction to Cyber-Security، المواد اللي هتفتحلك هي:
- Network Security [CB305]
- Software Security [CB306]
- Introduction to Cyber Attacks [CB307]
- Digital Forensics [CB402]
- Graduation Project 1 [CB406]
- Usable Security [CB310]
- Reverse Engineering & Disassemblers [CB313]
- Information Security [CB414]
```

### 32. Egyptian Arabic - PASS

**Question:** Network Security محتاجه ايه قبلها؟

**Expected markers:** CB301, CB304

**Production answer:**

```text
متطلبات [CB305] Network Security:
- المتطلبات الأساسية Computer Networks [CB301], Introduction to Cyber-Security [CB304]

- ملاحظة: اسأل عن السلسلة الكاملة لو عايز تشوف كل المتطلبات.
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

### 35. Egyptian Arabic - PASS

**Question:** MTH101 بتفتحلي ايه؟

**Expected markers:** MTH103, MTH104

**Production answer:**

```text
لو خلصت [MTH101] Mathematics 1، المواد اللي هتفتحلك هي:
- Mathematics 2 [MTH103]
- Probability and Statistics 1 [MTH104]
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

### 37. Egyptian Arabic - PASS

**Question:** بعد CS102 ايه المواد اللي بتتفتح؟

**Expected markers:** CS201, CS205, IS201

**Production answer:**

```text
لو خلصت [CS102] Structured Programming، المواد اللي هتفتحلك هي:
- Object Oriented Programming [CS201]
- Algorithms [CS205]
- Database Systems [IS201]
```

### 38. Egyptian Arabic - PASS

**Question:** Database Systems لازم قبلها ايه؟

**Expected markers:** IS101, CS102

**Production answer:**

```text
متطلبات [IS201] Database Systems:
- المتطلبات الأساسية Structured Programming [CS102], Fundamentals of Information Systems [IS101]

- ملاحظة: اسأل عن السلسلة الكاملة لو عايز تشوف كل المتطلبات.
```

### 39. Egyptian Arabic - PASS

**Question:** AI302 بتفتح ايه بعد كده؟

**Expected markers:** AI303, AI308, AI411

**Production answer:**

```text
لو خلصت [AI302] Natural Language Processing، المواد اللي هتفتحلك هي:
- Speech Recognition [AI303]
- Language Modeling [AI308]
- Language and Speech Technology [AI411]
- Statistical Language Modeling [AI412]
```

### 40. Egyptian Arabic - PASS

**Question:** Computer Vision متطلباتها ايه؟

**Expected markers:** AI301

**Production answer:**

```text
متطلبات [AI304] Computer Vision:
- المتطلبات الأساسية Machine Learning [AI301]

- ملاحظة: اسأل عن السلسلة الكاملة لو عايز تشوف كل المتطلبات.
```

### 41. Egyptian Arabic - PASS

**Question:** لو خلصت CB305 هيفتحلي ايه؟

**Expected markers:** CB308, CB314, CB408

**Production answer:**

```text
لو خلصت [CB305] Network Security، المواد اللي هتفتحلك هي:
- Real-Time Auditing & Defense [CB308]
- Threat Detection and Mitigation [CB314]
- Firewalls and Web Application Firewall [CB408]
- Computer Networks Defense [CB413]
```

### 42. Egyptian Arabic - PASS

**Question:** Ethical Hacking محتاجه ايه قبلها؟

**Expected markers:** CB308

**Production answer:**

```text
متطلبات [CB404] Ethical Hacking:
- المتطلبات الأساسية Real-Time Auditing & Defense [CB308]

- ملاحظة: اسأل عن السلسلة الكاملة لو عايز تشوف كل المتطلبات.
```

### 43. Egyptian Arabic - PASS

**Question:** ELC201 بتفتح اي مواد؟

**Expected markers:** CB309

**Production answer:**

```text
لو خلصت [ELC201] Logic Design، المواد اللي هتفتحلك هي:
- Hardware Security [CB309]
```

### 44. Egyptian Arabic - PASS

**Question:** Logic Design متطلبها ايه؟

**Expected markers:** ELC101

**Production answer:**

```text
متطلبات [ELC201] Logic Design:
- المتطلبات الأساسية Electronics [ELC101]

- ملاحظة: اسأل عن السلسلة الكاملة لو عايز تشوف كل المتطلبات.
```

### 45. Egyptian Arabic - PASS

**Question:** Software Engineering بتفتح ايه؟

**Expected markers:** SW303, SW401

**Production answer:**

```text
لو خلصت [SW201] Software Engineering، المواد اللي هتفتحلك هي:
- User Interface Design [SW303]
- Software Testing & Quality Assurance [SW401]
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

### 47. Egyptian Arabic - PASS

**Question:** بعد Deep Learning اقدر اخد ايه؟

**Expected markers:** AI410

**Production answer:**

```text
لو خلصت [AI403] Deep Learning، المواد اللي هتفتحلك هي:
- Cognitive Natural Networks [AI410]
```

### 48. Egyptian Arabic - PASS

**Question:** ايه البري ريكويست بتاع AI Applications؟

**Expected markers:** AI401, AI304

**Production answer:**

```text
متطلبات [AI406] AI Applications:
- المتطلبات الأساسية Computer Vision [AI304], Intelligent Algorithms [AI401]

- ملاحظة: اسأل عن السلسلة الكاملة لو عايز تشوف كل المتطلبات.
```

### 49. Egyptian Arabic - PASS

**Question:** Graduation Project 1 في AI بيفتح ايه؟

**Expected markers:** AI407

**Production answer:**

```text
لو خلصت [AI404] Graduation Project 1، المواد اللي هتفتحلك هي:
- Graduation Project 2 [AI407]
```

### 50. Egyptian Arabic - PASS

**Question:** Advanced Cryptography محتاجه ايه؟

**Expected markers:** CB303

**Production answer:**

```text
متطلبات [CB303] Cryptography:
- المتطلبات الأساسية Linear Algebra [MTH102]

- ملاحظة: اسأل عن السلسلة الكاملة لو عايز تشوف كل المتطلبات.
```

# Mixed Live Checklist

Use this checklist against the live Vercel chatbot. Each item includes the expected path and the expected result shape so you can judge whether the answer is correct.

| # | Path | Question | Expected result |
|---|------|----------|-----------------|
| 1 | KG | `Machine Learning لما أخلصها بتفتحلي إيه؟` | Should answer what courses `Machine Learning` opens, not generic course info. |
| 2 | KG | `Software Engineering إيه متطلبات مادة الـ؟` | Should answer the prerequisite(s) for `Software Engineering`, not a course description only. |
| 3 | KG | `What do I need before Deep Learning لو عايز اسجلها؟` | Should answer prerequisite(s) for `Deep Learning`. |
| 4 | KG | `بعد ما أخلص Data Structures هيفتحلي إيه؟` | Should answer what courses `Data Structures` opens. |
| 5 | KG | `AI applications عشان أخدها لازم أكون مخلص إيه؟` | Should answer prerequisite(s) for `AI applications`, not a broad course list. |
| 6 | KG | `لو نجحت في Operating Systems بيتفتحلي ايه بعد كده؟` | Should answer what `Operating Systems` opens. |
| 7 | KG | `Computer Networks إيه المواد اللي لازم أكون مخلصها قبلها؟` | Should answer prerequisite(s) for `Computer Networks`. |
| 8 | KG | `عايز أعرف مواد سنة تالتة AI` | Should answer the level/program study path, not regulation rules. |
| 9 | RAG | `هو الترم الصيفي مدتو قد ايه ؟` | Should answer `8 weeks`, including that it includes the exam period. |
| 10 | RAG | `لو طالب حصلو عذر و معرفش يحضر امتحان الفاينال المفروض بيحصلو ايه بعد كدا ؟` | Should mention `I / غير مكتمل` with the condition about `60%` coursework and the later final exam. |
| 11 | RAG | `لازم نسبة حضوري تكون كام في الميه عشان احضر الامتحان النهائي؟` | Should answer `75%` attendance minimum. |
| 12 | RAG | `لو غيابي زاد عن 25% في المادة ايه اللي يحصل؟` | Should mention possible deprivation from the final exam after warning. |
| 13 | RAG | `لو ال CGPA بتاعي من 2 لاقل من 3 اقدر اسجل كام ساعة؟` | Should answer `18 credit hours`. |
| 14 | RAG | `Withdraw من المادة ينفع لحد امتى؟` | Should answer the withdrawal deadline, expected `end of week 9`. |
| 15 | RAG | `نظام التقديرات في الجامعة عامل إزاي؟` | Should describe grades like `A+ ... F` and/or grade-point mapping, not unrelated regulations. |
| 16 | RAG | `How long is the regular semester بالعربي كده؟` | Should answer `17 weeks`, including exams. |
| 17 | Mental | `أنا متوتر من الامتحانات ومش عارف أبدأ from where` | Should give supportive study guidance, not RAG/KG data. |
| 18 | Mental | `حاسس إني تايه ومش لاحق المواد this term` | Should give supportive, practical academic coping advice. |
| 19 | Mental | `اختار AI ولا Cyber؟` | Should give major comparison guidance, not mental-support comfort only. |
| 20 | Mental | `I am afraid I will fail ومحتاج طريقة أذاكر بيها` | Should give supportive study advice, not course/regulation retrieval. |

## Result Log

Fill this after live testing.

| # | Actual answer summary | Correct? | Notes |
|---|------------------------|----------|-------|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |
| 6 |  |  |  |
| 7 |  |  |  |
| 8 |  |  |  |
| 9 |  |  |  |
| 10 |  |  |  |
| 11 |  |  |  |
| 12 |  |  |  |
| 13 |  |  |  |
| 14 |  |  |  |
| 15 |  |  |  |
| 16 |  |  |  |
| 17 |  |  |  |
| 18 |  |  |  |
| 19 |  |  |  |
| 20 |  |  |  |

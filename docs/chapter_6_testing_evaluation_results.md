# CHAPTER 6: TESTING, EVALUATION, AND RESULTS

## 6.1 Testing Objectives

The Smart Academic Advisor was tested to verify that the final backend prototype works correctly in local and production environments. Testing focused on functional correctness, answer accuracy, multilingual support, integration reliability, robustness, and basic production readiness.

The main testing objectives were:

1. **Functionality**
   - Verify that the main API endpoints work correctly.
   - Confirm that chat messages are routed to the correct service: RAG, KG, mental support, or electives.
   - Verify session creation, history storage, and health-check endpoints.

2. **Accuracy**
   - Check that regulation answers match the official academic regulations.
   - Check that KG prerequisite and unlock answers match the Neo4j course graph.
   - Check that KG registration-order answers correctly identify whether one course must be completed before another.
   - Check that mental-support prompts receive academic support responses rather than out-of-scope replies.

3. **Multilingual Robustness**
   - Test English, Arabic, Egyptian Arabic, and mixed Arabic-English prompts.
   - Verify that semantic routing works beyond exact keyword matching.
   - Confirm support for course codes and mixed-language academic terms such as `CGPA`, `AI301`, and `Machine Learning`.

4. **Integration**
   - Verify integration between FastAPI, LangGraph, OpenAI, Neo4j Aura, Supabase, and Vercel.
   - Confirm that production environment variables and cloud dependencies are configured correctly.

5. **Robustness**
   - Test direct standalone questions in English, Arabic, Egyptian Arabic, and mixed language forms.
   - Test fallback behavior when services return missing information.
   - Verify that low-confidence or malformed routing decisions do not break the chatbot.

6. **Performance and Availability**
   - Confirm that the deployed API responds successfully through Vercel.
   - Confirm that production `/health` reports connected dependencies.

7. **Security and Configuration**
   - Verify that secrets are kept in environment variables.
   - Confirm that production services use Vercel environment configuration instead of committed credentials.

8. **Interpretability**
   - Validate routing decisions through expected routes, sub-intents, and answer markers.
   - Use logs, reports, and test cases to explain why answers were accepted.

## 6.2 Testing Environment

### Local Testing Environment

| Item | Specification |
|---|---|
| Development machine | MacBook Air |
| Architecture | ARM64 |
| Operating system | macOS / Darwin 25.4.0 |
| Local Python version | Python 3.14.3 |
| Virtual environment | `.venv` |
| Test framework | Python `unittest` |
| Version control | Git 2.53.0 |
| Main test command | `.venv/bin/python -m unittest discover -s tests` |
| Compile check | `.venv/bin/python -m compileall advisor_ai scripts tests` |

### Production Testing Environment

| Item | Specification |
|---|---|
| Hosting platform | Vercel |
| Production base URL | `https://smart-academic-advisor-api.vercel.app` |
| Runtime | Vercel Python serverless runtime |
| Vercel Python version | Python 3.12 |
| API framework | FastAPI |
| Deployment command | `npx vercel deploy --prod --yes` |
| Production test endpoint | `POST /chat` |
| Health endpoint | `GET /health` |

### Cloud Services Tested

| Service | Purpose | Production Status |
|---|---|---|
| OpenAI | LLM routing, support prompts, and vector-store RAG | Connected |
| OpenAI Vector Store | Hosted regulation retrieval | Configured and initialized |
| Neo4j Aura | Knowledge graph database | Connected |
| Supabase | Sessions and chat history | Connected |
| Vercel | API hosting | Running |

### Test Data

The system was tested using:

- Official academic regulation content extracted into `important_pdf/RAG/regulations_clean.md`.
- KG course, category, program, and prerequisite data from `advisor_ai/populate_kg.py`.
- RAG question bank in `important_pdf/RAG/question_bank.md`.
- KG validation prompts in `scripts/run_egyptian_kg_checks.py`.
- Broad production-style RAG regression prompts in `scripts/run_production_rag_regression_checks.py`.
- Production multilingual prompts in `docs/production_multilingual_chat_checks_2026_05_12.md`.
- Full live chatbot report in `docs/live_full_chatbot_check_2026_05_12.md`.
- Existing regression tests in `tests/test_advisor_smoke.py`.
- RAG production regression tests in `tests/test_rag_production_regression.py`.

## 6.3 Test Cases

### Functional and Integration Test Cases

| Test ID | Test Scenario | Input/Test Data | Expected Result | Actual Result | Pass/Fail |
|---|---|---|---|---|---|
| TC-01 | Production health check | `GET /health` | API running; KG, RAG, and history connected | API running; KG, RAG, and history connected | Pass |
| TC-02 | RAG English graduation rule | `How many credit hours are required for graduation?` | Answer includes `144` credit hours | `To graduate, a minimum of 144 credit hours is required.` | Pass |
| TC-03 | RAG Arabic graduation rule | `كم ساعة معتمدة لازم الطالب يجتازها عشان يتخرج؟` | Answer includes `144` | `لازم الطالب يجتاز 144 ساعة معتمدة` | Pass |
| TC-04 | RAG Egyptian Arabic graduation rule | `لو انا عايز اتخرج، محتاج اخلص كام ساعة معتمدة؟` | Answer includes `144` | `لازم الطالب يجتاز 144 ساعة معتمدة` | Pass |
| TC-05 | RAG mixed Arabic-English CGPA rule | `لو ال CGPA بتاعي من 2 لاقل من 3 اقدر اسجل كام credit hours؟` | Answer includes `18` credit hours | Answer returned `18 ساعة معتمدة` | Pass |
| TC-06 | KG English unlock query | `what does AI301 unlock?` | Answer includes future courses such as `AI302` and `AI403` | Answer included `AI302`, `AI304`, `AI403`, and others | Pass |
| TC-07 | KG Arabic prerequisite query | `ما متطلبات مادة تعلم الآلة؟` | Answer includes `AI201` and `MTH104` | Answer included `AI201` and `MTH104` | Pass |
| TC-08 | KG Egyptian Arabic study-plan query | `ايه مواد سنة تالته ذكاء اصطناعي؟` | Answer includes level 3 AI courses such as `AI301`, `CS302`, `DS307` | Answer included `AI301`, `CS302`, `DS307` | Pass |
| TC-09 | KG mixed Arabic-English unlock query | `Machine Learning بتفتح ايه؟` | Answer includes `AI302` and `AI403` | Answer included `AI302` and `AI403` | Pass |
| TC-10 | KG Arabic registration-order rejection | `ينفع اسجل math2 قبل math1؟` | Answer says no and explains `Mathematics 1 [MTH101]` must be completed before `Mathematics 2 [MTH103]` | Answer rejected registering `Mathematics 2 [MTH103]` before `Mathematics 1 [MTH101]` | Pass |
| TC-11 | KG English registration-order acceptance | `can I take math 1 before math 2?` | Answer says yes and explains `Mathematics 1 [MTH101]` is required before `Mathematics 2 [MTH103]` | Answer confirmed the prerequisite order | Pass |
| TC-12 | KG Arabic registration-order rejection for non-math courses | `ينفع اسجل software engineering قبل oop؟` | Answer says no and explains `Object Oriented Programming [CS201]` must be completed first | Answer rejected registering `Software Engineering [SW201]` before `Object Oriented Programming [CS201]` | Pass |
| TC-13 | Mental English support | `I am stressed and need study tips` | Academic support response | Returned academic support and study tips | Pass |
| TC-14 | Mental Arabic support | `أنا قلقان من الامتحانات ومحتاج نصائح للمذاكرة` | Arabic academic support response | Returned Arabic academic support response | Pass |
| TC-15 | Mental Egyptian Arabic support | `انا خايف اسقط الترم ده ومش عارف اذاكر` | Egyptian Arabic academic support response | Returned Arabic academic support response | Pass |
| TC-16 | Mental mixed Arabic-English support | `انا stressed من exams ومحتاج study plan` | Arabic support response preserving mixed context | Returned Arabic academic support response | Pass |
| TC-17 | Local unit regression suite | `.venv/bin/python -m unittest discover -s tests` | All tests pass | `123 tests OK` | Pass |
| TC-18 | Local compile validation | `.venv/bin/python -m compileall advisor_ai scripts tests` | No syntax errors | Compile check passed | Pass |
| TC-19 | Focused local Egyptian RAG script | `.venv/bin/python -m scripts.run_egyptian_rag_checks` | All 20 checks pass | `20/20 passed` | Pass |
| TC-20 | Focused local Egyptian KG script | `.venv/bin/python -m scripts.run_egyptian_kg_checks` | All 20 checks pass | `20/20 passed` | Pass |
| TC-21 | Production KG prerequisite bank | 50 production KG prerequisite/unlock prompts | All expected markers found | `50/50 passed` | Pass |
| TC-22 | PDF-grounded chatbot report | 90 production prompts across RAG, KG, general | Expected markers found | `RAG 30/30`, `KG 30/30`, `GENERAL 30/30` | Pass |
| TC-23 | Local production-style RAG regression bank | 98 regulation prompts across 44 regulation topics | Expected markers found and forbidden wrong-topic markers absent | `98/98 passed` | Pass |
| TC-24 | Live full chatbot production check | 150 production prompts across KG, RAG, follow-up, and fallback groups | Strong majority should fully match; failures should identify remaining limitations | `126 FULL`, `3 PARTIAL`, `21 NO_MATCH`, `0 ERROR` | Partial |

### Representative Production Answers

| Area | Language | Prompt | Expected Marker | Actual Marker Found | Result |
|---|---|---|---|---|---|
| RAG | English | `How many credit hours are required for graduation?` | `144` | `144` | Pass |
| RAG | Arabic | `كم ساعة معتمدة لازم الطالب يجتازها عشان يتخرج؟` | `144` | `144` | Pass |
| RAG | Egyptian Arabic | `لو انا عايز اتخرج، محتاج اخلص كام ساعة معتمدة؟` | `144` | `144` | Pass |
| RAG | Mixed Arabic-English | `لو ال CGPA بتاعي من 2 لاقل من 3 اقدر اسجل كام credit hours؟` | `18` | `18` | Pass |
| KG | English | `what does AI301 unlock?` | `AI302`, `AI403` | `AI302`, `AI403` | Pass |
| KG | Arabic | `ما متطلبات مادة تعلم الآلة؟` | `AI201`, `MTH104` | `AI201`, `MTH104` | Pass |
| KG | Egyptian Arabic | `ايه مواد سنة تالته ذكاء اصطناعي؟` | `AI301`, `CS302`, `DS307` | `AI301`, `CS302`, `DS307` | Pass |
| KG | Mixed Arabic-English | `Machine Learning بتفتح ايه؟` | `AI302`, `AI403` | `AI302`, `AI403` | Pass |
| KG | Arabic | `ينفع اسجل math2 قبل math1؟` | No; `MTH101` before `MTH103` | No; `MTH101` before `MTH103` | Pass |
| Mental | English | `I am stressed and need study tips` | Academic support | Academic support returned | Pass |
| Mental | Arabic | `أنا قلقان من الامتحانات ومحتاج نصائح للمذاكرة` | Arabic study support | Arabic support returned | Pass |
| Mental | Egyptian Arabic | `انا خايف اسقط الترم ده ومش عارف اذاكر` | Arabic/Egyptian support | Arabic support returned | Pass |
| Mental | Mixed Arabic-English | `انا stressed من exams ومحتاج study plan` | Arabic support | Arabic support returned | Pass |

## 6.4 Evaluation Metrics

### Metrics Used in This Project

| Metric | Definition | Why It Is Appropriate |
|---|---|---|
| Pass rate | Number of passed tests divided by total tests | Measures functional correctness across test cases. |
| Expected-marker match | Checks whether key expected facts appear in the answer | Suitable for RAG/KG answers where exact wording may vary but facts must be present. |
| Routing accuracy | Percentage of prompts routed to the correct service | Validates semantic intent classification on the current standalone question. |
| Dependency health | Connected/not connected state for KG, RAG, and history | Confirms production readiness and integration availability. |
| Multilingual coverage | Number of language styles successfully handled | Evaluates Arabic, English, Egyptian Arabic, and mixed-language support. |
| Regression pass rate | Unit test pass percentage | Ensures new changes do not break previous behavior. |
| Compile success | Whether all Python modules compile | Detects syntax/import errors before deployment. |
| Response correctness | Manual/marker-based review of returned answers | Ensures the output is academically meaningful. |

### Specialization Recommended Metrics

Although this project is an academic-advising chatbot rather than a single traditional prediction model, metrics from related specializations can still guide evaluation.

| Specialization | Recommended Metrics | Application to This Project |
|---|---|---|
| Artificial Intelligence | Accuracy, precision, recall, F1-score, AUC, confusion matrix, loss curves, inference time, explainability outputs | Useful for evaluating semantic routing as a classification problem: correct route vs predicted route. In this project, route pass rate and expected-marker checks were used instead of a full confusion matrix. |
| Data Science | Data quality indicators, descriptive statistics, RMSE/MAE/R², classification metrics, dashboard usability, insight validation | Useful for checking regulation data quality, KG completeness, test coverage, and correctness of extracted facts. |
| Cybersecurity | Detection rate, false positive rate, vulnerability severity, CVSS score, response time, exploit success/failure, log coverage, compliance with secure practices | Useful for future security evaluation of API authentication, secret handling, dependency vulnerability scanning, logging, and abuse resistance. |

### Applied Metric Results

| Evaluation Area | Metric | Result |
|---|---|---:|
| Local unit tests | Regression pass rate | 123/123 passed |
| Local RAG focused checks | Expected-marker pass rate | 20/20 passed |
| Local KG focused checks | Expected-marker pass rate | 20/20 passed |
| Local production-style RAG regression checks | Expected-marker pass rate | 98/98 passed |
| Production multilingual `/chat` checks | Expected-marker pass rate | 12/12 passed |
| Production KG prerequisite checks | Expected-marker pass rate | 50/50 passed |
| PDF-grounded chatbot report | RAG pass rate | 30/30 passed |
| PDF-grounded chatbot report | KG pass rate | 30/30 passed |
| PDF-grounded chatbot report | General prompt pass rate | 30/30 passed |
| Live full chatbot production check | Full marker match | 126/150 full |
| Live full chatbot production check | Partial marker match | 3/150 partial |
| Live full chatbot production check | No-match marker result | 21/150 no match |
| Live full chatbot production check | Runtime errors | 0/150 errors |
| Production health | Dependency availability | 3/3 connected |

## 6.5 Results Presentation

### Summary of Main Results

| Test Group | Total Tests | Passed | Failed | Pass Rate |
|---|---:|---:|---:|---:|
| Local unit tests | 123 | 123 | 0 | 100% |
| Local Egyptian RAG checks | 20 | 20 | 0 | 100% |
| Local Egyptian KG checks | 20 | 20 | 0 | 100% |
| Local production-style RAG regression checks | 98 | 98 | 0 | 100% |
| Production multilingual chat checks | 12 | 12 | 0 | 100% |
| Production KG prerequisite checks | 50 | 50 | 0 | 100% |
| PDF-grounded chatbot report - RAG | 30 | 30 | 0 | 100% |
| PDF-grounded chatbot report - KG | 30 | 30 | 0 | 100% |
| PDF-grounded chatbot report - General | 30 | 30 | 0 | 100% |
| Live full chatbot production check - full matches | 150 | 126 full, 3 partial | 21 no match | 84.0% full / 86.0% full-or-partial |

### Production Health Result

| Dependency | Expected Result | Actual Result | Status |
|---|---|---|---|
| FastAPI service | Running | Running | Pass |
| KG / Neo4j Aura | Connected | Connected | Pass |
| RAG / OpenAI vector store | Initialized and configured | Initialized and configured | Pass |
| Supabase history | Connected | Connected | Pass |

### Routing Result by Service

| Service | Tested Prompt Types | Result |
|---|---|---|
| RAG | Graduation hours, CGPA credit load, Arabic/Egyptian Arabic regulation wording | Passed |
| KG | Prerequisites, unlocks, registration-order checks, level study plan, Arabic-English course names | Passed |
| Mental | Stress, exam anxiety, study tips, Arabic and mixed-language support | Passed |

### Multilingual Result

| Language Style | RAG | KG | Mental | Overall |
|---|---|---|---|---|
| English | Pass | Pass | Pass | Pass |
| Arabic | Pass | Pass | Pass | Pass |
| Egyptian Arabic | Pass | Pass | Pass | Pass |
| Mixed Arabic-English | Pass | Pass | Pass | Pass |

### Evidence Files

| Report/File | Purpose |
|---|---|
| `docs/production_multilingual_chat_checks_2026_05_12.md` | Full production prompts and answers for RAG, KG, and mental multilingual tests. |
| `docs/production_kg_prereq_checks_2026_05_11.md` | 50 production KG prerequisite/unlock checks. |
| `docs/pdf_grounded_chatbot_report.md` | PDF-grounded production report for RAG, KG, and general prompts. |
| `docs/live_full_chatbot_check_2026_05_12.md` | 150-prompt live production report showing full, partial, and no-match results. |
| `tests/test_advisor_smoke.py` | Local regression and smoke test suite. |
| `tests/test_rag_production_regression.py` | Automated unittest wrapper for the 98-case RAG regression bank. |
| `scripts/run_egyptian_rag_checks.py` | Focused Egyptian Arabic RAG validation script. |
| `scripts/run_egyptian_kg_checks.py` | Focused Egyptian Arabic KG validation script. |
| `scripts/run_production_rag_regression_checks.py` | Broad local regulation regression script covering 44 regulation topics. |

## 6.6 Discussion of Results

The test results show that the Smart Academic Advisor backend satisfies the main functional requirements of the prototype. The system successfully answers academic regulation questions, course prerequisite questions, course unlock questions, registration-order questions, study-plan questions, and mental-support prompts. The production system also passed multilingual tests in English, Arabic, Egyptian Arabic, and mixed Arabic-English.

The semantic-first routing refactor improved the chatbot's ability to understand user intent without relying only on strict word matching. Before the refactor, routing mixed LLM classification, deterministic parsing, and fuzzy matching in a way that could misclassify study-plan questions as category queries. After the refactor, the LLM acts as the main semantic extractor, while deterministic rules validate clear entities such as course codes, levels, programs, prerequisite wording, and compulsory/elective requirement type. Runtime follow-up rewriting was later removed from the main route decision because production checks showed that it could add latency and sometimes reuse the previous intent incorrectly. The current behavior routes from the current message first, while keeping compact history available for limited KG relationship follow-ups.

The RAG results show strong grounding for regulation questions. The system correctly answered graduation-hour and CGPA credit-load questions in production. A previous weakness was Arabic graduation phrasing such as "كم ساعة معتمدة لازم الطالب يجتازها عشان يتخرج؟". This was solved by adding deterministic RAG handling for Arabic graduation-hour variants. Later RAG changes expanded coverage for transfer, admission, graduate affairs, grade symbols, dismissal, appeals, final chance, withdrawal, and grievance topics through normalization, formal query rewriting, local clean-text fallback, and a 98-case production-style regression suite. After these fixes, the focused RAG scripts, broad local RAG regression suite, and PDF-grounded production report passed.

The KG results show that the Neo4j course graph is reliable for prerequisites, unlock relationships, and registration-order checks. Production KG checks passed for English and Egyptian Arabic prerequisite/unlock prompts. Local KG regression tests also confirmed that yes/no registration-order prompts are answered from prerequisite paths, such as rejecting `Mathematics 2 [MTH103]` before `Mathematics 1 [MTH101]`. The system correctly identified course dependencies such as `AI301 -> AI302/AI403` and prerequisites such as `Machine Learning -> AI201/MTH104`.

The mental-support results show that the system can identify academic stress and study-support requests across multiple language styles. A previous Arabic wording gap involving `قلقان` and `نصائح للمذاكرة` was fixed. Production tests now show correct mental-support routing for Arabic, Egyptian Arabic, and mixed Arabic-English prompts.

The 150-prompt live full chatbot check is useful because it shows both readiness and remaining gaps. It completed with no runtime errors and 126 full marker matches, but it also recorded 3 partial matches and 21 no-match cases. The no-match cases were concentrated around some Arabic formal KG phrasing, broad Cybersecurity level-plan wording, university compulsory wording, several contextual follow-up examples, and a few edge-case fallback expectations. These are treated as known limitations rather than hidden failures.

### Comparison with Expectations

| Expected Capability | Observed Result | Interpretation |
|---|---|---|
| Answer regulation questions from official data | Passed | RAG and deterministic regulation rules provide grounded answers. |
| Answer course prerequisite/unlock questions | Passed | Neo4j KG relationships return expected course codes. |
| Answer course registration-order questions | Passed | KG prerequisite paths support direct yes/no answers such as `Math 2` before `Math 1`. |
| Understand Arabic and Egyptian Arabic | Passed | Routing and answer generation handle Arabic variants. |
| Understand mixed Arabic-English academic questions | Passed | Course names, `CGPA`, and course codes are preserved correctly. |
| Maintain production dependency health | Passed | KG, RAG, and Supabase are connected in production. |
| Avoid regressions after routing refactor | Passed | Full local unit suite passed. |
| Broad live chatbot behavior | Partially passed | 126/150 prompts fully matched, 3 partially matched, and 0 runtime errors; 21 prompts identified follow-up/KG wording gaps. |

### Limitations

1. **Test coverage is representative, not exhaustive**
   - The production tests cover important examples, but they do not prove correctness for every possible student wording.

2. **Expected-marker evaluation is limited**
   - Marker checks confirm key facts are present, but they do not fully measure response clarity, completeness, or tone.

3. **Mental-support evaluation is qualitative**
   - Mental responses are checked for correct routing and safe academic support, but they are not evaluated by clinical or counseling experts.

4. **Performance was not benchmarked deeply**
   - The system was tested for availability and successful responses, but detailed latency, throughput, and load testing were not performed.

5. **Security testing was basic**
   - Secret handling and production health were verified, but formal penetration testing, CVSS scoring, and dependency vulnerability scanning were not included in this phase.

6. **Student-record KG is not part of the current production KG scope**
   - The KG currently focuses on courses, categories, programs, and prerequisites, not personal transcript/CGPA records.

7. **Some live KG and follow-up wording still needs improvement**
   - The 150-prompt live report found no runtime errors, but it did identify remaining no-match cases for some Arabic KG phrasings, contextual follow-ups, and category wording.

### Future Evaluation Work

Future testing can improve the evaluation by adding:

- A larger multilingual benchmark dataset.
- A route-level confusion matrix.
- Latency and throughput tests under concurrent users.
- User satisfaction/usability testing with students.
- Security testing including dependency scanning, API abuse checks, and rate-limit validation.
- Human evaluation of answer helpfulness, tone, and academic correctness.
- More detailed RAG retrieval evaluation using citation or source-page checks.

## Final Testing Conclusion

The implemented system passed the current local automated validation commands: `123/123` unit tests, compile validation, and `98/98` production-style RAG regression checks. Production evidence also shows connected dependencies, successful focused multilingual checks, successful KG prerequisite checks, and a successful PDF-grounded report. The broader 150-prompt live report shows the backend is operational and demo-ready, while also documenting remaining KG/follow-up wording gaps for future improvement.

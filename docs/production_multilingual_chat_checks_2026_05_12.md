# Production Multilingual Chat Checks

Date: May 12, 2026

Target production API: `https://smart-academic-advisor-api.vercel.app/chat`

Scope:
- RAG, KG, and mental-support routing.
- English, Arabic, Egyptian Arabic, and mixed Arabic-English prompts.
- Each prompt was sent in a fresh production chat session to avoid history bias.

## 1. RAG - English

**Question:**  
`How many credit hours are required for graduation?`

**Production answer:**  
To graduate, a minimum of 144 credit hours is required.

## 2. RAG - Arabic

**Question:**  
`كم ساعة معتمدة لازم الطالب يجتازها عشان يتخرج؟`

**Production answer:**  
- لازم الطالب يجتاز 144 ساعة معتمدة عشان يتخرج.

## 3. RAG - Egyptian Arabic

**Question:**  
`لو انا عايز اتخرج، محتاج اخلص كام ساعة معتمدة؟`

**Production answer:**  
- لازم الطالب يجتاز 144 ساعة معتمدة عشان يتخرج.

## 4. RAG - Mixed Arabic-English

**Question:**  
`لو ال CGPA بتاعي من 2 لاقل من 3 اقدر اسجل كام credit hours؟`

**Production answer:**  
- الطالب صاحب CGPA من 2 إلى أقل من 3 يقدر يسجل 18 ساعة معتمدة.

## 5. KG - English

**Question:**  
`what does AI301 unlock?`

**Production answer:**  
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

## 6. KG - Arabic

**Question:**  
`ما متطلبات مادة تعلم الآلة؟`

**Production answer:**  
علشان تفتح مادة Machine Learning [AI301]، لازم تكون مخلص:
- Introduction to Artificial Intelligence [AI201]
- Probability and Statistics 1 [MTH104]

## 7. KG - Egyptian Arabic

**Question:**  
`ايه مواد سنة تالته ذكاء اصطناعي؟`

**Production answer:**  
Recommended courses for Artificial Intelligence - Level 3:

- Architecture of Intelligence [AI312] - 3 credits
- Artificial Intelligence in Games [AI314] - 3 credits
- Cloud Computing [DS307] - 3 credits
- Computational Learning Theory [AI307] - 3 credits (Prerequisites: Machine Learning)
- Computational Perception [AI306] - 3 credits (Prerequisites: Computer Vision)
- Computer Architecture and Organization [CS302] - 3 credits (Prerequisites: Operating Systems)
- Computer Graphics [CS307] - 3 credits (Prerequisites: Object Oriented Programming)
- Computer Vision [AI304] - 3 credits (Prerequisites: Machine Learning)
- Embedded Systems [CS309] - 3 credits
- Expert Systems [AI311] - 3 credits (Prerequisites: Introduction to Artificial Intelligence)
- Fundamental of Cognitive Interaction with Robots [ROB302] - 3 credits
- Handwriting Recognition [AI310] - 3 credits (Prerequisites: Computer Vision)
- Image Processing [CS303] - 3 credits (Prerequisites: Signal and System)
- Language Modeling [AI308] - 3 credits (Prerequisites: Natural Language Processing)
- Machine Learning [AI301] - 3 credits (Prerequisites: Introduction to Artificial Intelligence, Probability and Statistics 1)
- Natural Language Processing [AI302] - 3 credits (Prerequisites: Machine Learning)
- Operations Research [CS301] - 3 credits
- Pattern Recognition [AI305] - 3 credits (Prerequisites: Machine Learning)
- Russian Language 3 [HM010] - 2 credits (Prerequisites: Russian Language 2)
- Scientific Research Methodology [HM008] - 2 credits
- Scientific Research Methodology 2 [HM009] - 2 credits
- Scientific Thinking [HM006] - 2 credits
- Software Development for Mobile Devices [SW305] - 3 credits (Prerequisites: Object Oriented Programming)
- Speech Recognition [AI303] - 3 credits (Prerequisites: Natural Language Processing)
- Technical Writing [HM007] - 1 credits
- User Interface Design [SW303] - 3 credits (Prerequisites: Software Engineering)
- User Models [AI309] - 3 credits

## 8. KG - Mixed Arabic-English

**Question:**  
`Machine Learning بتفتح ايه؟`

**Production answer:**  
لو خلصت Machine Learning [AI301]، المواد اللي هتتفتحلك هي:
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

## 9. Mental - English

**Question:**  
`I am stressed and need study tips`

**Production answer:**  
Academic support

I understand you're going through a tough time, and that's completely normal.

- Organize your time and prioritize your tasks.
- Take breaks so your mind has time to reset.
- Talk to your professor or TA, they are there to help.
- Break your study into small chunks, step by step.

If you're experiencing severe distress, please reach out to university counseling services.

## 10. Mental - Arabic

**Question:**  
`أنا قلقان من الامتحانات ومحتاج نصائح للمذاكرة`

**Production answer:**  
دعم أكاديمي

أنا فاهم إنك بتمر بوقت صعب، وده طبيعي جداً.

- حاول تنظم وقتك وترتب أولوياتك.
- خد بريك كل شوية، العقل المرتاح بيذاكر أحسن.
- اتكلم مع الدكتور أو المعيد، ده دورهم يساعدوك.
- قسّم المذاكرة لأجزاء صغيرة، خطوة خطوة.

لو حاسس إن الموضوع أكبر من كده، كلّم خدمات الإرشاد في الجامعة.

## 11. Mental - Egyptian Arabic

**Question:**  
`انا خايف اسقط الترم ده ومش عارف اذاكر`

**Production answer:**  
دعم أكاديمي

أنا فاهم إنك بتمر بوقت صعب، وده طبيعي جداً.

- حاول تنظم وقتك وترتب أولوياتك.
- خد بريك كل شوية، العقل المرتاح بيذاكر أحسن.
- اتكلم مع الدكتور أو المعيد، ده دورهم يساعدوك.
- قسّم المذاكرة لأجزاء صغيرة، خطوة خطوة.

لو حاسس إن الموضوع أكبر من كده، كلّم خدمات الإرشاد في الجامعة.

## 12. Mental - Mixed Arabic-English

**Question:**  
`انا stressed من exams ومحتاج study plan`

**Production answer:**  
دعم أكاديمي

أنا فاهم إنك بتمر بوقت صعب، وده طبيعي جداً.

- حاول تنظم وقتك وترتب أولوياتك.
- خد بريك كل شوية، العقل المرتاح بيذاكر أحسن.
- اتكلم مع الدكتور أو المعيد، ده دورهم يساعدوك.
- قسّم المذاكرة لأجزاء صغيرة، خطوة خطوة.

لو حاسس إن الموضوع أكبر من كده، كلّم خدمات الإرشاد في الجامعة.


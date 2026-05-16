# CHAPTER 5: IMPLEMENTATION

## 5.1 Implementation Overview

The Smart Academic Advisor was implemented as a cloud-ready AI backend that serves a mobile or web frontend through a FastAPI REST API. The final deliverable is a deployed academic-advising API that can answer student questions about academic regulations, course prerequisites, study plans, electives, and academic support in English, Arabic, Egyptian Arabic, and mixed Arabic-English.

The implementation was completed in phases:

1. **Requirements and data preparation**
   - Academic regulation content was extracted from official PDF sources and converted into cleaned Markdown files.
   - Course, category, program, and prerequisite information was structured for a Neo4j knowledge graph.
   - Sample question banks were prepared for RAG, KG, and multilingual chatbot validation.

2. **Backend API development**
   - A FastAPI backend was created with endpoints for chat, sessions, history, health checks, and admin controls.
   - The backend was organized into service modules for RAG, KG, mental support, electives, routing, and session management.

3. **AI routing and orchestration**
   - LangGraph was used to route each user question to the correct service node.
   - The routing system was refactored to use semantic LLM intent extraction as the main decision layer.
   - Deterministic rules were kept only for high-confidence validation, such as course codes, year/level words, program words, prerequisite/unlock wording, and compulsory/elective requirement type.

4. **Knowledge Graph implementation**
   - Neo4j Aura was used to store programs, categories, courses, and prerequisite relationships.
   - KG queries support course prerequisites, reverse prerequisites, registration-order checks between two courses, course information, category requirements, and level-based study paths.

5. **Regulation RAG implementation**
   - OpenAI vector stores and file search were used for semantic retrieval over academic regulation documents.
   - Deterministic known-answer rules were added for high-confidence regulation facts such as graduation credit hours, semester duration, attendance rules, and CGPA-based credit load.

6. **Session and history implementation**
   - Supabase was integrated to persist sessions and message history.
   - The backend stores previous messages for session history, recents, and UI retrieval.
   - The semantic router classifies the current user message without older history so that context switches are not misrouted. Previous history is still available to downstream services for carefully scoped cases, such as short course relationship follow-ups.

7. **Deployment and validation**
   - The API was deployed to Vercel as a Python serverless application.
   - Production was validated through `/health` and `/chat` checks for RAG, KG, and mental support across English, Arabic, Egyptian Arabic, and mixed Arabic-English.

The final deliverable is available as a production API:

```text
https://smart-academic-advisor-api.vercel.app
```

## 5.2 Tools, Technologies, and Frameworks

### Main Technology Stack

| Tool/Library | Version | Purpose | Justification |
|---|---:|---|---|
| Python | 3.14.3 local, 3.12 on Vercel | Backend implementation and service logic | Widely supported language for AI, APIs, and data processing. |
| FastAPI | 0.135.3 | REST API framework | High performance, automatic validation, OpenAPI support, and clean endpoint structure. |
| Uvicorn | 0.44.0 | Local ASGI server | Standard FastAPI development server. |
| Pydantic | 2.13.0 | Request/response validation and structured models | Ensures strict schemas for API requests and LLM router outputs. |
| LangGraph | 1.1.6 | Chatbot workflow orchestration | Provides graph-based routing between RAG, KG, mental, and elective nodes. |
| LangChain | 1.2.15 | LLM integration utilities | Used with OpenAI chat models and prompt pipelines. |
| LangChain OpenAI | 1.1.12 | OpenAI model integration | Connects semantic routing and support prompts to OpenAI models. |
| OpenAI SDK | 2.31.0 | LLM and vector-store file search | Supports hosted file-search RAG and chat completions. |
| Tiktoken | 0.12.0 | Tokenization utilities | Useful for OpenAI text/token handling. |
| Neo4j Python Driver | 6.1.0 | Knowledge graph database access | Connects backend services to Neo4j Aura. |
| Supabase Python SDK | 2.28.3 | Session and history storage | Provides cloud Postgres-backed message/session persistence. |
| python-dotenv | 1.2.2 | Environment variable loading | Keeps secrets outside source code during local development. |
| PyYAML | 6.0.3 | YAML configuration support | Supports structured local context/config files. |
| Requests | 2.33.1 | HTTP calls and validation scripts | Used for operational and validation requests. |
| Git | 2.53.0 | Version control | Tracks source changes and supports deployment workflows. |
| Vercel CLI | 53.x | Cloud deployment | Deploys the FastAPI serverless backend to Vercel production. |

### Programming Languages

| Language | Purpose |
|---|---|
| Python | Main backend implementation, AI services, scripts, and tests. |
| Cypher | Neo4j graph queries for courses, categories, programs, and prerequisites. |
| SQL | Supabase table setup for sessions and messages. |
| JSON | API request/response format and structured LLM router output. |
| Markdown | Documentation, question banks, extracted regulation text, and reports. |

### Cloud Services and Databases

| Service | Purpose | Integration |
|---|---|---|
| Vercel | Production hosting for the FastAPI API | `api/index.py` imports `advisor_ai.main:app`; `vercel.json` rewrites all paths to the API entrypoint. |
| OpenAI | LLM routing, response generation, and vector-store RAG | `OPENAI_API_KEY`, `OPENAI_VECTOR_STORE_ID`, and `OPENAI_LLM_MODEL`. |
| OpenAI Vector Store | Hosted document retrieval for academic regulations | Populated using `scripts/setup_openai_vector_store.py`. |
| Neo4j Aura | Knowledge graph database | Stores Program, Category, Course nodes and `REQUIRES` relationships. |
| Supabase | Chat session and history database | Stores `sessions` and `messages` tables for persistent conversation history. |
| LangSmith | Optional tracing/observability | Used through `@traceable` decorators where configured. |

### Security and Configuration Tools

| Tool/Technique | Purpose |
|---|---|
| Environment variables | Keeps OpenAI, Neo4j, Supabase, and LangSmith credentials out of code. |
| `.env` file | Local-only secret storage for development. |
| Vercel environment variables | Production secret storage. |
| `.vercelignore` | Prevents local-only files such as `.env`, `.venv`, PDFs, and test assets from being uploaded. |
| CORS middleware | Allows frontend clients, including Flutter/mobile clients, to call the backend. |
| FastAPI/Pydantic validation | Rejects malformed API requests with structured validation errors. |

### Development Tools

| Tool | Purpose |
|---|---|
| VS Code / IDE | Source editing, debugging, and project navigation. |
| Terminal / shell | Running tests, scripts, local server, and deployments. |
| Git | Version control and change tracking. |
| Vercel CLI / npx Vercel | Production deployment. |
| Python virtual environment `.venv` | Isolated dependency management. |
| unittest | Automated backend tests. |

## 5.3 Development Environment

### Hardware and Operating System

| Item | Specification |
|---|---|
| Development machine | MacBook Air |
| Architecture | ARM64 |
| Operating system | macOS / Darwin 25.4.0 |
| Kernel | Darwin Kernel Version 25.4.0 |

### Local Software Environment

| Item | Version / Configuration |
|---|---|
| Python local interpreter | Python 3.14.3 |
| Vercel Python runtime | Python 3.12 |
| Git | 2.53.0 |
| Virtual environment | `.venv` |
| Test framework | Python `unittest` |
| Package manager | `pip` |
| Deployment CLI | `npx vercel deploy --prod --yes` |

### Required Configuration

The backend requires these environment variables locally and in Vercel production:

| Environment Variable | Required | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | Yes | OpenAI model calls and vector-store RAG. |
| `OPENAI_VECTOR_STORE_ID` | Yes for RAG | ID of the hosted OpenAI vector store. |
| `OPENAI_LLM_MODEL` | Optional | Model name used by routing and support services. Defaults in code if omitted. |
| `NEO4J_URI` | Yes | Neo4j Aura connection URI. |
| `NEO4J_USER` or `NEO4J_USERNAME` | Yes | Neo4j username. |
| `NEO4J_PASSWORD` | Yes | Neo4j password. |
| `NEO4J_DATABASE` | Optional | Neo4j target database. |
| `SUPABASE_URL` | Yes for history | Supabase project URL. |
| `SUPABASE_KEY` | Yes for history | Supabase service/API key. |
| `LANGCHAIN_TRACING_V2` | Optional | Enables LangSmith tracing. |
| `LANGCHAIN_API_KEY` | Optional | LangSmith API key. |
| `LANGCHAIN_PROJECT` | Optional | LangSmith project name. |

### Local Setup Commands

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the local API:

```bash
uvicorn advisor_ai.main:app --reload
```

Populate Neo4j Aura:

```bash
python -m advisor_ai.populate_kg --reset
```

Create or refresh the OpenAI vector store:

```bash
python scripts/setup_openai_vector_store.py
```

Run validation:

```bash
python -m unittest discover -s tests
python -m compileall advisor_ai scripts tests
```

## 5.4 Module Implementation

### Component Summary

| Component/Module | Purpose | Technology Used | Inputs | Outputs | Status |
|---|---|---|---|---|---|
| `advisor_ai.main` | Exposes FastAPI endpoints and lazy-loads services | FastAPI, Pydantic | HTTP requests | JSON API responses | Implemented and deployed |
| `api/index.py` | Vercel serverless entrypoint | FastAPI on Vercel | Vercel HTTP events | FastAPI app execution | Implemented and deployed |
| `advisor_ai.graph` | Main chatbot workflow and semantic routing | LangGraph, OpenAI, Python | Current user question, student level/major | Routed answer from RAG/KG/mental/elective nodes | Implemented and validated |
| `advisor_ai.router_service` | LLM semantic intent extraction | LangChain, OpenAI, Pydantic | Current question | Strict structured routing decision | Implemented and refactored |
| `advisor_ai.followup_resolver` | Optional semantic follow-up classifier/rewriter retained for controlled follow-up experiments | LangChain, OpenAI, Pydantic | Current question and compact history | Follow-up decision or standalone rewrite | Implemented but not used for main runtime routing |
| `advisor_ai.rag_service` | Academic regulation RAG | OpenAI vector store, file search, local fallback | Regulation/policy question | Grounded regulation answer | Implemented and validated |
| `advisor_ai.kg_service` | Course and prerequisite knowledge graph queries | Neo4j Aura, Cypher, LangChain | Course/category/study-plan/registration-order question | Course info, prerequisites, unlocks, registration eligibility, study path | Implemented and validated |
| `advisor_ai.populate_kg` | Loads graph data into Neo4j | Neo4j driver, Cypher | Course/category/prerequisite constants | Neo4j graph database | Implemented |
| `advisor_ai.chat_controller` | Session and history management | Supabase, LangChain messages | Student ID, session ID, message | Persisted history and final chatbot response | Implemented |
| `advisor_ai.supabase_client` | Supabase connection wrapper | Supabase SDK | Supabase env vars | Supabase client/status | Implemented |
| `advisor_ai.mental_service` | Academic support and major guidance | OpenAI, LangChain prompts | Stress/support/major-selection question | Supportive academic response | Implemented |
| `advisor_ai.elective_service` | Elective query handling | Python, OpenAI fallback, admin state | Elective question or uploaded elective list | Active-term elective response | Implemented |
| `advisor_ai.language_utils` | Language detection and response-language rules | Python regex utilities | User question | Arabic/English response instruction | Implemented |
| `admin_upload.py` | Admin CLI helper | Python CLI | Term/elective inputs | Updated elective service state | Implemented |
| `scripts/setup_openai_vector_store.py` | Uploads regulation text to OpenAI vector store | OpenAI SDK | Cleaned regulation Markdown | Vector store ID | Implemented |
| `tests/test_advisor_smoke.py` | Regression and smoke tests | unittest | Simulated service calls and prompts | Pass/fail validation | Implemented |
| `tests/test_rag_production_regression.py` | Broad regulation regression suite | unittest, local RAG fallback helpers | 98 production-style regulation prompts | Marker-based pass/fail validation | Implemented |

### FastAPI API Layer

The API layer is implemented in `advisor_ai/main.py`. It defines the main endpoints used by the mobile or web frontend:

- `POST /sessions`: creates a new chat session.
- `GET /sessions`: lists recent sessions.
- `POST /chat`: sends a student message to the advisor.
- `GET /history`: retrieves previous messages.
- `POST /admin/upload-electives`: uploads active electives.
- `GET /admin/kg/status`: checks Neo4j KG status.
- `GET /admin/rag/status`: checks RAG/vector-store status.
- `GET /admin/history/status`: checks Supabase status.
- `GET /health`: combined system health endpoint.

The API uses Pydantic models for strict request and response validation. Services are lazy-loaded so that startup remains fast in serverless deployment.

### Chat Controller

`advisor_ai/chat_controller.py` is responsible for conversation management. It creates and updates sessions, saves user and assistant messages, retrieves previous messages, and supports chat history endpoints for the frontend.

The controller keeps session history in Supabase and builds a compact memory summary for the graph. Main semantic routing no longer depends on previous turns. This was changed after production testing showed that broad context-dependent follow-up rewriting could slow responses and could incorrectly reuse the previous question's intent.

The controller sends each message to `AdvisorGraph.run()`, along with:

- `question`
- compact `history`
- `student_level`
- `student_major`

This keeps the chatbot stable and predictable: route selection is controlled by the current message and explicit entities, while history is used only where a service can handle it safely, such as short KG follow-ups like "what does it open?" after a known course.

### Semantic Routing and Graph Workflow

`advisor_ai/graph.py` implements the main LangGraph workflow:

```text
router -> rag_node / kg_node / mental_node / elective_node -> hybrid_node -> final answer
```

The routing layer uses a semantic-first design:

1. Normalize the user question.
2. Extract high-confidence deterministic signals:
   - course code
   - course name alias
   - academic level/year
   - program
   - prerequisite/unlock wording
   - compulsory/elective wording
3. Use the LLM router as the main semantic intent extractor.
4. Validate and correct the LLM decision using deterministic signals.
5. Use fallback heuristics only when the LLM has low confidence or lacks required entities.
6. Return clear unsupported messages for student-record questions, instructor/room/timetable questions, and other data that is not present in the current backend.

Supported semantic intents include:

- `course_prerequisite_query`
- `course_unlock_query`
- `study_plan_query`
- `category_requirement_query`
- `regulation_query`
- `student_record_query`
- `general_chat`

The public route names remain compatible with the rest of the system:

- `kg`
- `rag`
- `mental`
- `elective`
- `hybrid`

### RAG Service

`advisor_ai/rag_service.py` implements academic regulation retrieval. Production uses OpenAI hosted vector stores and the Responses API file-search tool. The service also includes deterministic known-answer rules for high-confidence facts, such as:

- graduation requires 144 credit hours
- regular semester duration is 17 weeks
- summer semester duration is 8 weeks
- summer registration maximum is 9 credit hours
- CGPA-based credit load limits
- attendance and absence rules
- withdrawal rules
- registration, add/drop, final absence, academic warning, honor, dismissal, final-chance, grade-symbol, grievance, transfer, admission, and graduate-affairs rules

If file search does not return a strong answer, a local cleaned-text fallback searches the extracted regulation Markdown and clean excerpts.

### Knowledge Graph Service

`advisor_ai/kg_service.py` implements graph-backed course reasoning using Neo4j Aura. It supports:

- course lookup by code or name
- course aliases such as `ML`, `OOP`, `Intro AI`
- prerequisite queries
- reverse prerequisite/unlock queries
- registration-order checks such as whether `Math 2` can be registered before `Math 1`
- blocked-course queries
- category course lists
- category required credit hours
- level/program study paths

The graph is populated by `advisor_ai/populate_kg.py`, which creates:

- Program nodes
- Category nodes
- Course nodes
- `OFFERS`, `HAS_CATEGORY`, `BELONGS_TO`, and `REQUIRES` relationships

### Mental and Academic Support Service

`advisor_ai/mental_service.py` handles emotional and study-support prompts. It is not a medical tool; it provides academic support, study planning advice, encouragement, and referral to university support services when needed.

The graph routes mental-support prompts when it detects wording such as:

- stress
- fear of failure
- anxiety
- study tips
- Arabic/Egyptian Arabic equivalents such as `خايف`, `قلقان`, `مش عارف اذاكر`, and `نصائح للمذاكرة`

### Elective Service

`advisor_ai/elective_service.py` handles active-term elective questions. Admin endpoints and helper scripts allow updating elective lists and active term values. If a user asks about available electives for the current term, the graph routes the question to the elective node.

### Language Handling

`advisor_ai/language_utils.py` detects Arabic, Egyptian Arabic, Arabizi, and mixed Arabic-English input. The system uses this to keep responses in the user's language:

- English-only questions receive English answers.
- Arabic and Egyptian Arabic questions receive Arabic/Egyptian-style answers.
- Mixed Arabic-English questions preserve official English terms such as `CGPA`, course codes, and course names while answering in Arabic.

## 5.5 Integration

### Frontend and Backend Integration

The frontend integrates with the backend through JSON REST endpoints. The normal frontend flow is:

1. Call `POST /sessions` to create a new session.
2. Store the returned `session_id`.
3. Send each message to `POST /chat` with:

```json
{
  "student_id": "225241",
  "session_id": "generated-session-id",
  "message": "What are the prerequisites for Machine Learning?"
}
```

4. Display the returned `response` field directly in the chat UI.
5. Use `GET /sessions` and `GET /history` to show recent chats and previous messages.

### Backend and OpenAI Integration

OpenAI is used in three ways:

1. **Semantic routing**
   - The router asks the model to classify intent and return strict JSON.

2. **RAG retrieval**
   - The regulations file is uploaded into an OpenAI vector store.
   - The RAG service queries the vector store using file search.

3. **Support and synthesis**
   - Mental support and some fallback responses use OpenAI chat models.

### Backend and Neo4j Integration

Neo4j Aura is integrated using the official Neo4j Python driver. The backend opens a session against the configured database and executes Cypher queries for course and prerequisite data.

Examples of graph query outputs include:

- prerequisites for `AI301`
- courses unlocked by `AI301`
- whether `MTH103` Mathematics 2 can be registered before `MTH101` Mathematics 1
- level 3 AI courses
- university compulsory requirements

### Backend and Supabase Integration

Supabase stores:

- chat sessions
- message history
- timestamps
- generated session titles
- optional student level and major

The chat controller retrieves previous messages for `/history`, session display, and compact memory context. The semantic router still makes the route decision from the current message, while KG follow-up handling can use recent course context when the user asks a short relationship question.

### Deployment Integration

Vercel integrates with the backend through `api/index.py` and `vercel.json`. The Vercel deployment rewrites every incoming request to the FastAPI entrypoint:

```json
{
  "source": "/(.*)",
  "destination": "/api/index.py"
}
```

The production API uses Vercel environment variables for OpenAI, Neo4j, Supabase, and optional LangSmith tracing.

## 5.6 Deployment or Prototype Setup

### Local Prototype Setup

1. Clone or open the project directory.
2. Create a virtual environment.
3. Install dependencies.
4. Configure `.env`.
5. Populate Neo4j.
6. Create the OpenAI vector store.
7. Start FastAPI locally.

Commands:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m advisor_ai.populate_kg --reset
python scripts/setup_openai_vector_store.py
uvicorn advisor_ai.main:app --reload
```

Local API:

```text
http://localhost:8000
```

### Vercel Production Deployment

The project is configured for Vercel with `vercel.json`:

```json
{
  "buildCommand": null,
  "functions": {
    "api/index.py": {
      "memory": 1024,
      "maxDuration": 60
    }
  },
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/api/index.py"
    }
  ]
}
```

Deployment command:

```bash
npx vercel deploy --prod --yes
```

Production API:

```text
https://smart-academic-advisor-api.vercel.app
```

### Production Health Validation

The `/health` endpoint validates the main runtime dependencies:

```text
GET /health
```

Production status after deployment:

| Dependency | Status |
|---|---|
| KG / Neo4j Aura | Connected |
| RAG / OpenAI vector store | Initialized and configured |
| Supabase history | Connected |
| FastAPI service | Running |

### Production Chat Validation

Production `/chat` was tested using fresh sessions for RAG, KG, and mental support across:

- English
- Arabic
- Egyptian Arabic
- Mixed Arabic-English

The production multilingual check report is stored in:

```text
docs/production_multilingual_chat_checks_2026_05_12.md
```

## 5.7 Challenges and Solutions

| Challenge | Technical Impact | Solution Implemented |
|---|---|---|
| Routing mixed semantic and deterministic logic too early | Study-plan questions could be misclassified as category queries | Refactored routing to semantic-first with deterministic validation after LLM classification. |
| Fuzzy category matching could override better intent decisions | University requirements and study-plan questions could produce wrong KG answers | Restricted fuzzy matching to fallback cases and added exact compulsory/elective validation. |
| Arabic and Egyptian Arabic wording variations | Some correct questions missed deterministic rules | Added normalization and keyword coverage for Arabic spelling variants and Egyptian Arabic phrasing. |
| RAG local fallback differed from production vector-store behavior | Local validation did not always match production answers | Tested both local scripts and production `/chat`; added deterministic RAG fixes for high-confidence facts. |
| Graduation-hours Arabic prompt missed `144` | Arabic-only production prompt returned out-of-scope | Added direct RAG rules for `كم ساعة`, `ساعه معتمده`, `يتخرج`, and `اتخرج` wording. |
| Mental Arabic prompt with `قلقان` missed support routing | Arabic mental-support prompt returned out-of-scope | Added Arabic mental routing terms such as `قلقان`, `قلقانه`, and `نصائح للمذاكرة`. |
| Follow-up rewriting caused latency and wrong intent reuse | Questions like "what does it open?" could inherit the previous prerequisite intent and slow production requests | Disabled broad runtime follow-up routing/rewrite; kept Supabase history for UI, recents, and compact memory only. |
| Vague short course follow-ups still needed limited context | A student may ask "after it?" or "what does it open?" after asking about a course | Kept compact history available to KG relationship handling, while keeping semantic route classification current-message-first. |
| Students ask registration order as a yes/no question | A prerequisite list alone does not directly answer "Can I register Math 2 before Math 1?" | Added two-course KG registration-order checks that compare prerequisite paths and answer yes/no in the user's language. |
| Some regulation topics needed broader coverage than stable hardcoded facts | Production-style prompts about transfer, admission, dismissal, grade symbols, grievances, and graduate affairs could retrieve weak snippets | Added formalization, search-term expansion, local clean-text fallback, and a 98-case RAG regression suite. |
| Vercel serverless deployment has package and file-size limits | Local PDF/desktop assets should not be uploaded | Used `.vercelignore` and hosted OpenAI vector stores instead of local vector databases. |
| Secrets must not be committed | API keys and database passwords are sensitive | Used `.env` locally and Vercel environment variables in production. |
| Neo4j availability may vary | KG queries can fail if database is unavailable | Added status endpoints and graceful fallback messages. |
| Multi-language response consistency | Mixed Arabic-English prompts can produce inconsistent language | Added language utilities and strict language instructions. |

## Final Implementation Status

| Area | Status |
|---|---|
| FastAPI backend | Complete |
| Vercel deployment | Complete |
| OpenAI RAG | Complete and production-tested |
| Neo4j KG | Complete and production-tested |
| Supabase history | Complete and production-tested |
| Semantic routing | Refactored and tested |
| Follow-up handling | Current-message-first routing with limited KG history support |
| KG registration-order checks | Implemented and tested |
| Arabic/Egyptian Arabic support | Implemented and production-tested |
| Mixed Arabic-English support | Implemented and production-tested |
| Mental academic support | Implemented and production-tested |
| Mobile API documentation | Available |
| Automated tests | Passing: 123 local tests plus focused script checks |

# Smart Academic Advisor 🎓🤖

An AI-powered academic advisor for the Faculty of Artificial Intelligence (ERU), built with **FastAPI**, **LangGraph**, and **Neo4j Aura**.

This system helps students with course prerequisites, university regulations, elective choices, and academic guidance, using a sophisticated backend-driven architecture.

## 🌟 Key Features

### 1. 🧠 Intelligent RAG (Policy & Regulations)
- **Static Regulation Retrieval**: Fast answers about university bylaws, grading systems, and credit hours.
- **Vector Search**: Uses OpenAI vector stores and file search for semantic retrieval.
- **Vercel Friendly**: Uses a hosted vector store instead of local ChromaDB files.
- **Language Aware**: Maintains the language of the query (Arabic/English/Arabizi).

### 2. 🕸️ Knowledge Graph (AI & Cyber Programs)
- **Neo4j Aura Integration**: Models the complex dependencies of the AI and Cybersecurity curriculums.
- **Recursive Logic**: Traces deep prerequisite chains (e.g., "What do I need for Machine Learning?").
- **Fuzzy Matching**: Uses `difflib` to understand "Intro to AI" or "CS101" accurately.

### 3. 💬 Smart Session Management
- **Supabase History**: Persists chat sessions and message history in the cloud.
- **Context Awareness**: Remembers previous messages to resolve pronouns (e.g., "What opens *it*?").
- **Dynamic Identification**: Automatically asks for Student Level (1-4) and Major (AI/Cyber) when needed.

### 4. 💙 Mental & Academic Support
- **Guidance Node**: Provides academic motivation and study tips (non-medical).
- **Major Comparison**: Helps Level 2 students choose between AI and Cybersecurity programs.
- **Emotional Intelligence**: Detects stress/anxiety keywords and responds with empathy.

### 5. 📋 Dynamic Elective Admin
- **Term Management**: Admins set the active term (e.g., "Spring-2026").
- **Multi-Format Upload**: Supports Excel, PDF, Image (OCR), and Text inputs for schedules.
- **User View**: Students only see electives valid for the current active term.

---

## 🛠️ Tech Stack & Requirements

The deployable API uses a Vercel-friendly dependency set (`requirements.txt`):

- **Core Backend**: `fastapi`, `uvicorn`, `pydantic`.
- **Orchestration**: `langgraph`, `langchain`, `langchain-openai`.
- **Data & AI**: `openai`, OpenAI vector stores, `neo4j`.
- **Utilities**: `supabase` (DB), `python-dotenv`, `pyyaml`.

Local-only extras for Streamlit and PDF/Excel elective uploads live in `requirements-full.txt`.

---

## 📂 Project Structure

A clean, flat backend architecture optimized for maintainability:

### Core Application (`advisor_ai/`)
- **`main.py`**: The FastAPI entry point. Handles HTTP requests, CORS, and lazy-loading of services.
- **`graph.py`**: The **Brain**. A `LangGraph` state machine that routes queries to the correct service (KG, RAG, Mental, Elective) and manages conversation state.
- **`chat_controller.py`**: The **Session Manager**. Handles session persistence to Supabase and converts history into a format the Graph can understand.
- **`constants.py`**: **Configuration Center**. Stores all system prompts, routing keywords, and configuration constants in one place.

### Services (`advisor_ai/`)
- **`kg_service.py`**: Manages **Neo4j** interactions. Handles fuzzy course matching, intent classification, and prerequisite queries.
- **`rag_service.py`**: Queries an OpenAI vector store that contains the extracted regulations text.
- **`mental_service.py`**: Provides empathetic academic support and program recommendations using specialized LLM prompts.
- **`elective_service.py`**: Handles term-specific elective data. Supports ingestion from multiple file formats.
- **`supabase_client.py`**: simple wrapper to connect to the Supabase database.

### Tools & Scripts
- **`admin_upload.py`**: CLI tool for admins to upload elective schedules and set the active term without touching the code.
- **`advisor_ai/streamlit_app.py`**: A lightweight GUI for testing the API endpoints during development.

---

## 🚀 Setup & Installation

### 1. Environment
**Python 3.12+** is required.
```bash
python -m venv .venv
# Windows
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force; .\.venv\Scripts\Activate.ps1
# Mac/Linux
source .venv/bin/activate
```

### 2. Dependencies
```bash
pip install -r requirements.txt
```

For local admin PDF/Excel uploads and Streamlit testing:
```bash
pip install -r requirements-full.txt
```

### 3. Configuration
Create a `.env` file with your credentials:
```env
OPENAI_API_KEY=sk-...
OPENAI_VECTOR_STORE_ID=vs_...
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=your-aura-username
NEO4J_PASSWORD=your-aura-password
NEO4J_DATABASE=your-aura-database
AURA_INSTANCEID=your-instance-id
AURA_INSTANCENAME=smartadvisor
SUPABASE_URL=https://...
SUPABASE_KEY=...
```

You can copy `.env.example` as the starting point.

### 4. Create the OpenAI Vector Store
Run this once after configuring `OPENAI_API_KEY`:
```bash
python scripts/setup_openai_vector_store.py
```

Copy the printed `OPENAI_VECTOR_STORE_ID=vs_...` into `.env` and into your Vercel environment variables.

### 5. Populate Neo4j Aura
```bash
python -m advisor_ai.populate_kg --reset
```

The backend connects to the configured Neo4j Aura URI and database.

---

## 🏃‍♂️ Usage

### 1. Start the Backend Server
```bash
uvicorn advisor_ai.main:app --reload
```
API runs at: `http://localhost:8000`

### 2. Admin: Manage Electives
Use the CLI tool to update the system for a new term:
```bash
# Set the active term
python admin_upload.py --term "Spring-2026"

# Upload a schedule file
python admin_upload.py --file "schedules/Spring2026_Electives.xlsx"
```

### 3. Test the Interface
Launch the Streamlit app to chat with the advisor:
```bash
streamlit run advisor_ai/streamlit_app.py
```

---

## 🔌 API Endpoints

### Student Chat
- **POST** `/chat`: Main interaction endpoint. Requires `session_id` and `message`.
- **GET** `/history`: Retrieve past conversation history for a session.

### Admin Controls
- **POST** `/admin/upload-electives`: Backend endpoint for uploading schedule files.
- **POST** `/admin/set-term`: Backend endpoint for changing the academic term.
- **GET** `/admin/kg/status`: Check Neo4j connection and KG counts.
- **GET** `/admin/rag/status`: Check OpenAI vector-store RAG status.
- **GET** `/admin/history/status`: Check Supabase history status.
- **GET** `/health`: Combined service health check.

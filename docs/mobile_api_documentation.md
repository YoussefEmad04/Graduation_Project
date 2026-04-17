# Smart Academic Advisor API Documentation

Technical reference for the mobile developer after the FastAPI backend is deployed to Vercel.

## Base URL

Use the Vercel deployment domain as the base URL:

```text
https://<your-vercel-project>.vercel.app
```

Vercel routes all paths to `api/index.py`, which imports `advisor_ai.main:app`.

## Vercel Deployment Option

The backend is configured for Vercel using `vercel.json`.

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

### Vercel URL Options For Mobile

Use one of these URL options in the mobile app config:

```json
{
  "production_base_url": "https://<project-name>.vercel.app",
  "preview_base_url": "https://<project-name>-git-<branch>-<team>.vercel.app",
  "custom_domain_base_url": "https://api.your-domain.com"
}
```

Recommended mobile setup:

```json
{
  "dev": {
    "api_base_url": "http://localhost:8000"
  },
  "staging": {
    "api_base_url": "https://<vercel-preview-url>"
  },
  "production": {
    "api_base_url": "https://<vercel-production-url>"
  }
}
```

Required Vercel environment variables:

```json
{
  "OPENAI_API_KEY": "required",
  "OPENAI_VECTOR_STORE_ID": "required for regulations RAG",
  "OPENAI_LLM_MODEL": "optional, defaults in code",
  "NEO4J_URI": "required for knowledge graph",
  "NEO4J_USERNAME": "required for knowledge graph",
  "NEO4J_PASSWORD": "required for knowledge graph",
  "NEO4J_DATABASE": "optional",
  "SUPABASE_URL": "required for chat history",
  "SUPABASE_KEY": "required for chat history",
  "LANGCHAIN_TRACING_V2": "optional",
  "LANGCHAIN_API_KEY": "optional",
  "LANGCHAIN_PROJECT": "optional",
  "LANGCHAIN_ENDPOINT": "optional"
}
```

## General Notes

- API framework: FastAPI
- API version: `1.0.0`
- Content type for JSON endpoints: `application/json`
- Content type for elective upload: `multipart/form-data`
- CORS: currently allows all origins, methods, and headers
- Validation errors return FastAPI's standard HTTP `422` response
- Session history is persisted in Supabase when `SUPABASE_URL` and `SUPABASE_KEY` are configured

## Error Schema

FastAPI validation errors use this structure:

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "Field required",
      "type": "missing",
      "input": {}
    }
  ]
}
```

## POST /sessions

Creates a new ChatGPT-style chat session for one student. The mobile app sends the logged-in `student_id`, and the backend returns the new `session_id`.

### Request

```http
POST /sessions
Content-Type: application/json
```

Endpoint URL:

```text
https://<your-vercel-project>.vercel.app/sessions
```

Request JSON sample:

```json
{
  "student_id": "225241",
  "title": "Machine Learning prerequisites"
}
```

`title` is optional. If it is not sent, the backend initially uses `New chat`, then uses OpenAI to rename the chat after the first meaningful topic message.

### Success Response

Status: `200 OK`

```json
{
  "student_id": "225241",
  "session_id": "4f1117fa-4284-4ef4-9c8a-7f90597ebf54",
  "title": "Machine Learning prerequisites"
}
```

## GET /sessions

Returns ChatGPT-style recent chats as a JSON array, newest first. Pass `student_id` to filter the list to one student, or omit it to return all sessions.

### Request

```http
GET /sessions?student_id=225241
```

### Success Response

Status: `200 OK`

```json
[
  {
    "student_id": "225241",
    "session_id": "4f1117fa-4284-4ef4-9c8a-7f90597ebf54",
    "title": "Machine Learning prerequisites",
    "last_message": "Machine Learning requires ...",
    "created_at": "2026-04-16T12:00:00Z",
    "updated_at": "2026-04-16T12:05:00Z"
  }
]
```

## POST /chat

Main student chat endpoint. The mobile app should call `POST /sessions` first, then send the returned `session_id` with every chat message.

Special reset messages are handled by the backend:

```text
start, new, reset, /start
```

### Request

```http
POST /chat
Content-Type: application/json
```

Endpoint URL:

```text
https://<your-vercel-project>.vercel.app/chat
```

Request JSON sample:

```json
{
  "student_id": "225241",
  "session_id": "4f1117fa-4284-4ef4-9c8a-7f90597ebf54",
  "message": "What are the prerequisites for Machine Learning?"
}
```

### Request Schema

```json
{
  "student_id": "string, required",
  "session_id": "string, required",
  "message": "string, required",
  "title": "string, optional"
}
```

### Success Response

Status: `200 OK`

```json
{
  "student_id": "225241",
  "session_id": "4f1117fa-4284-4ef4-9c8a-7f90597ebf54",
  "response": "Machine Learning requires ..."
}
```

### Response Schema

```json
{
  "student_id": "string",
  "session_id": "string",
  "response": "string"
}
```

### Mobile Usage Notes

- Use `POST /sessions` when the student taps New Chat.
- Store the returned `session_id` in the frontend for that chat thread.
- Send both `student_id` and `session_id` with every `POST /chat` request.
- Send `message: "start"` to begin or reset a conversation.
- Reset messages only reset that selected `(student_id, session_id)` chat.
- Session titles can start as `New chat`; call `GET /sessions` again after the student sends a real topic question to get the OpenAI-generated title.
- If the student sends only `1`, `2`, `3`, or `4`, the backend stores the student level.
- For Level 1 and Level 2, the backend sets the major to `General`.
- For Level 3 and Level 4, the advisor can ask or infer whether the student is AI or Cybersecurity.
- Show the `response` string directly in the chat UI.

### cURL Example

```bash
curl -X POST "https://<your-vercel-project>.vercel.app/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "225241",
    "session_id": "4f1117fa-4284-4ef4-9c8a-7f90597ebf54",
    "message": "start"
  }'
```

## GET /history

Returns saved chat history for one session.

### Request

```http
GET /history?student_id=225241&session_id=4f1117fa-4284-4ef4-9c8a-7f90597ebf54
```

Endpoint URL:

```text
https://<your-vercel-project>.vercel.app/history?student_id=225241&session_id=4f1117fa-4284-4ef4-9c8a-7f90597ebf54
```

Request JSON sample:

```json
{
  "method": "GET",
  "url": "/history",
  "query": {
    "student_id": "225241",
    "session_id": "4f1117fa-4284-4ef4-9c8a-7f90597ebf54"
  },
  "body": null
}
```

### Query Parameters

```json
{
  "student_id": "string, required",
  "session_id": "string, required"
}
```

### Success Response

Status: `200 OK`

```json
{
  "student_id": "225241",
  "session_id": "4f1117fa-4284-4ef4-9c8a-7f90597ebf54",
  "history": [
    {
      "role": "user",
      "content": "What are the AI electives?",
      "created_at": "2026-04-16T12:00:00Z"
    },
    {
      "role": "assistant",
      "content": "The current electives are ...",
      "created_at": "2026-04-16T12:00:05Z"
    }
  ]
}
```

### Response Schema

```json
{
  "student_id": "string",
  "session_id": "string",
  "history": [
    {
      "role": "string: user | assistant",
      "content": "string",
      "created_at": "string timestamp from Supabase"
    }
  ]
}
```

### Mobile Usage Notes

- Use this endpoint to restore a previous chat screen.
- If Supabase is unavailable or not configured, `history` can return an empty array.

## POST /admin/upload-electives

Admin endpoint for replacing the active term elective list from JSON.

```http
POST /admin/upload-electives
Content-Type: application/json
```

Endpoint URL:

```text
https://<your-vercel-project>.vercel.app/admin/upload-electives
```

Request body:

```json
{
  "electives": [
    "AI Ethics",
    "Cloud Computing",
    "Computer Vision"
  ]
}
```

### Success Response

Status: `200 OK`

```json
{
  "status": "success",
  "message": "Uploaded 3 electives: AI Ethics, Cloud Computing, Computer Vision"
}
```

### Error Response

Status: `200 OK`

```json
{
  "status": "error",
  "message": "No electives provided."
}
```

### Response Schema

```json
{
  "status": "string: success | error",
  "message": "string"
}
```

### cURL Example

```bash
curl -X POST "https://<your-vercel-project>.vercel.app/admin/upload-electives" \
  -H "Content-Type: application/json" \
  -d '{"electives":["AI Ethics","Cloud Computing","Computer Vision"]}'
```

## POST /admin/set-term

Admin endpoint for changing the active academic term used by the elective service.

### Request

```http
POST /admin/set-term
Content-Type: application/json
```

Endpoint URL:

```text
https://<your-vercel-project>.vercel.app/admin/set-term
```

Request JSON sample:

```json
{
  "term": "Spring-2026"
}
```

### Request Schema

```json
{
  "term": "string, required"
}
```

### Success Response

Status: `200 OK`

```json
{
  "status": "success",
  "message": "Active term updated to: Spring-2026"
}
```

### Response Schema

```json
{
  "status": "string",
  "message": "string"
}
```

## GET /admin/kg/status

Checks Neo4j knowledge graph connectivity and graph counts.

### Request

```http
GET /admin/kg/status
```

Endpoint URL:

```text
https://<your-vercel-project>.vercel.app/admin/kg/status
```

Request JSON sample:

```json
{
  "method": "GET",
  "url": "/admin/kg/status",
  "query": {},
  "body": null
}
```

### Success Response

Status: `200 OK`

```json
{
  "connected": true,
  "uri": "neo4j+s://example.databases.neo4j.io",
  "user": "neo4j",
  "database": "neo4j",
  "counts": {
    "programs": 2,
    "categories": 10,
    "courses": 80,
    "prerequisites": 120
  },
  "last_error": null
}
```

### Response Schema

```json
{
  "connected": "boolean",
  "uri": "string",
  "user": "string",
  "database": "string | null",
  "counts": {
    "programs": "number",
    "categories": "number",
    "courses": "number",
    "prerequisites": "number"
  },
  "last_error": "string | null"
}
```

## GET /admin/rag/status

Checks the OpenAI file-search RAG configuration used for regulations and bylaws.

### Request

```http
GET /admin/rag/status
```

Endpoint URL:

```text
https://<your-vercel-project>.vercel.app/admin/rag/status
```

Request JSON sample:

```json
{
  "method": "GET",
  "url": "/admin/rag/status",
  "query": {},
  "body": null
}
```

### Success Response

Status: `200 OK`

```json
{
  "provider": "openai_file_search",
  "initialized": false,
  "openai_configured": true,
  "vector_store_configured": true,
  "vector_store_id": "vs_xxx",
  "retrieval_k": 4,
  "source_file": "path/to/regulations_extracted.md",
  "source_exists": true,
  "last_error": null
}
```

### Response Schema

```json
{
  "provider": "string",
  "initialized": "boolean",
  "openai_configured": "boolean",
  "vector_store_configured": "boolean",
  "vector_store_id": "string | null",
  "retrieval_k": "number",
  "source_file": "string",
  "source_exists": "boolean",
  "last_error": "string | null"
}
```

## GET /admin/history/status

Checks Supabase chat-history configuration and connectivity.

### Request

```http
GET /admin/history/status
```

Endpoint URL:

```text
https://<your-vercel-project>.vercel.app/admin/history/status
```

Request JSON sample:

```json
{
  "method": "GET",
  "url": "/admin/history/status",
  "query": {},
  "body": null
}
```

### Success Response

Status: `200 OK`

```json
{
  "configured": true,
  "connected": true,
  "url_configured": true,
  "key_configured": true,
  "last_error": null
}
```

### Response Schema

```json
{
  "configured": "boolean",
  "connected": "boolean",
  "url_configured": "boolean",
  "key_configured": "boolean",
  "last_error": "string | null"
}
```

## GET /

Basic health check.

### Request

```http
GET /
```

Endpoint URL:

```text
https://<your-vercel-project>.vercel.app/
```

Request JSON sample:

```json
{
  "method": "GET",
  "url": "/",
  "query": {},
  "body": null
}
```

### Success Response

Status: `200 OK`

```json
{
  "service": "Smart Academic Advisor",
  "status": "running",
  "version": "1.0.0"
}
```

### Response Schema

```json
{
  "service": "string",
  "status": "string",
  "version": "string"
}
```

## GET /health

Dependency-aware health check. This calls the KG, RAG, and history status checks.

### Request

```http
GET /health
```

Endpoint URL:

```text
https://<your-vercel-project>.vercel.app/health
```

Request JSON sample:

```json
{
  "method": "GET",
  "url": "/health",
  "query": {},
  "body": null
}
```

### Success Response

Status: `200 OK`

```json
{
  "service": "Smart Academic Advisor",
  "status": "running",
  "version": "1.0.0",
  "dependencies": {
    "kg": {
      "connected": true,
      "counts": {
        "programs": 2,
        "categories": 10,
        "courses": 80,
        "prerequisites": 120
      },
      "last_error": null
    },
    "rag": {
      "provider": "openai_file_search",
      "openai_configured": true,
      "vector_store_configured": true,
      "last_error": null
    },
    "history": {
      "configured": true,
      "connected": true,
      "last_error": null
    }
  }
}
```

### Response Schema

```json
{
  "service": "string",
  "status": "string",
  "version": "string",
  "dependencies": {
    "kg": "object from GET /admin/kg/status",
    "rag": "object from GET /admin/rag/status",
    "history": "object from GET /admin/history/status"
  }
}
```

## Mobile Integration Checklist

1. Store the Vercel base URL in app configuration.
2. Get the logged-in `student_id` from the mobile app user profile/auth flow.
3. Call `POST /sessions` when the student taps New Chat and store the returned `session_id`.
4. Call `POST /chat` for every message with both `student_id` and `session_id`.
5. Render the `response` field in the chat UI.
6. Call `GET /sessions?student_id=...` to show ChatGPT-style recents.
7. Call `GET /history?student_id=...&session_id=...` when restoring a conversation.
8. Treat HTTP `422` as a client request-shape bug.
9. Treat admin endpoints as protected in the mobile product unless the app has an admin-only screen.
10. Use `/health` after deployment to verify OpenAI, Neo4j, and Supabase dependencies.

## Recommended Mobile Models

### SessionCreateRequest

```ts
type SessionCreateRequest = {
  student_id: string;
  title?: string;
};
```

### SessionCreateResponse

```ts
type SessionCreateResponse = {
  student_id: string;
  session_id: string;
  title: string;
};
```

### SessionListResponse

```ts
type SessionListResponse = Array<{
  student_id: string;
  session_id: string;
  title?: string;
  last_message: string;
  created_at?: string;
  updated_at?: string;
}>;
```

### ChatRequest

```ts
type ChatRequest = {
  student_id: string;
  session_id: string;
  message: string;
  title?: string;
};
```

### ChatResponse

```ts
type ChatResponse = {
  student_id: string;
  session_id: string;
  response: string;
};
```

### HistoryResponse

```ts
type HistoryResponse = {
  student_id: string;
  session_id: string;
  history: Array<{
    role: "user" | "assistant";
    content: string;
    created_at: string;
  }>;
};
```

### StatusResponse

```ts
type StatusResponse = {
  status: "success" | "error" | string;
  message: string;
};
```

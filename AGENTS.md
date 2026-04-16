# Repository Guidelines

## Project Structure & Module Organization

This repository is a Python FastAPI backend for the Smart Academic Advisor.

- `advisor_ai/`: main application package. `main.py` exposes API routes, `graph.py` routes advisor flows, `rag_service.py` uses OpenAI vector-store file search, `kg_service.py` connects to Neo4j Aura, and `chat_controller.py` manages sessions/history.
- `api/index.py`: Vercel FastAPI entrypoint.
- `scripts/`: operational scripts, including OpenAI vector-store setup.
- `tests/`: smoke tests for routing, KG config, and RAG behavior.
- `important_pdf/`: source and extracted academic regulation content.
- `pdf/` and `High_Diagrams/`: presentation/reference assets, not runtime code.

## Build, Test, and Development Commands

Create and activate a virtual environment before running commands:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the API locally:

```bash
uvicorn advisor_ai.main:app --reload
```

Populate Neo4j Aura after configuring `.env`:

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

## Coding Style & Naming Conventions

Use Python 3 with 4-space indentation. Use `snake_case` for functions, variables, and modules; use `PascalCase` for classes. Keep service-specific logic in its service module and shared routing constants/prompts in `advisor_ai/constants.py`. Prefer explicit handling for external services such as OpenAI, Neo4j Aura, Supabase, and Vercel.

## Testing Guidelines

Tests use the standard `unittest` framework. Test files should be named `test_*.py`, with focused classes such as `RoutingSmokeTests` or `KgConfigSmokeTests`. Add tests for routing changes, environment parsing, external-service fallbacks, and API behavior that affects Flutter integration.

## Commit & Pull Request Guidelines

Use short imperative commit messages, for example `Move KG to Neo4j Aura` or `Fix RAG file search status`. Pull requests should include a concise summary, commands run, environment changes, and any API behavior changes. Include screenshots only for UI-facing changes.

## Security & Configuration Tips

Never commit real secrets. Keep credentials in `.env` and Vercel environment variables. Required services are OpenAI, Neo4j Aura, Supabase, and optionally LangSmith. Use `/health`, `/admin/kg/status`, `/admin/rag/status`, and `/admin/history/status` to verify runtime dependencies.

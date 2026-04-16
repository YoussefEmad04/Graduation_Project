"""
Create or refresh the OpenAI vector store used by regulation RAG.

Run from the project root:
    python scripts/setup_openai_vector_store.py

The script prints OPENAI_VECTOR_STORE_ID, which should be added to .env and
to Vercel environment variables.
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PROJECT_ROOT / "important_pdf" / "RAG" / "regulations_extracted.md"
DEFAULT_NAME = "smart-academic-advisor-regulations"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Upload regulations text to an OpenAI vector store."
    )
    parser.add_argument(
        "--source",
        default=str(DEFAULT_SOURCE),
        help="Path to the extracted regulations text/markdown file.",
    )
    parser.add_argument(
        "--name",
        default=DEFAULT_NAME,
        help="Name for the OpenAI vector store.",
    )
    return parser.parse_args()


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env")
    args = parse_args()
    source = Path(args.source).expanduser().resolve()

    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not configured.", file=sys.stderr)
        return 1
    if not source.exists():
        print(f"Source file not found: {source}", file=sys.stderr)
        return 1

    client = OpenAI()
    vector_store = client.vector_stores.create(
        name=args.name,
        metadata={"project": "smart-academic-advisor", "source": source.name},
    )

    with source.open("rb") as file_handle:
        uploaded_file = client.files.create(file=file_handle, purpose="assistants")

    batch = client.vector_stores.file_batches.create(
        vector_store_id=vector_store.id,
        file_ids=[uploaded_file.id],
    )
    completed_batch = client.vector_stores.file_batches.poll(
        batch.id,
        vector_store_id=vector_store.id,
    )

    print(f"Vector store: {vector_store.id}")
    print(f"Uploaded file: {uploaded_file.id}")
    print(f"Batch status: {completed_batch.status}")
    print()
    print("Add this to .env and Vercel environment variables:")
    print(f"OPENAI_VECTOR_STORE_ID={vector_store.id}")

    if completed_batch.status != "completed":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

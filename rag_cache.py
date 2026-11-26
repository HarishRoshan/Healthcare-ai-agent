
import hashlib
import os
import sys
import json
from pathlib import Path

from rag_loader import load_document, chunk_document
from rag_embeddings import create_embeddings


BASE_DIR = Path(__file__).resolve().parent
CACHE_PATH = Path(
    os.environ.get(
        "AURA_RAG_CACHE_PATH",
        str(BASE_DIR / "rag_embeddings_cache.json")
    )
)

CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

EMBEDDING_MODEL = "text-embedding-3-small"


def get_document_hash(text):
    """Create a fingerprint of the document content."""
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def load_or_create_embeddings():
    """Reuse embeddings unless the document changed."""

    document = load_document()
    chunks = chunk_document(document)

    document_hash = get_document_hash(document)

    if CACHE_PATH.exists():
        try:
            cache = json.loads(
                CACHE_PATH.read_text(encoding="utf-8")
            )

            if (
                cache.get("document_hash") == document_hash
                and cache.get("model") == EMBEDDING_MODEL
                and cache.get("chunks") == chunks
                and len(cache.get("embeddings", [])) == len(chunks)
            ):
                print("Using cached embeddings.", file=sys.stderr)
                return chunks, cache["embeddings"]

        except (json.JSONDecodeError, OSError, TypeError):
            print("Cache unreadable. Rebuilding.", file=sys.stderr)

    print("Generating new embeddings...", file=sys.stderr)

    embeddings = create_embeddings(chunks)

    cache_data = {
        "document_hash": document_hash,
        "model": EMBEDDING_MODEL,
        "chunks": chunks,
        "embeddings": embeddings
    }

    CACHE_PATH.write_text(
        json.dumps(cache_data),
        encoding="utf-8"
    )

    return chunks, embeddings


if __name__ == "__main__":
    chunks, embeddings = load_or_create_embeddings()

    print(f"Chunks: {len(chunks)}")
    print(f"Embeddings: {len(embeddings)}")


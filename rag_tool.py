"""Retrieve relevant fictional AURA clinic policy sections."""

import sys
import time

from rag_cache import load_or_create_embeddings
from rag_search import search_documents


def search_clinic_policy(question):
    """Retrieve relevant fictional clinic policy sections."""
    if not isinstance(question, str) or not question.strip():
        raise ValueError("A policy question is required")

    cache_start = time.perf_counter()
    chunks, embeddings = load_or_create_embeddings()
    cache_ms = (time.perf_counter() - cache_start) * 1000

    search_start = time.perf_counter()
    results = search_documents(question, chunks, embeddings)
    search_ms = (time.perf_counter() - search_start) * 1000

    # MCP stdio reserves stdout for protocol messages.
    print(
        f"operation=rag_cache_load duration_ms={cache_ms:.2f}",
        file=sys.stderr,
    )
    print(
        f"operation=rag_search duration_ms={search_ms:.2f}",
        file=sys.stderr,
    )

    top_results = results[:2]
    matches = []

    for score, chunk in top_results:
        matches.append({
            "source": "AURA-POL-001",
            "similarity_score": round(score, 4),
            "content": chunk,
        })

    return {"question": question, "matches": matches}


if __name__ == "__main__":
    result = search_clinic_policy("How can I reschedule my appointment?")
    for match in result["matches"]:
        print(f"\nSource: {match['source']}")
        print(f"Similarity: {match['similarity_score']}")
        print(match["content"])

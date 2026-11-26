import sys

import os
from aura_input_guard import count_tokens

from openai import OpenAI
from rag_loader import load_document, chunk_document


def create_embeddings(chunks):
    """Convert text chunks into numerical vectors."""

    if not isinstance(chunks, list) or not chunks:
        raise ValueError("Document chunks are required")

    if len(chunks) > 50:
        raise ValueError("Maximum document chunks exceeded")

    token_counts = [count_tokens(chunk) for chunk in chunks]

    if any(count > 1000 for count in token_counts):
        raise ValueError("Document chunk token limit exceeded")

    if sum(token_counts) > 10000:
        raise ValueError("Document embedding token limit exceeded")

    client = OpenAI(timeout=30.0, max_retries=0)

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=chunks
    )

    usage = getattr(response, "usage", None)

    if usage is not None:
        print(
            f"operation=embedding_token_usage "
            f"prompt_tokens={getattr(usage, 'prompt_tokens', None)} "
            f"total_tokens={getattr(usage, 'total_tokens', None)}",
            file=sys.stderr,
        )

    embeddings = [
        item.embedding
        for item in response.data
    ]

    return embeddings


if __name__ == "__main__":

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not configured"
        )

    document = load_document()
    chunks = chunk_document(document)

    print(f"Loaded {len(chunks)} chunks")

    embeddings = create_embeddings(chunks)

    print(f"Created {len(embeddings)} embeddings")

    if embeddings:
        print(
            f"Numbers per embedding: {len(embeddings[0])}"
        )
        print(
            f"First 5 numbers: {embeddings[0][:5]}"
        )





import os

from openai import OpenAI
from rag_loader import load_document, chunk_document


def create_embeddings(chunks):
    """Convert text chunks into numerical vectors."""

    client = OpenAI()

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=chunks
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

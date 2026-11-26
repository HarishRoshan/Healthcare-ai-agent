import sys

import math
from aura_input_guard import validate_question

from openai import OpenAI
from rag_loader import load_document, chunk_document
from rag_embeddings import create_embeddings
from functools import lru_cache


@lru_cache(maxsize=128)
def get_question_embedding(question):
    """Reuse embeddings for repeated policy questions."""

    validate_question(question)

    client = OpenAI(timeout=30.0, max_retries=0)

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=question
    )

    usage = getattr(response, "usage", None)

    if usage is not None:
        print(
            f"operation=embedding_token_usage "
            f"prompt_tokens={getattr(usage, 'prompt_tokens', None)} "
            f"total_tokens={getattr(usage, 'total_tokens', None)}",
            file=sys.stderr,
        )

    return response.data[0].embedding


def cosine_similarity(vector_a, vector_b):
    """Compare the direction of two vectors."""

    dot_product = sum(
        a * b for a, b in zip(vector_a, vector_b)
    )

    magnitude_a = math.sqrt(
        sum(a * a for a in vector_a)
    )

    magnitude_b = math.sqrt(
        sum(b * b for b in vector_b)
    )

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def search_documents(question, chunks, embeddings):
    """Find the most relevant document chunks."""

    # Reuse a cached embedding when the question repeats.
    question_embedding = get_question_embedding(question)

    results = []

    for chunk, embedding in zip(chunks, embeddings):
        score = cosine_similarity(
            question_embedding, embedding
        )

        results.append((score, chunk))

    results.sort(reverse=True, key=lambda item: item[0])

    return results


if __name__ == "__main__":
    document = load_document()
    chunks = chunk_document(document)

    print("Creating document embeddings...")
    embeddings = create_embeddings(chunks)

    question = "How can I change my appointment date?"

    print(f"\nQuestion: {question}")

    results = search_documents(
        question,
        chunks,
        embeddings
    )

    print("\nTOP 3 MATCHING CHUNKS")

    for score, chunk in results[:3]:
        print(f"\nSimilarity score: {score:.4f}")
        print(chunk)
        print("-----------------------------")





from openai import OpenAI

from rag_loader import load_document, chunk_document
from rag_embeddings import create_embeddings
from rag_search import search_documents


def answer_with_rag(question, chunks, embeddings):
    """Generate an answer using retrieved clinic policy."""

    results = search_documents(
        question,
        chunks,
        embeddings
    )

    # Retrieve the two highest-ranked chunks.
    top_results = results[:2]

    context_parts = []

    for score, chunk in top_results:
        context_parts.append(chunk)

    context = "\n\n".join(context_parts)

    client = OpenAI()

    response = client.responses.create(
        model="gpt-4.1-mini",
        instructions=(
            "You are AURA AI, an assistant for a fictional "
            "training clinic. Answer only using the provided "
            "clinic policy context. If the context does not "
            "contain the answer, say you cannot find that "
            "information in the available policy. "
            "Do not invent facts. "
            "Do not present the policy as official NHS guidance. "
            "When the context supports an answer, cite "
            "AURA-POL-001 and the relevant section number."
        ),
        input=(
            f"Clinic policy context:\n{context}\n\n"
            f"User question:\n{question}"
        )
    )

    return response.output_text


if __name__ == "__main__":

    document = load_document()
    chunks = chunk_document(document)

    print("Creating embeddings...")
    embeddings = create_embeddings(chunks)

    question = question = "Does AURA Demo Clinic provide free parking?"
    print(f"\nQuestion: {question}")

    answer = answer_with_rag(
        question,
        chunks,
        embeddings
    )

    print("\nAURA AI ANSWER")
    print("-----------------------------")
    print(answer)

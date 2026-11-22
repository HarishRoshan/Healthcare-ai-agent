
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

DOCUMENT_PATH = (
    BASE_DIR
    / "knowledge_base"
    / "appointment_policy.txt"
)


def load_document():
    """Read the fictional clinic policy document."""

    text = DOCUMENT_PATH.read_text(encoding="utf-8")

    return text


def chunk_document(text):
    """Split a document into sections using blank lines."""

    chunks = text.split("\n\n")

    cleaned_chunks = []

    for chunk in chunks:
        chunk = chunk.strip()

        if chunk:
            cleaned_chunks.append(chunk)

    return cleaned_chunks


if __name__ == "__main__":
    document = load_document()

    chunks = chunk_document(document)

    print("AURA AI — DOCUMENT CHUNKING")
    print("---------------------------")

    print(f"Total chunks: {len(chunks)}")

    for index, chunk in enumerate(chunks, start=1):
        print(f"\nCHUNK {index}")
        print(chunk)
        print("---------------------------")

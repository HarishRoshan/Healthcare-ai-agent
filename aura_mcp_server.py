
from pathlib import Path

from dotenv import load_dotenv

# Load AURA's existing environment configuration
# before importing the RAG implementation.
load_dotenv(
    dotenv_path=Path(__file__).resolve().parent / ".env"
)

from mcp.server.fastmcp import FastMCP
from rag_tool import search_clinic_policy


mcp = FastMCP("AURA Demo Clinic")


@mcp.tool()
def lookup_clinic_policy(question: str) -> dict:
    """Search the fictional AURA clinic policy documents."""

    if not question.strip():
        return {"error": "A policy question is required"}

    return search_clinic_policy(question)


if __name__ == "__main__":
    mcp.run(transport="stdio")

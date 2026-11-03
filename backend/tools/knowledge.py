"""Knowledge-base search tool for the support agent.

Wraps ``rag.search.search_chunks`` and exposes:
- ``TOOL_DEFINITION``: the Anthropic-format tool schema passed to Claude.
- ``search_knowledge``: the async callable executed when Claude picks this tool.
"""

from __future__ import annotations

from uuid import UUID

from integrations.embedding_interfaces.base_embedding_interface import (
    BaseEmbeddingInterface,
)
from rag.search import search_chunks

TOOL_DEFINITION: dict = {
    "name": "search_knowledge",
    "description": (
        "Search the company knowledge base to find answers to specific questions "
        "about the company's products, services, or procedures. "
        "Use this tool before answering any content question."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The question or text to search for in the knowledge base.",
            },
        },
        "required": ["query"],
    },
}


async def search_knowledge(
    query: str,
    company_id: UUID,
    *,
    top_k: int = 5,
    embedding_client: BaseEmbeddingInterface | None = None,
) -> str:
    """Execute a semantic search over the company's knowledge base.

    Args:
        query: The question or text to search for.
        company_id: Tenant identifier used to scope the search.
        top_k: Maximum number of chunks to return.
        embedding_client: Optional embedding client; uses the default if None.

    Returns:
        A formatted string with the most relevant knowledge-base excerpts, or
        a message indicating no results were found.
    """
    results = await search_chunks(
        query=query,
        company_id=company_id,
        top_k=top_k,
        embedding_client=embedding_client,
    )

    if not results:
        return "No results found in the knowledge base for this question."

    parts = [f"[{i}] {r.content}" for i, r in enumerate(results, start=1)]
    return "\n\n".join(parts)

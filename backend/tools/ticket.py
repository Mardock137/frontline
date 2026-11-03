"""Ticket creation tool for the support agent.

Exposes:
- ``TOOL_DEFINITION``: the Anthropic-format tool schema passed to Claude.
- ``create_ticket``: the callable executed when Claude picks this tool.
"""

from __future__ import annotations

import asyncio
from uuid import UUID

from supabase import Client

TOOL_DEFINITION: dict = {
    "name": "create_ticket",
    "description": (
        "Create a support ticket for issues that cannot be resolved "
        "immediately through the knowledge base and that need human attention, "
        "but are not immediately urgent. Do not use for urgent cases: in that case use "
        "the 'escalate' tool."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "subject": {
                "type": "string",
                "description": "Short, descriptive title of the issue.",
            },
            "description": {
                "type": "string",
                "description": "Detailed description of the issue reported by the customer.",
            },
        },
        "required": ["subject", "description"],
    },
}


async def create_ticket(
    subject: str,
    description: str,
    company_id: UUID,
    conversation_id: UUID,
    supabase: Client,
) -> str:
    """Insert a new support ticket in the database.

    Args:
        subject: Short title for the ticket.
        description: Detailed description of the issue.
        company_id: Tenant identifier.
        conversation_id: Conversation this ticket is linked to.
        supabase: Supabase client instance.

    Returns:
        A confirmation string with the new ticket ID.
    """
    row = {
        "company_id": str(company_id),
        "conversation_id": str(conversation_id),
        "subject": subject,
        "description": description,
        "status": "open",
        "is_escalation": False,
    }
    result = await asyncio.to_thread(
        lambda: supabase.table("tickets").insert(row).execute()
    )
    ticket_id = result.data[0]["id"] if result.data else "unknown"
    return f"Support ticket created with ID: {ticket_id}"

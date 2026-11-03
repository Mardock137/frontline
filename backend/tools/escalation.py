"""Escalation tool for the support agent.

Exposes:
- ``TOOL_DEFINITION``: the Anthropic-format tool schema passed to Claude.
- ``escalate``: the callable executed when Claude picks this tool.
"""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from supabase import Client

logger = logging.getLogger(__name__)

TOOL_DEFINITION: dict = {
    "name": "escalate",
    "description": (
        "Escalate the conversation to a human operator when the issue is urgent, "
        "complex, or needs a direct intervention from the company team. "
        "Use only when the issue cannot be handled autonomously and "
        "needs immediate attention."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "subject": {
                "type": "string",
                "description": "Short, descriptive title of the escalation reason.",
            },
            "description": {
                "type": "string",
                "description": (
                    "Detailed description of the issue and why "
                    "human intervention is required."
                ),
            },
        },
        "required": ["subject", "description"],
    },
}


async def escalate(
    subject: str,
    description: str,
    company_id: UUID,
    conversation_id: UUID,
    supabase: Client,
) -> str:
    """Create an escalation ticket and mark the conversation as ESCALATED.

    Args:
        subject: Short title for the escalation.
        description: Detailed reason for escalation.
        company_id: Tenant identifier.
        conversation_id: Conversation this escalation is linked to.
        supabase: Supabase client instance.

    Returns:
        A confirmation string indicating the conversation has been escalated.
    """
    row = {
        "company_id": str(company_id),
        "conversation_id": str(conversation_id),
        "subject": subject,
        "description": description,
        "status": "open",
        "is_escalation": True,
    }
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("tickets").insert(row).execute()
        )
        if not result.data:
            logger.error(
                "escalate: ticket insert returned no data for conversation %s",
                conversation_id,
            )
            return "Internal error during escalation. Try again or contact support."
        ticket_id = result.data[0]["id"]
    except Exception:
        logger.exception(
            "escalate: failed to insert ticket for conversation %s", conversation_id
        )
        return "Internal error during escalation. Try again or contact support."

    try:
        await asyncio.to_thread(
            lambda: supabase.table("conversations")
            .update({"status": "escalated"})
            .eq("id", str(conversation_id))
            .execute()
        )
    except Exception:
        logger.error(
            "escalate: ticket %s created but conversation %s status update failed",
            ticket_id,
            conversation_id,
        )
    return (
        f"Conversation escalated to a human operator. "
        f"Reason: {subject}. The team will contact you as soon as possible."
    )

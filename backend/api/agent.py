"""HTTP endpoint for the customer-facing AI chat.

In the MVP the tenant is resolved from the ``company_slug`` path parameter
(matched against the ``companies`` table).
"""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from agents.support_agent import SupportAgent
from database.models import AgentConfig
from database.supabase_client import get_supabase_client
from integrations.llm_interfaces.anthropic_interface import get_llm_client
from utils.config import get_settings
from utils.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Schemas ----------------------------------------------------------------


class ChatRequest(BaseModel):
    conversation_id: UUID | None = Field(
        default=None,
        description="UUID of an existing conversation. Pass null to start a new one.",
    )
    content: str = Field(min_length=1, description="The customer's message text.")


class ChatResponse(BaseModel):
    conversation_id: UUID
    reply: str


class ChatMessageOut(BaseModel):
    id: UUID
    role: str
    content: str


# --- Endpoint ---------------------------------------------------------------


@router.post(
    "/chat/{company_slug}/message",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit(lambda: get_settings().CHAT_RATE_LIMIT)
async def send_message(
    request: Request,
    company_slug: str,
    body: ChatRequest,
) -> ChatResponse:
    """Process one customer message and return the agent reply.

    - If ``conversation_id`` is null a new conversation is created.
    - The agent loads history, calls Claude (with tool-calling enabled),
      executes any requested tools and returns the final text reply.
    """
    supabase = get_supabase_client()
    settings = get_settings()

    # 1. Resolve company -------------------------------------------------------
    company_row = await asyncio.to_thread(
        lambda: supabase.table("companies")
        .select("id")
        .eq("slug", company_slug)
        .limit(1)
        .execute()
    )
    if not company_row.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company '{company_slug}' not found",
        )
    company_id = UUID(company_row.data[0]["id"])

    # 2. Load agent config -----------------------------------------------------
    cfg_row = await asyncio.to_thread(
        lambda: supabase.table("agent_configs")
        .select("*")
        .eq("company_id", str(company_id))
        .limit(1)
        .execute()
    )
    if not cfg_row.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent config not found for company '{company_slug}'",
        )
    agent_config = AgentConfig(**cfg_row.data[0])

    # 3. Create or reuse conversation ------------------------------------------
    if body.conversation_id is None:
        conv_row = await asyncio.to_thread(
            lambda: supabase.table("conversations")
            .insert({"company_id": str(company_id), "status": "active"})
            .execute()
        )
        conversation_id = UUID(conv_row.data[0]["id"])
        logger.info("New conversation %s for company %s", conversation_id, company_slug)
    else:
        conv_check = await asyncio.to_thread(
            lambda: supabase.table("conversations")
            .select("id")
            .eq("id", str(body.conversation_id))
            .eq("company_id", str(company_id))
            .limit(1)
            .execute()
        )
        if not conv_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        conversation_id = body.conversation_id

    # 4. Run the agent ---------------------------------------------------------
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ANTHROPIC_API_KEY is not configured",
        )

    llm = get_llm_client()
    agent = SupportAgent(
        company_id=company_id,
        agent_config=agent_config,
        llm=llm,
        supabase=supabase,
    )

    result = await agent.run(
        {"conversation_id": conversation_id, "content": body.content}
    )

    return ChatResponse(conversation_id=conversation_id, reply=result["reply"])


@router.get(
    "/chat/{company_slug}/conversation/{conversation_id}/messages",
    response_model=list[ChatMessageOut],
    status_code=status.HTTP_200_OK,
)
async def get_conversation_messages(
    company_slug: str,
    conversation_id: UUID,
) -> list[ChatMessageOut]:
    """Return the messages of an existing conversation.

    Public read-only endpoint used to restore chat history.
    ``conversation_id`` acts as a capability URL: whoever has it can read
    the conversation, consistent with the public nature of the ``/chat/*`` endpoints.
    """
    supabase = get_supabase_client()

    # 1. Resolve company -------------------------------------------------------
    company_row = await asyncio.to_thread(
        lambda: supabase.table("companies")
        .select("id")
        .eq("slug", company_slug)
        .limit(1)
        .execute()
    )
    if not company_row.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company '{company_slug}' not found",
        )
    company_id = UUID(company_row.data[0]["id"])

    # 2. Verify cross-tenant ownership ----------------------------------------
    conv_check = await asyncio.to_thread(
        lambda: supabase.table("conversations")
        .select("id")
        .eq("id", str(conversation_id))
        .eq("company_id", str(company_id))
        .limit(1)
        .execute()
    )
    if not conv_check.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # 3. Load messages (exclude system role, chronological order) --------------
    messages_row = await asyncio.to_thread(
        lambda: supabase.table("messages")
        .select("id, role, content")
        .eq("conversation_id", str(conversation_id))
        .neq("role", "system")
        .order("created_at")
        .execute()
    )

    return [ChatMessageOut(**row) for row in messages_row.data or []]

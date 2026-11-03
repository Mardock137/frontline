"""Public endpoint that returns branding and agent configuration for a company.

No authentication required: the page /chat/{slug} is publicly accessible.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from database.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Schema -----------------------------------------------------------------


class ChatConfig(BaseModel):
    agent_name: str
    company_display_name: str
    logo_url: str | None
    primary_color: str
    welcome_message: str


# --- Endpoint ---------------------------------------------------------------


@router.get(
    "/chat/{company_slug}/config",
    response_model=ChatConfig,
    status_code=status.HTTP_200_OK,
)
async def get_chat_config(company_slug: str) -> ChatConfig:
    """Return public branding and welcome message for the given company slug.

    Used by the frontend to initialise the chat page before the first message.
    """
    supabase = get_supabase_client()

    # 1. Resolve company -------------------------------------------------------
    company_row = (
        supabase.table("companies")
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
    company_id = company_row.data[0]["id"]

    # 2. Load agent config -----------------------------------------------------
    cfg_row = (
        supabase.table("agent_configs")
        .select("agent_name, company_display_name, logo_url, primary_color, welcome_message")
        .eq("company_id", company_id)
        .limit(1)
        .execute()
    )
    if not cfg_row.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent config not found for company '{company_slug}'",
        )

    row = cfg_row.data[0]
    logger.info("Config requested for company slug=%s", company_slug)
    return ChatConfig(**row)

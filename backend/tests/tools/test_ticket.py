"""Tests for tools/ticket.py (Supabase client mocked)."""

import pytest

from unittest.mock import MagicMock
from uuid import uuid4

from tools.ticket import TOOL_DEFINITION, create_ticket


def _make_supabase(ticket_id: str) -> MagicMock:
    supabase = MagicMock()
    supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[{"id": ticket_id}]
    )
    return supabase


@pytest.mark.asyncio
async def test_create_ticket_returns_ticket_id():
    ticket_id = str(uuid4())
    supabase = _make_supabase(ticket_id)

    result = await create_ticket(
        subject="Password reset issue",
        description="The reset link does not work.",
        company_id=uuid4(),
        conversation_id=uuid4(),
        supabase=supabase,
    )

    assert ticket_id in result


@pytest.mark.asyncio
async def test_create_ticket_inserts_correct_row():
    company_id = uuid4()
    conversation_id = uuid4()
    supabase = _make_supabase(str(uuid4()))

    await create_ticket(
        subject="Sub",
        description="Desc",
        company_id=company_id,
        conversation_id=conversation_id,
        supabase=supabase,
    )

    supabase.table.assert_called_with("tickets")
    call_args = supabase.table.return_value.insert.call_args[0][0]
    assert call_args["company_id"] == str(company_id)
    assert call_args["conversation_id"] == str(conversation_id)
    assert call_args["is_escalation"] is False
    assert call_args["status"] == "open"


@pytest.mark.asyncio
async def test_create_ticket_handles_missing_data():
    supabase = MagicMock()
    supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[]
    )

    result = await create_ticket(
        subject="Sub",
        description="Desc",
        company_id=uuid4(),
        conversation_id=uuid4(),
        supabase=supabase,
    )

    assert "unknown" in result


def test_tool_definition_schema():
    assert TOOL_DEFINITION["name"] == "create_ticket"
    props = TOOL_DEFINITION["input_schema"]["properties"]
    assert "subject" in props
    assert "description" in props
    assert set(TOOL_DEFINITION["input_schema"]["required"]) == {"subject", "description"}

"""Tests for tools/escalation.py (Supabase client mocked)."""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from tools.escalation import TOOL_DEFINITION, escalate


def _make_supabase() -> MagicMock:
    supabase = MagicMock()

    tickets_table = MagicMock()
    tickets_table.insert.return_value.execute.return_value = MagicMock(
        data=[{"id": str(uuid4())}]
    )

    conversations_table = MagicMock()
    conversations_table.update.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[]
    )

    def table_side_effect(name):
        if name == "tickets":
            return tickets_table
        if name == "conversations":
            return conversations_table
        return MagicMock()

    supabase.table.side_effect = table_side_effect
    return supabase


@pytest.mark.asyncio
async def test_escalate_inserts_ticket_with_is_escalation_true():
    company_id = uuid4()
    conversation_id = uuid4()
    supabase = _make_supabase()

    await escalate(
        subject="Critical issue",
        description="The system is down.",
        company_id=company_id,
        conversation_id=conversation_id,
        supabase=supabase,
    )

    insert_call_args = supabase.table("tickets").insert.call_args[0][0]
    assert insert_call_args["is_escalation"] is True
    assert insert_call_args["company_id"] == str(company_id)
    assert insert_call_args["conversation_id"] == str(conversation_id)


@pytest.mark.asyncio
async def test_escalate_updates_conversation_status():
    conversation_id = uuid4()
    supabase = _make_supabase()

    await escalate(
        subject="Urgent",
        description="Details.",
        company_id=uuid4(),
        conversation_id=conversation_id,
        supabase=supabase,
    )

    supabase.table("conversations").update.assert_called_with({"status": "escalated"})
    supabase.table("conversations").update.return_value.eq.assert_called_with(
        "id", str(conversation_id)
    )


@pytest.mark.asyncio
async def test_escalate_returns_confirmation_message():
    supabase = _make_supabase()

    result = await escalate(
        subject="Broken feature",
        description="Details.",
        company_id=uuid4(),
        conversation_id=uuid4(),
        supabase=supabase,
    )

    assert "escalated" in result.lower() or "operator" in result.lower()


@pytest.mark.asyncio
async def test_escalate_returns_error_string_when_ticket_insert_fails():
    supabase = _make_supabase()
    supabase.table("tickets").insert.return_value.execute.side_effect = RuntimeError(
        "db insert failed"
    )

    result = await escalate(
        subject="Broken feature",
        description="Details.",
        company_id=uuid4(),
        conversation_id=uuid4(),
        supabase=supabase,
    )

    assert "error" in result.lower()


@pytest.mark.asyncio
async def test_escalate_returns_confirmation_when_only_conversation_update_fails():
    supabase = _make_supabase()
    supabase.table("conversations").update.return_value.eq.return_value.execute.side_effect = RuntimeError(
        "db update failed"
    )

    result = await escalate(
        subject="Broken feature",
        description="Details.",
        company_id=uuid4(),
        conversation_id=uuid4(),
        supabase=supabase,
    )

    assert "escalated" in result.lower()


def test_tool_definition_schema():
    assert TOOL_DEFINITION["name"] == "escalate"
    props = TOOL_DEFINITION["input_schema"]["properties"]
    assert "subject" in props
    assert "description" in props
    assert set(TOOL_DEFINITION["input_schema"]["required"]) == {"subject", "description"}

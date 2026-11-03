"""Tests for the Pydantic database models."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from database.models import (
    AgentConfig,
    AgentConfigCreate,
    AgentTone,
    Company,
    CompanyCreate,
    ConversationCreate,
    ConversationStatus,
    DocumentCreate,
    DocumentStatus,
    MessageCreate,
    MessageRole,
    TicketCreate,
    TicketStatus,
)


# --- companies --------------------------------------------------------------


def test_company_create_requires_valid_slug():
    company = CompanyCreate(slug="acme-inc", name="Acme Inc.")
    assert company.slug == "acme-inc"
    assert company.name == "Acme Inc."


def test_company_create_rejects_invalid_slug():
    with pytest.raises(ValidationError):
        CompanyCreate(slug="Acme Inc!", name="Acme")


def test_company_output_parses_full_row():
    row = {
        "id": uuid4(),
        "slug": "acme",
        "name": "Acme",
        "created_at": datetime.now(timezone.utc),
    }
    assert Company(**row).slug == "acme"


# --- agent_configs ----------------------------------------------------------


def test_agent_config_defaults():
    cfg = AgentConfigCreate(company_id=uuid4(), company_display_name="Acme")
    assert cfg.agent_name == "Frontline"
    assert cfg.tone is AgentTone.FORMAL
    assert cfg.primary_color == "#000000"
    assert cfg.default_language == "en"


def test_agent_config_rejects_bad_tone():
    with pytest.raises(ValidationError):
        AgentConfigCreate(
            company_id=uuid4(),
            company_display_name="Acme",
            tone="shouty",
        )


def test_agent_config_rejects_bad_color():
    with pytest.raises(ValidationError):
        AgentConfigCreate(
            company_id=uuid4(),
            company_display_name="Acme",
            primary_color="red",
        )


def test_agent_config_accepts_hex_color():
    cfg = AgentConfigCreate(
        company_id=uuid4(),
        company_display_name="Acme",
        primary_color="#ff8800",
        tone=AgentTone.INFORMAL,
    )
    assert cfg.primary_color == "#ff8800"
    assert cfg.tone is AgentTone.INFORMAL


def test_agent_config_output_includes_id():
    cfg = AgentConfig(
        id=uuid4(),
        company_id=uuid4(),
        company_display_name="Acme",
        updated_at=datetime.now(timezone.utc),
    )
    assert cfg.agent_name == "Frontline"


# --- documents --------------------------------------------------------------


def test_document_create_defaults_status_to_pending():
    doc = DocumentCreate(
        company_id=uuid4(),
        filename="faq.pdf",
        storage_path="uuid/faq.pdf",
        content_type="application/pdf",
    )
    assert doc.status is DocumentStatus.PENDING


def test_document_rejects_unknown_status():
    with pytest.raises(ValidationError):
        DocumentCreate(
            company_id=uuid4(),
            filename="faq.pdf",
            storage_path="uuid/faq.pdf",
            content_type="application/pdf",
            status="weird",
        )


# --- conversations / messages ----------------------------------------------


def test_conversation_default_status_active():
    conv = ConversationCreate(company_id=uuid4())
    assert conv.status is ConversationStatus.ACTIVE


def test_message_requires_known_role():
    msg = MessageCreate(
        conversation_id=uuid4(),
        role=MessageRole.CUSTOMER,
        content="Hello",
    )
    assert msg.role is MessageRole.CUSTOMER

    with pytest.raises(ValidationError):
        MessageCreate(conversation_id=uuid4(), role="robot", content="x")


def test_message_content_cannot_be_empty():
    with pytest.raises(ValidationError):
        MessageCreate(
            conversation_id=uuid4(),
            role=MessageRole.AGENT,
            content="",
        )


# --- tickets ----------------------------------------------------------------


def test_ticket_default_status_open():
    ticket = TicketCreate(
        company_id=uuid4(),
        conversation_id=uuid4(),
        subject="Refund",
        description="Customer asks for a refund",
    )
    assert ticket.status is TicketStatus.OPEN


def test_ticket_rejects_bad_status():
    with pytest.raises(ValidationError):
        TicketCreate(
            company_id=uuid4(),
            conversation_id=uuid4(),
            subject="x",
            description="y",
            status="done",
        )

"""Pydantic models mirroring the Supabase database tables.

For each table we expose two classes where useful:
- ``<Entity>Create``: input shape when inserting a new row (no server-side
  defaults like ``id``/``created_at``).
- ``<Entity>``: output shape as read from the database (all fields populated).
"""

from datetime import datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class _DbModel(BaseModel):
    """Base class for DB models (shared configuration)."""

    model_config = ConfigDict(from_attributes=True, extra="ignore")


# --- Enums ------------------------------------------------------------------


class AgentTone(StrEnum):
    FORMAL = "formal"
    INFORMAL = "informal"


class DocumentStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class ConversationStatus(StrEnum):
    ACTIVE = "active"
    CLOSED = "closed"
    ESCALATED = "escalated"


class MessageRole(StrEnum):
    CUSTOMER = "customer"
    AGENT = "agent"
    SYSTEM = "system"


class TicketStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


# --- companies --------------------------------------------------------------


Slug = Annotated[str, Field(min_length=1, max_length=64, pattern=r"^[a-z0-9-]+$")]


class CompanyCreate(_DbModel):
    slug: Slug
    name: str = Field(min_length=1)


class Company(CompanyCreate):
    id: UUID
    created_at: datetime


# --- agent_configs ----------------------------------------------------------


HexColor = Annotated[str, Field(pattern=r"^#[0-9a-fA-F]{6}$")]


class AgentConfigCreate(_DbModel):
    company_id: UUID
    agent_name: str = "Frontline"
    company_display_name: str = Field(min_length=1)
    logo_url: str | None = None
    primary_color: HexColor = "#000000"
    tone: AgentTone = AgentTone.FORMAL
    default_language: str = Field(default="en", min_length=2, max_length=8)
    welcome_message: str = "Hi! How can I help you today?"


class AgentConfig(AgentConfigCreate):
    id: UUID
    updated_at: datetime


# --- documents --------------------------------------------------------------


class DocumentCreate(_DbModel):
    company_id: UUID
    filename: str = Field(min_length=1)
    storage_path: str = Field(min_length=1)
    content_type: str = Field(min_length=1)
    status: DocumentStatus = DocumentStatus.PENDING


class Document(DocumentCreate):
    id: UUID
    created_at: datetime


# --- document_chunks --------------------------------------------------------


class DocumentChunkCreate(_DbModel):
    document_id: UUID
    company_id: UUID
    chunk_index: int = Field(ge=0)
    content: str = Field(min_length=1)
    embedding: list[float]


class DocumentChunk(DocumentChunkCreate):
    id: UUID
    created_at: datetime


# --- conversations ----------------------------------------------------------


class ConversationCreate(_DbModel):
    company_id: UUID
    status: ConversationStatus = ConversationStatus.ACTIVE


class Conversation(ConversationCreate):
    id: UUID
    started_at: datetime


# --- messages ---------------------------------------------------------------


class MessageCreate(_DbModel):
    conversation_id: UUID
    role: MessageRole
    content: str = Field(min_length=1)


class Message(MessageCreate):
    id: UUID
    created_at: datetime


# --- tickets ----------------------------------------------------------------


class TicketCreate(_DbModel):
    company_id: UUID
    conversation_id: UUID
    subject: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: TicketStatus = TicketStatus.OPEN
    is_escalation: bool = False


class Ticket(TicketCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime


__all__ = [
    "AgentTone",
    "DocumentStatus",
    "ConversationStatus",
    "MessageRole",
    "TicketStatus",
    "CompanyCreate",
    "Company",
    "AgentConfigCreate",
    "AgentConfig",
    "DocumentCreate",
    "Document",
    "DocumentChunkCreate",
    "DocumentChunk",
    "ConversationCreate",
    "Conversation",
    "MessageCreate",
    "Message",
    "TicketCreate",
    "Ticket",
]

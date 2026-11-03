-- Migration 007: messages
-- Individual messages belonging to a conversation.

create table if not exists frontline.messages (
    id uuid primary key default gen_random_uuid(),
    conversation_id uuid not null references frontline.conversations (id) on delete cascade,
    role text not null check (role in ('customer', 'agent', 'system')),
    content text not null,
    created_at timestamptz not null default now()
);

create index if not exists messages_conversation_id_idx on frontline.messages (conversation_id);

alter table frontline.messages enable row level security;

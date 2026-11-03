-- Migration 008: tickets
-- Tickets opened by the agent for cases that cannot be resolved autonomously
-- or that require escalation to the company's human referent.

create table if not exists frontline.tickets (
    id uuid primary key default gen_random_uuid(),
    company_id uuid not null references frontline.companies (id) on delete cascade,
    conversation_id uuid not null references frontline.conversations (id) on delete cascade,
    subject text not null,
    description text not null,
    status text not null default 'open'
        check (status in ('open', 'in_progress', 'closed')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create trigger trg_tickets_updated_at
    before update on frontline.tickets
    for each row execute function frontline.set_updated_at();

create index if not exists tickets_company_id_idx on frontline.tickets (company_id);
create index if not exists tickets_conversation_id_idx on frontline.tickets (conversation_id);
create index if not exists tickets_status_idx on frontline.tickets (status);

alter table frontline.tickets enable row level security;

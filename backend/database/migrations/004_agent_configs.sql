-- Migration 004: agent_configs
-- Per-company configuration of the AI agent (branding, tone, welcome).

create table if not exists frontline.agent_configs (
    id uuid primary key default gen_random_uuid(),
    company_id uuid not null unique references frontline.companies (id) on delete cascade,
    agent_name text not null default 'Frontline',
    company_display_name text not null,
    logo_url text,
    primary_color text not null default '#000000',
    tone text not null default 'formal' check (tone in ('formal', 'informal')),
    default_language text not null default 'en',
    welcome_message text not null default 'Hi! How can I help you today?',
    updated_at timestamptz not null default now()
);

create or replace function frontline.set_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

create trigger trg_agent_configs_updated_at
    before update on frontline.agent_configs
    for each row execute function frontline.set_updated_at();

alter table frontline.agent_configs enable row level security;

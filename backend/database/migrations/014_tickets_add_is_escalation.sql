-- Migration 014: add is_escalation column to tickets
-- Distinguishes tickets opened for unresolvable cases (is_escalation = false)
-- from those created by the agent when handing off to a human operator
-- (is_escalation = true).

alter table frontline.tickets
    add column if not exists is_escalation boolean not null default false;

create index if not exists tickets_is_escalation_idx on frontline.tickets (is_escalation);

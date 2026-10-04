create extension if not exists "pgcrypto";

create table if not exists public.profiles (
    id uuid primary key default gen_random_uuid(),
    google_sub text unique not null,
    email text unique not null,
    full_name text not null default '',
    avatar_url text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.tasks (
    id uuid primary key default gen_random_uuid(),
    title text not null check (char_length(trim(title)) between 1 and 200),
    description text not null default '',
    created_by uuid not null references public.profiles(id) on delete cascade,
    assigned_to uuid not null references public.profiles(id) on delete restrict,
    completed boolean not null default false,
    completed_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_tasks_created_by on public.tasks(created_by);
create index if not exists idx_tasks_assigned_to on public.tasks(assigned_to);
create index if not exists idx_tasks_completed on public.tasks(completed);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists profiles_updated_at on public.profiles;
create trigger profiles_updated_at
before update on public.profiles
for each row execute function public.set_updated_at();

drop trigger if exists tasks_updated_at on public.tasks;
create trigger tasks_updated_at
before update on public.tasks
for each row execute function public.set_updated_at();

alter table public.profiles enable row level security;
alter table public.tasks enable row level security;
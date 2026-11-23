-- Supabase Migration: Initial schema for CivicAssist Phase 02
-- Created: 2023-11-23 (timestamp placeholder)

-- Enable pgcrypto extension for UUID generation
create extension if not exists "pgcrypto";

-- Trigger function to create profile for new auth users
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer as $$
begin
  insert into public.profiles (
    id,
    name,
    phone,
    role,
    department_id,
    created_at
  ) values (
    new.id,
    coalesce(new.raw_user_meta_data->>'full_name', ''),
    coalesce(new.raw_user_meta_data->>'phone', ''),
    'citizen',
    null,
    now()
  );
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- 1. Profiles table (connected to Supabase Auth)
create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    name text,
    phone text,
    role text not null check (role in ('citizen','department','admin')),
    department_id uuid references public.departments(id) on delete set null,
    created_at timestamptz default now()
);

-- 2. Departments table
create table if not exists public.departments (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    helpline text,
    email text,
    sla_hours integer,
    created_at timestamptz default now()
);

-- 3. Complaints table
create sequence if not exists public.complaint_number_seq start 1 increment 1;

create table if not exists public.complaints (
    id uuid primary key default gen_random_uuid(),
    complaint_number text not null default 'CMP-' || lpad(nextval('public.complaint_number_seq')::text,6,'0'),
    citizen_id uuid not null references public.profiles(id) on delete restrict,
    description text,
    source text not null check (source in ('website','email')),
    latitude decimal,
    longitude decimal,
    address text,
    predicted_department_id uuid references public.departments(id) on delete set null,
    prediction_confidence decimal,
    assigned_department_id uuid references public.departments(id) on delete set null,
    priority text not null check (priority in ('low','medium','high','critical')),
    priority_score decimal,
    similar_count integer default 0,
    cluster_id uuid references public.complaint_clusters(id) on delete set null,
    status text not null check (status in ('submitted','ai_classified','assigned','acknowledged','in_progress','resolution_submitted','verification','resolved','rejected','reassigned')),
    deadline timestamptz,
    citizen_image_path text,
    resolution_image_path text,
    resolution_notes text,
    created_at timestamptz default now(),
    updated_at timestamptz default now(),
    resolved_at timestamptz
);

-- 4. Complaint History table
create table if not exists public.complaint_history (
    id uuid primary key default gen_random_uuid(),
    complaint_id uuid not null references public.complaints(id) on delete cascade,
    status text not null,
    message text,
    changed_by uuid references public.profiles(id) on delete set null,
    created_at timestamptz default now()
);

-- 5. Notifications table
create table if not exists public.notifications (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.profiles(id) on delete cascade,
    complaint_id uuid references public.complaints(id) on delete set null,
    title text,
    message text,
    is_read boolean default false,
    created_at timestamptz default now()
);

-- 6. Complaint Clusters table
create table if not exists public.complaint_clusters (
    id uuid primary key default gen_random_uuid(),
    title text,
    department_id uuid not null references public.departments(id) on delete restrict,
    complaint_count integer default 0,
    priority text check (priority in ('low','medium','high','critical')),
    latitude decimal,
    longitude decimal,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

-- 7. Email Messages table
create table if not exists public.email_messages (
    id uuid primary key default gen_random_uuid(),
    message_id text not null unique,
    sender_email text,
    subject text,
    body text,
    complaint_id uuid references public.complaints(id) on delete set null,
    received_at timestamptz default now()
);

-- Indexes
create index if not exists idx_complaints_citizen_id on public.complaints(citizen_id);
create index if not exists idx_complaints_assigned_department_id on public.complaints(assigned_department_id);
create index if not exists idx_complaints_predicted_department_id on public.complaints(predicted_department_id);
create index if not exists idx_complaints_status on public.complaints(status);
create index if not exists idx_complaints_priority on public.complaints(priority);
create index if not exists idx_complaints_cluster_id on public.complaints(cluster_id);
create index if not exists idx_complaints_created_at on public.complaints(created_at);
create index if not exists idx_complaints_deadline on public.complaints(deadline);

create index if not exists idx_complaint_history_complaint_id on public.complaint_history(complaint_id);

create index if not exists idx_notifications_user_id on public.notifications(user_id);
create index if not exists idx_notifications_is_read on public.notifications(is_read);

create index if not exists idx_email_messages_message_id on public.email_messages(message_id);

create index if not exists idx_profiles_role on public.profiles(role);
create index if not exists idx_profiles_department_id on public.profiles(department_id);

-- Row Level Security
alter table public.profiles enable row level security;
alter table public.departments enable row level security;
alter table public.complaints enable row level security;
alter table public.complaint_history enable row level security;
alter table public.notifications enable row level security;
alter table public.complaint_clusters enable row level security;
alter table public.email_messages enable row level security;

-- RLS Policies (simplified placeholders, to be refined later)
-- Citizens can select their own profile and related data
create policy "citizen_select_own_profile" on public.profiles for select using (auth.uid() = id);
create policy "citizen_insert_profile" on public.profiles for insert with check (auth.uid() = id);

-- Citizens can insert and select their own complaints and history
create policy "citizen_complaint_insert" on public.complaints for insert with check (auth.uid() = citizen_id);
create policy "citizen_complaint_select" on public.complaints for select using (auth.uid() = citizen_id);
create policy "citizen_history_select" on public.complaint_history for select using (auth.uid() = changed_by);
create policy "citizen_notification_select" on public.notifications for select using (auth.uid() = user_id);

-- Departments can select complaints assigned to their department
create policy "dept_complaint_select" on public.complaints for select using (assigned_department_id = (select department_id from public.profiles where id = auth.uid()));
create policy "dept_complaint_update" on public.complaints for update using (assigned_department_id = (select department_id from public.profiles where id = auth.uid()));
create policy "dept_history_select" on public.complaint_history for select using (complaint_id in (select id from public.complaints where assigned_department_id = (select department_id from public.profiles where id = auth.uid())));
create policy "dept_notification_select" on public.notifications for select using (user_id = auth.uid());

-- Admins have full access (using role = 'admin')
create policy "admin_full_access" on public.profiles for all using (exists (select 1 from auth.users where id = auth.uid() and (select role from public.profiles where id = auth.uid()) = 'admin'));
create policy "admin_full_access_all" on public.departments for all using (exists (select 1 from public.profiles where id = auth.uid() and role = 'admin'));
create policy "admin_full_access_complaints" on public.complaints for all using (exists (select 1 from public.profiles where id = auth.uid() and role = 'admin'));
create policy "admin_full_access_history" on public.complaint_history for all using (exists (select 1 from public.profiles where id = auth.uid() and role = 'admin'));
create policy "admin_full_access_notifications" on public.notifications for all using (exists (select 1 from public.profiles where id = auth.uid() and role = 'admin'));
create policy "admin_full_access_clusters" on public.complaint_clusters for all using (exists (select 1 from public.profiles where id = auth.uid() and role = 'admin'));
create policy "admin_full_access_email" on public.email_messages for all using (exists (select 1 from public.profiles where id = auth.uid() and role = 'admin'));

-- Note: Supabase storage bucket creation is performed via CLI, not SQL.

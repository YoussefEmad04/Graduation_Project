-- Student-scoped chat sessions for ChatGPT/Claude-style recents.
-- Apply this in Supabase before deploying the updated API.

alter table sessions add column if not exists student_id text;
alter table sessions add column if not exists title text;
alter table sessions add column if not exists updated_at timestamptz default now();

alter table messages add column if not exists student_id text;

create unique index if not exists idx_sessions_student_session_unique
  on sessions (student_id, session_id);

create index if not exists idx_sessions_student_updated
  on sessions (student_id, updated_at desc);

create index if not exists idx_messages_student_session_created
  on messages (student_id, session_id, created_at);

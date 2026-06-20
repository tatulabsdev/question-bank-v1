-- Run this once in Supabase: Dashboard -> SQL Editor -> New query -> paste -> Run
-- Matches the fields produced by pipeline.py's to_final_record() exactly.

create table if not exists questions (
  id text primary key,
  created timestamptz default now(),
  topic_id text not null,
  subject text,
  chapter text,
  topic text,
  level int,
  tier text,
  question_en text,
  options_en jsonb,
  correct_answer int,
  explanation jsonb,
  diagram_required boolean default false,
  diagram jsonb,
  exam_mapping jsonb,
  exam_tags jsonb,
  verified boolean default true,
  quality_score numeric,
  copyright_original boolean default true,
  translations jsonb default '{}'::jsonb
);

-- Speeds up the quota_tracker's per-topic-per-level count checks, which
-- run before every generation job.
create index if not exists idx_questions_topic_level on questions (topic_id, level);

-- Row Level Security is on by default for new Supabase projects. The
-- pipeline writes with the SERVICE ROLE key (not the anon/public key),
-- which bypasses RLS automatically — so no policy is required for the
-- pipeline itself to work. If you also want your TryIT app's frontend to
-- READ questions using the public anon key, uncomment and adjust this:

-- alter table questions enable row level security;
-- create policy "Public read access" on questions
--   for select using (true);

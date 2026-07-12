-- TryIT Question Engine — FULL FRESH SCHEMA
-- Run this once in your NEW Supabase project: Dashboard -> SQL Editor ->
-- New query -> paste this whole file -> Run.
--
-- Covers all 3 tables the codebase touches:
--   subjects  — written once by seed_subjects.py, read by pipeline.py
--   topics    — written once by seed_topics.py, read by quota_tracker.py
--               and pipeline.py; questions_available is meant to be kept
--               current by a trigger (see bottom) or a periodic job —
--               nothing in the current codebase updates it automatically
--   questions — written continuously by pipeline.py

-- ──────────────────────────────────────────────────────────
-- SUBJECTS
-- ──────────────────────────────────────────────────────────
create table if not exists subjects (
  subject_id    text primary key,
  subject_name  text not null,
  parent_id     text references subjects(subject_id),
  stream        text  -- "general" | "science" | "arts" | "commerce" | "law" | "professional" | "language"
);

-- ──────────────────────────────────────────────────────────
-- TOPICS
-- ──────────────────────────────────────────────────────────
create table if not exists topics (
  topic_id            text primary key,
  subject_id          text references subjects(subject_id),
  topic_name          text not null,
  topic_name_hi       text,
  topic_name_ta       text,
  parent_topic_id     text references topics(topic_id),
  difficulty_range    text,        -- e.g. "2-7", parsed by config.levels_from_difficulty_range
  is_visual           boolean default false,
  coverage_score      int,         -- higher = processed earlier by quota_tracker
  question_target     int default 0,
  questions_available int default 0,
  display_order       int
);

create index if not exists idx_topics_coverage on topics (coverage_score desc);
create index if not exists idx_topics_subject on topics (subject_id);

-- ──────────────────────────────────────────────────────────
-- QUESTIONS
-- ──────────────────────────────────────────────────────────
create table if not exists questions (
  id                  text primary key,
  topic_id            text references topics(topic_id),
  subject_id          text references subjects(subject_id),
  level               int,
  difficulty          text,        -- "Easy" | "Medium" | "Hard" | "Expert"
  pattern_type        text,        -- e.g. "standalone_mcq4"
  question_en         text,
  options_en          jsonb,
  correct_answer      int,
  explanation          jsonb,       -- the 7-layer explanation object
  translations        jsonb default '{}'::jsonb,
  exam_tags           jsonb default '[]'::jsonb,
  has_visual          boolean default false,
  visual_type         text,        -- diagram_kind, e.g. "geometry_svg"
  visual_data         jsonb,
  access_tier         text,        -- "free" | "pro"
  copyright_original  boolean default true,
  verified            boolean default true,
  quality_score       numeric,
  report_count        int default 0,
  generated_by        text,        -- e.g. "tryit_engine:call_cerebras"
  created_at          timestamptz default now()
);

create index if not exists idx_questions_topic_level on questions (topic_id, level);
create index if not exists idx_questions_access_tier on questions (access_tier);
create index if not exists idx_questions_exam_tags on questions using gin (exam_tags);

-- ──────────────────────────────────────────────────────────
-- KEEP topics.questions_available IN SYNC AUTOMATICALLY
-- Nothing in pipeline.py currently increments this — quota_tracker.py
-- assumes it's "auto-maintained by the database" (per its own docstring)
-- but no trigger existed anywhere in the codebase to actually do that.
-- Without this, questions_available stays 0 forever and quota_tracker
-- will think every topic needs its FULL target generated, every single
-- run, forever — massively over-generating. This trigger is required,
-- not optional, for quota_tracker.py's logic to mean what it assumes.
-- ──────────────────────────────────────────────────────────
create or replace function increment_topic_question_count()
returns trigger as $$
begin
  update topics
  set questions_available = questions_available + 1
  where topic_id = new.topic_id;
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_increment_topic_question_count on questions;
create trigger trg_increment_topic_question_count
  after insert on questions
  for each row
  execute function increment_topic_question_count();

-- Row Level Security is on by default for new Supabase projects. The
-- pipeline writes with the SERVICE ROLE key (not the anon/public key),
-- which bypasses RLS automatically — so no policy is required for the
-- pipeline itself to work. If you also want your TryIT app's frontend to
-- READ these tables using the public anon key, uncomment and adjust:

-- alter table subjects enable row level security;
-- alter table topics enable row level security;
-- alter table questions enable row level security;
-- create policy "Public read access" on subjects for select using (true);
-- create policy "Public read access" on topics for select using (true);
-- create policy "Public read access" on questions for select using (true);

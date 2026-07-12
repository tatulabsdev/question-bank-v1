#!/usr/bin/env bash
# Run this from the ROOT of your question-bank-v1 repo in the Codespaces terminal:
#   bash apply_fixes_round2.sh
# Writes/overwrites: schema.sql (now covers subjects+topics+questions
# plus the missing questions_available trigger), seed_subjects.py (new).
set -e

cat > schema.sql << 'TRYIT_EOF'
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
TRYIT_EOF
echo "wrote schema.sql"

cat > seed_subjects.py << 'TRYIT_EOF'

"""
TryIT Question Engine — Subject Seeder
==========================================
Populates the `subjects` table. This table was previously never created
or populated anywhere in the codebase, even though supabase_data.py reads
from it and pipeline.py calls fetch_subjects() on every single run — on
a fresh Supabase project this would crash the pipeline immediately with
a 404/"relation does not exist" error before a single question got
generated.

Two kinds of rows:
  1. Four UMBRELLA PARENTS (maths, english, reasoning, general_knowledge)
     — display-grouping only, per seed_topics.py's own docstring
     ("Only LEAF subjects get topics ... umbrella parents for display
     grouping"). These have parent_id = None.
  2. The 40 LEAF subjects that seed_topics.py's SUBJECT_TOPICS actually
     attaches topics to. Each leaf's parent_id points at one of the 4
     umbrellas where applicable, or stays None for standalone leaves
     (physics, chemistry, history, accountancy, etc. — these don't
     nest under any umbrella today).

ASSUMPTION — `stream` grouping (general/science/arts/commerce/law/
professional/language) is not defined anywhere else in the codebase, so
this is a first-pass default grouping for filtering/display purposes.
Confirm/adjust these against your own product taxonomy before treating
them as final — they don't affect question generation itself (only
questions.subject_id / topics.subject_id do that), just how subjects
might get grouped in a UI.
"""

import os
import requests

REQUEST_TIMEOUT = 30

# ──────────────────────────────────────────────────────────
# UMBRELLA PARENTS — display grouping only, no topics attach directly
# ──────────────────────────────────────────────────────────
UMBRELLA_PARENTS = {
    "maths":             ("Mathematics", "general"),
    "english":           ("English", "general"),
    "reasoning":         ("Reasoning", "general"),
    "general_knowledge": ("General Knowledge", "general"),
}

# ──────────────────────────────────────────────────────────
# LEAF SUBJECTS — subject_id -> (subject_name, parent_id_or_None, stream)
# subject_id values match SUBJECT_TOPICS keys in seed_topics.py exactly —
# this list is NOT auto-derived from there on purpose, so a change to
# seed_topics.py doesn't silently rename/reparent a subject in prod
# without a deliberate matching edit here.
# ──────────────────────────────────────────────────────────
LEAF_SUBJECTS = {
    "maths_arithmetic":   ("Arithmetic", "maths", "general"),
    "maths_algebra":      ("Algebra", "maths", "general"),
    "maths_geometry":     ("Geometry", "maths", "general"),
    "maths_trigonometry": ("Trigonometry", "maths", "general"),
    "maths_stats":        ("Statistics", "maths", "general"),
    "data_interpretation":("Data Interpretation", "maths", "general"),
    "maths_calculus":     ("Calculus", "maths", "science"),

    "reasoning_verbal":    ("Verbal Reasoning", "reasoning", "general"),
    "reasoning_nonverbal": ("Non-Verbal Reasoning", "reasoning", "general"),
    "reasoning_critical":  ("Critical Reasoning", "reasoning", "general"),

    "english_grammar": ("English Grammar", "english", "general"),
    "english_vocab":   ("English Vocabulary", "english", "general"),
    "english_reading": ("English Reading Comprehension", "english", "general"),
    "english_writing": ("English Writing", "english", "general"),

    "gk_history":      ("History (GK)", "general_knowledge", "general"),
    "gk_polity":       ("Polity (GK)", "general_knowledge", "general"),
    "gk_geography":    ("Geography (GK)", "general_knowledge", "general"),
    "gk_economy":      ("Economy (GK)", "general_knowledge", "general"),
    "gk_science":      ("Science (GK)", "general_knowledge", "general"),
    "gk_sports":       ("Sports (GK)", "general_knowledge", "general"),
    "gk_awards":       ("Awards and Honours (GK)", "general_knowledge", "general"),
    "gk_india":        ("India Static GK", "general_knowledge", "general"),
    "current_affairs": ("Current Affairs", "general_knowledge", "general"),

    "physics":    ("Physics", None, "science"),
    "chemistry":  ("Chemistry", None, "science"),
    "biology":    ("Biology", None, "science"),
    "science_gen":("General Science", None, "science"),
    "computer":   ("Computer Science", None, "science"),
    "environment":("Environmental Science", None, "science"),

    "history":   ("History (Detailed)", None, "arts"),
    "geography": ("Geography (Detailed)", None, "arts"),
    "polity":    ("Polity (Detailed)", None, "arts"),
    "economy":   ("Economy (Detailed)", None, "arts"),

    "accountancy":     ("Accountancy", None, "commerce"),
    "management_sub":  ("Management", None, "commerce"),
    "law_sub":         ("Law", None, "law"),
    "agriculture_sub": ("Agriculture", None, "professional"),
    "engineering_sub": ("Engineering", None, "professional"),
    "hindi":           ("Hindi", None, "language"),
    "regional_lang":   ("Regional Languages", None, "language"),
}


def build_subject_rows():
    rows = []
    for subject_id, (name, stream) in UMBRELLA_PARENTS.items():
        rows.append({
            "subject_id": subject_id,
            "subject_name": name,
            "parent_id": None,
            "stream": stream,
        })
    for subject_id, (name, parent_id, stream) in LEAF_SUBJECTS.items():
        rows.append({
            "subject_id": subject_id,
            "subject_name": name,
            "parent_id": parent_id,
            "stream": stream,
        })
    return rows


def push_subjects(rows, batch_size=50):
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()
    if not url or not key:
        print("SUPABASE_URL/SUPABASE_KEY not set — nothing pushed")
        return 0

    saved = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        r = requests.post(
            f"{url}/rest/v1/subjects",
            headers={"apikey": key, "Authorization": f"Bearer {key}",
                     "Content-Type": "application/json", "Prefer": "return=minimal"},
            json=batch, timeout=REQUEST_TIMEOUT,
        )
        if r.status_code in (200, 201):
            saved += len(batch)
        else:
            print(f"  error {r.status_code}: {r.text[:200]}")
    return saved


if __name__ == "__main__":
    rows = build_subject_rows()
    print(f"Built {len(rows)} subjects "
          f"({len(UMBRELLA_PARENTS)} umbrella parents + {len(LEAF_SUBJECTS)} leaves)")
    saved = push_subjects(rows)
    print(f"Pushed {saved}/{len(rows)} to Supabase")
TRYIT_EOF
echo "wrote seed_subjects.py"

echo "Done. Run: python3 -m py_compile seed_subjects.py"

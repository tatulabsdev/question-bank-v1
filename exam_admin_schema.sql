-- TRYIT EXAM ADMIN — EXTENDED SCHEMA
-- Run this in Supabase SQL Editor AFTER the main schema.sql has run.
-- Adds: exam_tiers, exam_sections, exam_syllabus_map tables, and
-- extends exam_registry with detail columns the admin panel needs.
-- Safe to re-run (all statements are CREATE IF NOT EXISTS / ADD COLUMN IF NOT EXISTS).

-- ── 1. EXTEND exam_registry with detail columns ────────────────────────────
alter table exam_registry
  add column if not exists difficulty_score    int check (difficulty_score between 1 and 10),
  add column if not exists official_url        text,
  add column if not exists application_fee_gen int,   -- general category fee in rupees
  add column if not exists syllabus_notes      text,
  add column if not exists is_active           boolean default true;

-- ── 2. EXAM TIERS ─────────────────────────────────────────────────────────
-- One row per stage (Prelims, Mains, Tier 1, Paper 1, Phase 1, etc.)
create table if not exists exam_tiers (
  tier_id               text primary key,  -- e.g. "ssc_cgl_tier1"
  exam_id               text references exam_registry(exam_id) on delete cascade,
  tier_name             text not null,     -- "Prelims", "Tier 2", "Phase 1"
  tier_order            int  not null default 1,
  is_qualifying         boolean default false,   -- true = gate only, not merit
  total_questions       int,
  total_marks           int,
  duration_minutes      int,
  negative_marking_rate numeric,           -- e.g. 0.25, 0.333, 1.0; null = none
  mode                  text,              -- "online_cbt" | "offline_omr" | "descriptive" | "hybrid"
  notes                 text,
  created_at            timestamptz default now()
);

create index if not exists idx_tiers_exam on exam_tiers(exam_id, tier_order);

-- ── 3. EXAM SECTIONS ──────────────────────────────────────────────────────
-- One row per section within a tier (Reasoning, Quant, English, GA, etc.)
create table if not exists exam_sections (
  section_id                 text primary key,  -- e.g. "ssc_cgl_tier1_reasoning"
  tier_id                    text references exam_tiers(tier_id) on delete cascade,
  section_name               text not null,
  section_order              int  default 1,
  num_questions              int,
  marks_per_question         numeric default 1,
  total_marks                int,
  time_minutes               int,              -- null = no per-section timer
  negative_marking_override  numeric,          -- null = inherits tier's rate
  subject_group              text,             -- "quant"|"reasoning"|"english"|"gk"|"di"|"technical"|"computer"|"language"
  notes                      text
);

create index if not exists idx_sections_tier on exam_sections(tier_id, section_order);

-- ── 4. EXAM SYLLABUS MAP ──────────────────────────────────────────────────
-- Maps specific topics from the topics table onto exam sections,
-- with weightage %. This is what drives the question_target rebalancing
-- engine (topic_exam_weightage.py) once it's populated.
create table if not exists exam_syllabus_map (
  map_id            text primary key,  -- auto-generated
  exam_id           text references exam_registry(exam_id) on delete cascade,
  section_id        text references exam_sections(section_id) on delete cascade,
  topic_id          text references topics(topic_id),
  weightage_percent numeric,    -- what % of the section's marks this topic covers
  priority          int default 3 check (priority between 1 and 5),
                                -- 1=must-know, 5=bonus/rare
  notes             text
);

create index if not exists idx_syllabus_exam    on exam_syllabus_map(exam_id);
create index if not exists idx_syllabus_section on exam_syllabus_map(section_id);
create index if not exists idx_syllabus_topic   on exam_syllabus_map(topic_id);

-- ── 5. USEFUL VIEW ────────────────────────────────────────────────────────
-- Admin panel uses this to show a flat, readable breakdown of every
-- exam → tier → section in one query.
create or replace view exam_full_structure as
  select
    r.exam_id,
    r.exam_name,
    r.category,
    r.research_status,
    r.is_active,
    t.tier_id,
    t.tier_name,
    t.tier_order,
    t.is_qualifying,
    t.total_questions  as tier_total_q,
    t.total_marks      as tier_total_marks,
    t.duration_minutes as tier_duration,
    t.negative_marking_rate as tier_neg_marking,
    t.mode             as tier_mode,
    s.section_id,
    s.section_name,
    s.section_order,
    s.num_questions    as section_q,
    s.marks_per_question,
    s.total_marks      as section_marks,
    s.time_minutes     as section_time,
    s.negative_marking_override,
    s.subject_group
  from exam_registry r
  left join exam_tiers    t on t.exam_id    = r.exam_id
  left join exam_sections s on s.tier_id    = t.tier_id
  order by r.exam_name, t.tier_order, s.section_order;

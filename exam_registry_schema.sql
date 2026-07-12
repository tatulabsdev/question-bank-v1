-- TRYIT EXAM REGISTRY
-- Purpose: track EVERY exam TryIT should eventually cover, its research
-- status, and — critically — WHEN it needs re-checking. This is what
-- turns "research all exams" from an impossible one-time claim into a
-- sustainable, never-drops-anything process.
--
-- Run this in Supabase SQL Editor alongside your existing schema.

create table if not exists exam_registry (
  exam_id             text primary key,       -- e.g. "ib_acio", "ssc_cgl", "cbi_si_via_ssc_cgl"
  exam_name           text not null,
  conducting_body     text,
  category            text,                   -- see CATEGORY VALUES below
  qualification_level text,                   -- '10th' | '12th' | 'graduate' | 'pg' | 'phd' | 'any'

  -- FREQUENCY: this is the field that prevents irregular exams (IB ACIO,
  -- CBI-linked posts, sports-quota-adjacent recruitment, one-off state
  -- notifications) from silently falling off the radar.
  frequency_type      text,                   -- 'annual' | 'biannual' | 'irregular_vacancy_driven' |
                                               -- 'every_2_3_years' | 'one_time_notification' | 'ongoing_rolling'

  research_status     text default 'not_started',
                                               -- 'deep_dived' (marks/pattern/weightage confirmed) |
                                               -- 'pass1_mapped_only' (named+scoped, no weightage yet) |
                                               -- 'not_started' |
                                               -- 'not_applicable' (e.g. sports quota — no MCQ content needed)

  source_file         text,                   -- which .md file has the research, if any
  last_researched_on  date,
  next_recheck_due    date,                   -- NULL for one-time/stable exams; set for irregular ones
  notes                text
);

create index if not exists idx_registry_status on exam_registry (research_status);
create index if not exists idx_registry_recheck on exam_registry (next_recheck_due);

-- ──────────────────────────────────────────────────────────
-- THE QUERY THAT MATTERS: run this periodically (e.g. monthly) to see
-- what needs attention. This is the actual mechanism that keeps the
-- "nothing left, forever" promise honest and operational.
-- ──────────────────────────────────────────────────────────
-- select exam_id, exam_name, research_status, next_recheck_due
-- from exam_registry
-- where research_status in ('not_started', 'pass1_mapped_only')
--    or (next_recheck_due is not null and next_recheck_due <= current_date)
-- order by
--   case research_status when 'not_started' then 0 when 'pass1_mapped_only' then 1 else 2 end,
--   next_recheck_due nulls last;

-- CATEGORY VALUES (for consistency): central_govt, state_govt, banking,
-- defence_paramilitary, railway, academic_entrance_ug, academic_entrance_pg,
-- academic_entrance_phd, k12_olympiad, k12_scholarship, professional_cert,
-- foreign_study, language_proficiency, design_creative, not_applicable

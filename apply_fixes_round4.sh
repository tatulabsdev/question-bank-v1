#!/usr/bin/env bash
# Run from the ROOT of your question-bank-v1 repo in the Codespaces terminal:
#   bash apply_fixes_round4.sh
set -e
mkdir -p docs/exam-database

cat > exam_registry_schema.sql << 'TRYIT_EOF'
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
TRYIT_EOF
echo "wrote exam_registry_schema.sql"

cat > seed_exam_registry.py << 'TRYIT_EOF'

"""
TryIT Exam Registry Seeder — Phase 1 population
====================================================================
Populates exam_registry with every exam identified across the research
so far: 24 markdown files (K-12 database, PG entrance map, Case 3
Batches 1-2) plus this session's new findings.

THIS IS A STARTER SEED, NOT A CLAIM OF COMPLETENESS. Its job is to make
the registry's "what's still pending" query immediately useful — most
rows below are 'not_started' or 'pass1_mapped_only', which is honest:
Case 3's own Pass-1 file names 100+ exams, and this seed only carries
forward what's been explicitly named across all files read so far.
Run this once, then keep adding rows (or editing via Supabase directly)
as new exams get named or researched.
"""

import os
import datetime
import requests

REQUEST_TIMEOUT = 30
TODAY = datetime.date.today().isoformat()

# (exam_id, exam_name, body, category, level, frequency, status, source_file, notes)
REGISTRY = [
    # ── DEEP-DIVED (Case 3 Batch 1-2, this session) ──
    ("upsc_cse_prelims", "UPSC Civil Services Examination (Prelims)", "UPSC", "central_govt", "graduate",
     "annual", "deep_dived", "case3_batch1_flagship_govt_exams.md", "GS1 decides merit; CSAT qualifying only"),
    ("ssc_cgl", "SSC Combined Graduate Level", "SSC", "central_govt", "graduate",
     "annual", "deep_dived", "case3_batch1_flagship_govt_exams.md", "Tier2 decides merit; English highest-weighted"),
    ("ssc_chsl", "SSC Combined Higher Secondary Level", "SSC", "central_govt", "12th",
     "annual", "deep_dived", "case3_batch2_ssc_chsl_ib_acio.md", "Same English>GK pattern as CGL"),
    ("ibps_po", "IBPS Probationary Officer", "IBPS", "banking", "graduate",
     "annual", "deep_dived", "case3_batch1_flagship_govt_exams.md", "No GA at Prelims at all"),
    ("rrb_ntpc", "RRB Non-Technical Popular Categories", "Railway Recruitment Board", "railway", "12th-graduate",
     "irregular_vacancy_driven", "deep_dived", "case3_batch1_flagship_govt_exams.md", "Exact section split unconfirmed"),
    ("tnpsc_group4", "TNPSC Group 4 (CCSE-IV)", "TNPSC", "state_govt", "10th",
     "irregular_vacancy_driven", "deep_dived", "case3_batch1_flagship_govt_exams.md", "No negative marking; Tamil paper = 50% of marks"),
    ("ib_acio", "IB Assistant Central Intelligence Officer Gr-II", "MHA", "central_govt", "graduate",
     "irregular_vacancy_driven", "deep_dived", "case3_batch2_ssc_chsl_ib_acio.md", "Recheck cadence yearly-ish but NOT fixed"),
    ("cbi_si_via_ssc_cgl", "CBI Sub Inspector (via SSC CGL post option)", "SSC/CBI", "central_govt", "graduate",
     "annual", "not_applicable", "case3_batch2_ssc_chsl_ib_acio.md", "Not a separate exam — fully covered by ssc_cgl"),
    ("sports_quota_recruitment", "Sports Quota Recruitment (cross-department)", "Various", "not_applicable", "any",
     "ongoing_rolling", "not_applicable", "case3_batch2_ssc_chsl_ib_acio.md", "Trial/certificate-based, not MCQ — no question-bank content needed"),

    # ── PASS-1 MAPPED (named + scoped, weightage NOT yet researched) ──
    ("upsc_ifos", "UPSC Indian Forest Service", "UPSC", "central_govt", "graduate", "annual", "pass1_mapped_only", "case3_competitive_exams_map.md", "Shares CSE Prelims, separate Mains"),
    ("upsc_ese", "UPSC Engineering Services Examination", "UPSC", "central_govt", "specific_degree", "annual", "pass1_mapped_only", "case3_competitive_exams_map.md", None),
    ("upsc_cds", "UPSC Combined Defence Services", "UPSC", "defence_paramilitary", "graduate", "biannual", "pass1_mapped_only", "case3_competitive_exams_map.md", None),
    ("upsc_capf_ac", "UPSC CAPF Assistant Commandant", "UPSC", "defence_paramilitary", "graduate", "annual", "pass1_mapped_only", "case3_competitive_exams_map.md", None),
    ("ssc_mts", "SSC Multi-Tasking Staff", "SSC", "central_govt", "10th", "annual", "pass1_mapped_only", "case3_competitive_exams_map.md", None),
    ("ssc_gd_constable", "SSC GD Constable", "SSC", "defence_paramilitary", "10th", "annual", "pass1_mapped_only", "case3_competitive_exams_map.md", "BSF/CRPF/CISF/SSB/ITBP recruitment"),
    ("ssc_cpo", "SSC Central Police Organization SI", "SSC", "defence_paramilitary", "graduate", "annual", "pass1_mapped_only", "case3_competitive_exams_map.md", None),
    ("ssc_je", "SSC Junior Engineer", "SSC", "central_govt", "diploma_or_degree", "annual", "pass1_mapped_only", "case3_competitive_exams_map.md", None),
    ("ibps_clerk", "IBPS Clerk", "IBPS", "banking", "graduate", "annual", "pass1_mapped_only", "case3_competitive_exams_map.md", None),
    ("ibps_so", "IBPS Specialist Officer", "IBPS", "banking", "specific_degree", "annual", "pass1_mapped_only", "case3_competitive_exams_map.md", None),
    ("ibps_rrb", "IBPS RRB PO/Clerk", "IBPS", "banking", "graduate/12th", "annual", "pass1_mapped_only", "case3_competitive_exams_map.md", None),
    ("sbi_po", "SBI Probationary Officer", "SBI", "banking", "graduate", "annual", "pass1_mapped_only", "case3_competitive_exams_map.md", None),
    ("sbi_clerk", "SBI Clerk (Junior Associate)", "SBI", "banking", "12th", "annual", "pass1_mapped_only", "case3_competitive_exams_map.md", None),
    ("rbi_grade_b", "RBI Grade B Officer", "RBI", "banking", "graduate", "annual", "pass1_mapped_only", "case3_competitive_exams_map.md", None),
    ("rbi_assistant", "RBI Assistant", "RBI", "banking", "graduate", "annual", "pass1_mapped_only", "case3_competitive_exams_map.md", None),
    ("rrb_group_d", "RRB Group D", "Railway Recruitment Board", "railway", "10th", "irregular_vacancy_driven", "pass1_mapped_only", "case3_competitive_exams_map.md", None),
    ("rrb_je", "RRB Junior Engineer", "Railway Recruitment Board", "railway", "diploma_or_degree", "irregular_vacancy_driven", "pass1_mapped_only", "case3_competitive_exams_map.md", None),
    ("rrb_alp", "RRB Assistant Loco Pilot", "Railway Recruitment Board", "railway", "10th_iti", "irregular_vacancy_driven", "pass1_mapped_only", "case3_competitive_exams_map.md", None),
    ("gate", "GATE", "IISc/IITs", "academic_entrance_pg", "graduate", "annual", "deep_dived", "case2_batch1_engineering_pg.md", "PG admission + PSU recruitment dual-use"),
    ("iit_jam", "IIT JAM", "IISc/IITs", "academic_entrance_pg", "graduate", "annual", "deep_dived", "case2_batch1_engineering_pg.md", None),
    ("karnataka_pgcet", "Karnataka PGCET", "KEA", "state_govt", "graduate", "annual", "deep_dived", "case2_batch1_engineering_pg.md", None),
    ("tancet", "TANCET", "Anna University", "state_govt", "graduate", "annual", "deep_dived", "case2_batch1_engineering_pg.md", None),
    ("jee_main", "JEE Main", "NTA", "academic_entrance_ug", "12th", "biannual", "deep_dived", "deepdive_batch3_class11to12.md", None),
    ("neet_ug", "NEET-UG", "NTA", "academic_entrance_ug", "12th", "annual", "deep_dived", "deepdive_batch3_class11to12.md", None),
    ("cuet_ug", "CUET-UG", "NTA", "academic_entrance_ug", "12th", "annual", "deep_dived", "deepdive_batch3_class11to12.md", "2026: 37 subjects, no stream restriction"),
    ("nda_na", "NDA & NA", "UPSC", "defence_paramilitary", "12th", "biannual", "deep_dived", "deepdive_batch3_class11to12.md", None),
    ("iat_iiser", "IISER Aptitude Test (IAT)", "IISERs", "academic_entrance_ug", "12th", "annual", "deep_dived", "deepdive_batch3_class11to12.md", "Sole IISER admission channel since 2024"),

    # ── NOT STARTED (named in Pass-1 mapping, zero research yet) ──
    ("upsc_ies_iss", "UPSC Indian Economic/Statistical Service", "UPSC", "central_govt", "pg", "annual", "not_started", "case3_competitive_exams_map.md", None),
    ("upsc_cms", "UPSC Combined Medical Services", "UPSC", "central_govt", "mbbs", "annual", "not_started", "case3_competitive_exams_map.md", None),
    ("nabard_grade_a", "NABARD Grade A", "NABARD", "banking", "graduate", "annual", "not_started", "case3_competitive_exams_map.md", None),
    ("lic_aao", "LIC AAO", "LIC", "banking", "graduate", "annual", "not_started", "case3_competitive_exams_map.md", None),
    ("state_judicial_service", "State Judicial Service Exams", "State High Courts/PSCs", "state_govt", "llb", "irregular_vacancy_driven", "not_started", "case3_competitive_exams_map.md", "One per state, 28 states"),
    ("state_teacher_tet", "State TET (per state)", "State Boards", "state_govt", "graduate", "annual", "not_started", "case3_competitive_exams_map.md", "28 states + 8 UTs, each own TET"),
    ("cat_mba", "CAT", "IIMs", "academic_entrance_pg", "graduate", "annual", "not_started", "case2_pg_entrance_map_pass1.md", None),
    ("xat", "XAT", "XLRI", "academic_entrance_pg", "graduate", "annual", "not_started", "case2_pg_entrance_map_pass1.md", None),
    ("clat_pg", "CLAT-PG (LLM)", "Consortium of NLUs", "academic_entrance_pg", "llb", "annual", "not_started", "case2_pg_entrance_map_pass1.md", None),
    ("neet_pg", "NEET-PG", "NBE", "academic_entrance_pg", "mbbs", "annual", "not_started", "case2_pg_entrance_map_pass1.md", None),
    ("ini_cet", "INI-CET", "AIIMS Delhi", "academic_entrance_pg", "mbbs", "biannual", "not_started", "case2_pg_entrance_map_pass1.md", "Harder than NEET-PG"),
    ("ugc_net_jrf", "UGC-NET/JRF", "NTA", "professional_cert", "pg", "biannual", "not_started", "case2_pg_entrance_map_pass1.md", "Teaching eligibility + PhD gateway"),
    ("csir_net", "CSIR-NET", "CSIR", "professional_cert", "pg", "biannual", "not_started", "case2_pg_entrance_map_pass1.md", None),
    ("gre", "GRE", "ETS", "foreign_study", "graduate", "ongoing_rolling", "not_started", "case2_pg_entrance_map_pass1.md", "US/international PG admission"),
    ("gmat", "GMAT", "GMAC", "foreign_study", "graduate", "ongoing_rolling", "not_started", "case2_pg_entrance_map_pass1.md", None),
    ("ielts", "IELTS", "British Council/IDP", "language_proficiency", "any", "ongoing_rolling", "not_started", None, "India-to-abroad; not MCQ-shaped, needs separate product design"),
    ("toefl", "TOEFL iBT", "ETS", "language_proficiency", "any", "ongoing_rolling", "not_started", None, "Same product-shape caveat as IELTS"),
    ("pte_academic", "PTE Academic", "Pearson", "language_proficiency", "any", "ongoing_rolling", "not_started", None, None),
    ("usmle", "USMLE (USA)", "ECFMG/FSMB", "foreign_study", "mbbs", "ongoing_rolling", "not_started", "case2_pg_entrance_map_pass1.md", "Licensing, not admission"),
    ("plab_uk", "PLAB (UK)", "GMC", "foreign_study", "mbbs", "ongoing_rolling", "not_started", "case2_pg_entrance_map_pass1.md", None),
    ("nift_entrance", "NIFT Entrance", "NTA", "design_creative", "12th", "annual", "not_started", "deepdive_batch7_design_cs.md", "CAT section not MCQ-shaped"),
    ("uceed", "UCEED", "IIT Bombay", "design_creative", "12th", "annual", "not_started", "deepdive_batch7_design_cs.md", None),
]


def push_registry(rows, batch_size=50):
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()
    if not url or not key:
        print(f"SUPABASE_URL/SUPABASE_KEY not set — built {len(rows)} rows, nothing pushed")
        return 0

    payload = []
    for (exam_id, name, body, category, level, freq, status, source, notes) in rows:
        recheck = None
        if freq == "irregular_vacancy_driven":
            recheck = (datetime.date.today() + datetime.timedelta(days=180)).isoformat()
        payload.append({
            "exam_id": exam_id, "exam_name": name, "conducting_body": body,
            "category": category, "qualification_level": level, "frequency_type": freq,
            "research_status": status, "source_file": source,
            "last_researched_on": TODAY if status == "deep_dived" else None,
            "next_recheck_due": recheck, "notes": notes,
        })

    saved = 0
    for i in range(0, len(payload), batch_size):
        batch = payload[i:i + batch_size]
        r = requests.post(
            f"{url}/rest/v1/exam_registry",
            headers={"apikey": key, "Authorization": f"Bearer {key}",
                     "Content-Type": "application/json", "Prefer": "return=minimal,resolution=merge-duplicates"},
            json=batch, timeout=REQUEST_TIMEOUT,
        )
        if r.status_code in (200, 201):
            saved += len(batch)
        else:
            print(f"  error {r.status_code}: {r.text[:200]}")
    return saved


if __name__ == "__main__":
    deep = sum(1 for r in REGISTRY if r[6] == "deep_dived")
    pass1 = sum(1 for r in REGISTRY if r[6] == "pass1_mapped_only")
    not_started = sum(1 for r in REGISTRY if r[6] == "not_started")
    na = sum(1 for r in REGISTRY if r[6] == "not_applicable")
    print(f"Registry seed: {len(REGISTRY)} exams total")
    print(f"  deep_dived: {deep} | pass1_mapped_only: {pass1} | not_started: {not_started} | not_applicable: {na}")
    saved = push_registry(REGISTRY)
    print(f"Pushed {saved}/{len(REGISTRY)} to Supabase")
TRYIT_EOF
echo "wrote seed_exam_registry.py"

cat > docs/exam-database/case3_batch2_ssc_chsl_ib_acio.md << 'TRYIT_EOF'
# TRYIT EDUCATIONS — CASE 3 DEEP-DIVE, BATCH 2
# SSC CHSL, IB ACIO + two important SCOPE CLARIFICATIONS (CBI SI, Sports Quota)
# Verified against live sources, July 2026

---

# 1. SSC CHSL (Combined Higher Secondary Level) — 12th-pass level

| Field | Detail |
|---|---|
| Conducting Body | SSC |
| Posts | LDC/JSA, Postal Assistant, Sorting Assistant, Data Entry Operator, Court Clerk |
| Tier 1 | 100 questions, 200 marks, 60 min, **qualifying only**. 4 equal sections (25Q/50 marks each): English, General Intelligence/Reasoning, Quantitative Aptitude, General Awareness. |
| Tier 1 Negative Marking | 0.50 marks per wrong answer. |
| Tier 2 | **Scoring stage.** Session 1 (Paper 1): 4 modules across Sections I-II — Mathematical Abilities (30Q), Reasoning & General Intelligence (30Q), English Language & Comprehension (45Q — the largest single module), General Awareness (25Q). Total ~130Q/390 marks. Section III (Computer Knowledge, qualifying-only) + Session 2 (Skill/Typing Test, qualifying-only, no negative marking) don't count toward merit. |
| Tier 2 Negative Marking | 1 mark per wrong answer in Sections I-II (double Tier 1's rate) — no penalty on the qualifying-only Computer Knowledge module or the typing test. |
| Key structural note | English is again the single largest module by question count at the merit-deciding stage (45 of ~130 questions) — the same pattern already found in SSC CGL. This strengthens the earlier finding: **across SSC's exam family specifically, English consistently carries more real weight than General Awareness does**, which cuts against the common assumption that GK matters most for "SSC-type" prep. |

---

# 2. IB ACIO (Intelligence Bureau, Assistant Central Intelligence Officer Grade-II) — Graduate level

| Field | Detail |
|---|---|
| Conducting Body | Ministry of Home Affairs (MHA) |
| Frequency | Conducted periodically based on vacancy need — **not a fixed annual calendar exam** like SSC/UPSC/Banking. Multiple sources confirm it has run close to annually in recent cycles, but timing is vacancy-driven, not fixed. |
| Tier 1 | 100 questions, 100 marks, objective. 5 sections: Current Affairs, General Studies, Numerical Aptitude, Reasoning & Logical Aptitude, English Language. |
| Tier 1 Negative Marking | 0.25 marks per wrong answer. |
| Tier 2 | Descriptive, 50 marks — Essay Writing, English Comprehension/Précis, long-answer questions often touching current affairs/economics/socio-political issues. No negative marking (descriptive). |
| Tier 3 | Interview, 100 marks — notably equal in weight to the entire Tier 1 objective stage, a much heavier interview weighting than SSC/Banking/Railways use. |
| Content emphasis | General Awareness here is NOT the same as SSC's generic GK — it specifically emphasizes intelligence/security-agency topics (RAW, IB, NIA, NTRO), cybersecurity, and border/internal security. A generic `gk_*` question pool built for SSC will under-serve IB ACIO aspirants on this specific dimension. |
| Key structural note | Content-pattern-wise, IB ACIO is close enough to SSC CGL/CHSL (same 4 core subjects) that your existing topic taxonomy covers it structurally — but its irregular, vacancy-driven schedule means it needs a different *tracking* approach than SSC/UPSC's fixed annual calendar (see Exam Registry note below). |

---

# 3. SCOPE CLARIFICATION: "CBI Sub Inspector" is NOT a separate exam

Checked specifically because it was flagged as a named target. **CBI Sub Inspector is a post filled THROUGH the SSC CGL exam** (candidates select CBI SI as a post preference during SSC CGL application) — it is not an independent recruitment exam with its own separate syllabus/pattern. Same written exam (SSC CGL Tier 1 + Tier 2) already covered in Batch 1, followed by CBI-specific physical standards and document verification (no separate Physical Efficiency Test, unlike some other SSC CGL posts).

**Action:** no new content category needed for "CBI SI" — it's fully served by your existing SSC CGL topic mapping. Just make sure CBI-specific current-affairs content (agency structure, recent CBI cases in the news) gets folded into `gk_*`/`current_affairs` content for SSC-track students, similar to the IB ACIO content-emphasis note above.

---

# 4. SCOPE CLARIFICATION: "Sports Quota" recruitment is NOT an MCQ exam category

Checked specifically because it was flagged as a named target. Sports quota recruitment (used across CRPF/BSF/Railways/PSUs/many government departments) works structurally differently from every other exam in this database:
- It is an **eligibility relaxation + trial-based selection** pathway, not a written competitive exam — candidates with certified sports achievements (national/state-level certificates) get **age relaxation and/or a separate, smaller recruitment quota**, then are selected primarily via **sports trials/physical performance**, not MCQs.
- Where a written component exists at all, it is typically a much-reduced qualifying-only version of the same department's standard written test (e.g., a sports-quota CRPF candidate still needs to clear a basic written qualifying bar, but competes for the seat on sports merit, not written-exam rank).

**Action:** this is not a question-bank content gap — there's no MCQ syllabus to build. If TryIT wants to serve sports-quota aspirants at all, the right product isn't more questions; it's an **eligibility/certificate-guide product** (which sports achievements qualify, what certification is needed, which departments/quotas exist) — same shape as the PM YASASVI "no test exists" finding from the K-12 database. Flagging this now so effort isn't spent building MCQs nobody needs for this category.

---

## WHAT THIS BATCH ESTABLISHES

1. **English > GK at the merit-deciding stage is now confirmed across THREE SSC-family exams** (CGL, CHSL, and by extension CBI SI which uses the same exam) — a real, repeated pattern, not a one-off.
2. **Not every named target is a new research item.** CBI SI and sports quota needed a scope check, not a deep-dive — both turned out to require zero new topic-mapping work, just correct tagging of existing content.
3. **Exam frequency varies structurally** — SSC/UPSC/Banking/Railways run on fixed annual/biannual calendars; IB ACIO and similar agency-specific exams run on an irregular, vacancy-driven cadence. This is exactly the distinction that needs a systematic tracking mechanism (see the Exam Registry proposal delivered alongside this batch).
TRYIT_EOF
echo "wrote docs/exam-database/case3_batch2_ssc_chsl_ib_acio.md"

echo "Done. Run: python3 -m py_compile seed_exam_registry.py"

#!/usr/bin/env bash
# Run from the ROOT of your question-bank-v1 repo in the Codespaces terminal:
#   bash apply_fixes_round5.sh
set -e
mkdir -p docs/exam-database

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
    ("ssc_mts", "SSC Multi-Tasking Staff + Havaldar", "SSC", "central_govt", "10th",
     "annual", "deep_dived", "case3_batch3_ssc_mts_gd_ibps_clerk.md", "Hybrid marking by SESSION not paper/section"),
    ("ssc_gd_constable", "SSC GD Constable", "SSC", "defence_paramilitary", "10th",
     "annual", "deep_dived", "case3_batch3_ssc_mts_gd_ibps_clerk.md", "BSF/CRPF/CISF/SSB/ITBP/Assam Rifles recruitment"),
    ("ssc_cpo", "SSC Central Police Organization SI", "SSC", "defence_paramilitary", "graduate", "annual", "pass1_mapped_only", "case3_competitive_exams_map.md", None),
    ("ssc_je", "SSC Junior Engineer", "SSC", "central_govt", "diploma_or_degree", "annual", "pass1_mapped_only", "case3_competitive_exams_map.md", None),
    ("ibps_clerk", "IBPS Clerk", "IBPS", "banking", "graduate",
     "annual", "deep_dived", "case3_batch3_ssc_mts_gd_ibps_clerk.md", "LPT stage can disqualify even after Mains success"),
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

cat > docs/exam-database/case3_batch3_ssc_mts_gd_ibps_clerk.md << 'TRYIT_EOF'
# TRYIT EDUCATIONS — CASE 3 DEEP-DIVE, BATCH 3
# SSC MTS, SSC GD Constable, IBPS Clerk
# Verified against live sources, July 2026

---

# 1. SSC MTS (Multi-Tasking Staff) + Havaldar — 10th-pass level

| Field | Detail |
|---|---|
| Conducting Body | SSC |
| Posts | MTS (Non-Technical) across central govt departments; Havaldar (CBIC & CBN) |
| Structure | Single CBT with 2 mandatory sessions, same sitting — NOT a Tier 1/Tier 2 split like CGL/CHSL. Both sessions compulsory; skipping either disqualifies the candidate. |
| Session 1 | 40 questions, 120 marks (3 marks/question) — Numerical Ability + Reasoning. **No negative marking.** |
| Session 2 | 50 questions, 150 marks (3 marks/question) — English Language + General Awareness. **1 mark deducted per wrong answer.** |
| Total | 90 questions, 270 marks, 90 minutes (45 min/session; scribe candidates get 60 min/session) |
| Mode | Online CBT, available in **15 languages** (English, Hindi + 13 regional) |
| Havaldar-specific | Additional PET/PST after CBT, qualifying only |
| Key structural note | The zero-vs-full negative marking split is by **session (Maths+Reasoning vs English+GA)**, not by objective-vs-subjective like CA Foundation/CSEET — a third distinct variant of the "hybrid negative marking within one exam" pattern already tracked across this database. |

---

# 2. SSC GD Constable (General Duty) — 10th-pass level, Defence/Paramilitary

| Field | Detail |
|---|---|
| Conducting Body | SSC |
| Recruits For | BSF, CRPF, CISF, SSB, ITBP, Assam Rifles (as Rifleman), SSF, and Sepoy in Narcotics Control Bureau — the exact "CRPF/BSF-type" exam you flagged as a target category |
| Structure | Single CBT, one sitting, no tiers |
| Sections | 4 equal sections, 20 questions/40 marks each: General Intelligence & Reasoning, General Knowledge & General Awareness, Elementary Mathematics, English/Hindi |
| Total | 80 questions, 160 marks (2 marks/question), 60 minutes |
| Negative Marking | 0.25 marks per wrong answer |
| Mode | Online CBT, English/Hindi + 13 regional languages |
| Final Merit | Based on normalized CBT score alone (multiple shifts require normalization) + NCC bonus marks where applicable. PET/PST/Medical/Document Verification are qualifying-only, no marks. |
| Level | Class 10 standard content — the same foundational level as SSC MTS, but with a paramilitary-specific physical-fitness gate layered on top |
| Key structural note | This is a genuinely clean, flat 25/25/25/25 split with a single low negative-marking rate (0.25) — structurally the simplest exam pattern found in the Case 3 research so far, in contrast to CGL/CHSL's Tier1-vs-Tier2 asymmetric weighting. |

---

# 3. IBPS Clerk — Graduate level, Banking

| Field | Detail |
|---|---|
| Conducting Body | IBPS |
| Prelims | 100 questions, 100 marks, 60 min, **qualifying only**. 3 sections (individually timed, 20 min each): English Language, Reasoning Ability, Numerical Ability. |
| Mains | Recently revised (2026 cycle): 155 questions, 200 marks, 120 minutes (down from the older 190-question/160-minute format — any content or mock tests built on the pre-revision pattern is now outdated). 4 sections: General/Financial Awareness, General English, Reasoning Ability (now merged with Computer Aptitude into one section), Quantitative Aptitude. |
| Negative Marking | 0.25 marks per wrong answer, both Prelims and Mains. No penalty for unattempted. |
| Final Selection | 100% Mains marks — Prelims marks never count. No interview at all. |
| Language Proficiency Test (LPT) | Final qualifying stage — tests proficiency in the official language of the state applied to; exempted if the candidate studied that language in/above Class 10. Failing LPT disqualifies even after clearing Prelims+Mains. |
| Exact section-wise Mains question split | Multiple sources show minor variation post-revision (e.g., some cite GA~50Q/English~40Q/Reasoning~60Q, others show different splits) — recommend confirming the exact current numbers against the official 2026 IBPS Clerk notification once released, expected around July-August 2026. |
| Key structural note | IBPS Clerk's LPT is a genuinely distinct mechanism not seen in SSC/UPSC/RRB — a state-specific regional-language competency gate that sits AFTER the merit list, meaning a candidate can top Mains and still be disqualified for language reasons. This is directly relevant to your regional-language translation prioritization: IBPS-track students specifically need strength in whichever state's official language they're applying under, not just Hindi/English. |

---

## CROSS-EXAM COMPARISON — BATCH 3

| Exam | Merit-deciding stage | Negative marking pattern | Sections | Level |
|---|---|---|---|---|
| SSC MTS | Single CBT (both sessions) | Session 1: none. Session 2: 1 mark | Maths+Reasoning / English+GA | 10th |
| SSC GD Constable | Single CBT | 0.25 mark flat | 4 equal (Reasoning/GK/Maths/English-Hindi) | 10th |
| IBPS Clerk | Mains only | 0.25 mark flat, both stages | 3 (Prelims) / 4 (Mains) | Graduate |

## UPDATED CROSS-DATABASE FINDING

**The "zero negative marking on one component, penalty on another, within the same single-sitting exam" pattern is now confirmed a FOURTH way** — SSC MTS splits it by session (not by paper like CA Foundation, not by question-type like GATE/JAM, not by section-marking-scheme like UCEED). Four structurally distinct variants of hybrid marking now exist across this database, each requiring its own explicit rule in any scoring-simulator tool built for TryIT.

## EXAM REGISTRY UPDATE
`ssc_mts`, `ssc_gd_constable`, and `ibps_clerk` move from `pass1_mapped_only`/`not_started` to `deep_dived` in the exam registry (see updated `seed_exam_registry.py`).

## STILL PENDING (Case 3 Batch 4+)
- SSC CPO, SSC JE, IBPS SO, IBPS RRB PO/Clerk, SBI PO/Clerk, RBI Grade B/Assistant, RRB Group D/JE/ALP, NABARD Grade A, LIC AAO, State Judicial Services, State TETs — all still `pass1_mapped_only` or `not_started`.
TRYIT_EOF
echo "wrote docs/exam-database/case3_batch3_ssc_mts_gd_ibps_clerk.md"

echo "Done. Run: python3 -m py_compile seed_exam_registry.py"

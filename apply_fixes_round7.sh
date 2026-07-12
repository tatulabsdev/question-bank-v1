#!/usr/bin/env bash
# Run from the ROOT of your question-bank-v1 repo in the Codespaces terminal:
#   bash apply_fixes_round7.sh
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
    ("ssc_cpo", "SSC Central Police Organization SI", "SSC", "defence_paramilitary", "graduate",
     "annual", "deep_dived", "case3_batch4_ssc_cpo_sbi_po.md", "Full standalone 200-mark English paper = 50% of total marks"),
    ("ssc_je", "SSC Junior Engineer (Civil/Mechanical/Electrical)", "SSC", "central_govt", "diploma_or_degree",
     "annual", "deep_dived", "case3_batch5_ssc_je_sbi_clerk.md", "80% technical content weight - needs dedicated engineering topic pool"),
    ("ibps_clerk", "IBPS Clerk", "IBPS", "banking", "graduate",
     "annual", "deep_dived", "case3_batch3_ssc_mts_gd_ibps_clerk.md", "LPT stage can disqualify even after Mains success"),
    ("ibps_so", "IBPS Specialist Officer", "IBPS", "banking", "specific_degree", "annual", "pass1_mapped_only", "case3_competitive_exams_map.md", None),
    ("ibps_rrb", "IBPS RRB PO/Clerk", "IBPS", "banking", "graduate/12th", "annual", "pass1_mapped_only", "case3_competitive_exams_map.md", None),
    ("sbi_po", "SBI Probationary Officer", "SBI", "banking", "graduate",
     "annual", "deep_dived", "case3_batch4_ssc_cpo_sbi_po.md", "2026: descriptive cut 50->30 marks; attempt limits loosened"),
    ("sbi_clerk", "SBI Clerk (Junior Associate)", "SBI", "banking", "12th",
     "annual", "deep_dived", "case3_batch5_ssc_je_sbi_clerk.md", "HAS sectional cutoff at Prelims, unlike SBI PO"),
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

cat > docs/exam-database/case3_batch5_ssc_je_sbi_clerk.md << 'TRYIT_EOF'
# TRYIT EDUCATIONS — CASE 3 DEEP-DIVE, BATCH 5
# SSC JE, SBI Clerk
# Verified against live sources, July 2026

---

# 1. SSC JE (Junior Engineer) — Diploma/Degree level, Technical

| Field | Detail |
|---|---|
| Conducting Body | SSC |
| Posts | Junior Engineer (Civil, Mechanical, Electrical) across CPWD, MES, BRO, CWC, and other central departments |
| Paper 1 | 200 questions, 200 marks (1 mark each), 2 hours, **qualifying only** — screens candidates for Paper 2. 3 sections: General Intelligence & Reasoning (50 marks), General Awareness (50 marks), General Engineering — candidate's chosen discipline (100 marks, i.e. half the paper). |
| Paper 1 Negative Marking | 0.25 marks per wrong answer |
| Paper 2 | **Scoring stage.** 100 questions, 300 marks (3 marks/question), 2 hours — fully technical, entirely from the candidate's chosen engineering discipline (Civil & Structural / Electrical / Mechanical). Candidates select ONE discipline; no cross-discipline questions. |
| Paper 2 Negative Marking | 1 mark per wrong answer — 4x Paper 1's rate, and each question is worth 3x as many marks, so a wrong answer in Paper 2 is far costlier in both absolute and relative terms than in Paper 1. |
| Mode | Both papers online CBT, objective-only (Paper 2 was historically descriptive — SSC shifted it to objective/MCQ in a recent cycle; content built on the old descriptive-Paper-2 assumption is outdated) |
| Final Merit | Paper 2 score decides merit; Paper 1 is purely a screening gate + Document Verification |
| Key structural note | **General Engineering already occupies half of Paper 1** (100 of 200 marks) even before Paper 2's fully-technical 300 marks — meaning across both papers combined, technical/engineering content is worth 400 of 500 total marks (80%), with General Intelligence + GA together making up only the remaining 20%. This is the most technical-content-heavy exam found in the Case 3 research so far, a sharp contrast to SSC CGL/CHSL/CPO/GD/MTS which are uniformly generalist. |

---

# 2. SBI Clerk (Junior Associate) — 12th-pass level, Banking

| Field | Detail |
|---|---|
| Conducting Body | State Bank of India |
| Prelims | 100 questions, 100 marks, 1 hour, **qualifying only**, sectional timing (20 min/section) AND sectional cutoffs (unlike SBI PO's Prelims, which has no sectional cutoff). 3 sections: English Language (30 marks), Numerical Ability (35 marks), Reasoning Ability (35 marks). |
| Mains | **Scoring stage**, decides final merit entirely. 190 questions, 200 marks, 2 hours 40 minutes, sectional timing. 4 sections: General/Financial Awareness, General English, Quantitative Aptitude, Reasoning Ability & Computer Aptitude. |
| Negative Marking | 0.25 marks per wrong answer, both Prelims and Mains. No penalty for unattempted. |
| Bonus Marks | Trained SBI apprentices get a 2.5% bonus (5 of 200 Mains marks) added to their aggregate — a genuine SBI-Clerk-specific mechanic not found in SBI PO or IBPS Clerk. |
| No Interview | Selection is 100% Mains marks (+ apprentice bonus where applicable) — no interview stage at all. |
| Local Language Proficiency Test (LLPT) | Same mechanism as IBPS Clerk's LPT — mandatory after Mains for candidates without Class 10/12 proof of having studied the applied state's local language. Failing it disqualifies even after topping Mains. |
| Key structural note | **SBI Clerk has sectional cutoffs at Prelims; SBI PO explicitly does not.** This is a real, easy-to-miss distinction for anyone building a unified "SBI-track" product — a Clerk aspirant who's weak in one Prelims section can be eliminated even with a strong overall score, while a PO aspirant with the same profile would advance. Difficulty note (sourced, not editorial): multiple sources independently describe SBI Clerk's question difficulty as higher than IBPS Clerk's despite a near-identical syllabus/pattern — worth reflecting in question-bank difficulty calibration if both are served from a shared "banking clerk" topic pool. |

---

## CROSS-EXAM COMPARISON — BATCH 5

| Exam | Merit-deciding stage | Sectional cutoff at qualifying stage? | Technical content weight | Negative marking |
|---|---|---|---|---|
| SSC JE | Paper 2 only | N/A (Paper 1 is screening only) | 80% of combined marks | 0.25 (P1) / 1 mark (P2) |
| SBI Clerk | Mains only | YES at Prelims (unlike SBI PO) | None (generalist) | 0.25, both stages |

## UPDATED CROSS-DATABASE FINDING

**SBI Clerk vs SBI PO's differing Prelims-sectional-cutoff rule is a new, exam-family-internal distinction** — the first case in this database where two exams from the *same conducting body*, with near-identical subject lists at Prelims, apply genuinely different qualifying rules. This means "SBI-track prep" cannot safely share one qualifying-stage strategy across both exams even though the content overlaps heavily.

**SSC JE's 80%-technical-content weighting makes it structurally unlike every other SSC exam researched so far** (CGL/CHSL/CPO/GD/MTS are all generalist, testing Reasoning/English/GK/basic Maths with no domain-specific technical component). This confirms SSC JE needs its own dedicated technical-subject content (Civil/Electrical/Mechanical engineering topics) rather than reusing the generalist `maths_*`/`reasoning_*`/`gk_*` pool that serves the rest of the SSC family — a genuine new-subject-area requirement, not just a re-weighting exercise.

## EXAM REGISTRY UPDATE
`ssc_je` and `sbi_clerk` move to `deep_dived` in the exam registry.

## STILL PENDING (Case 3 Batch 6+)
- IBPS SO, IBPS RRB PO/Clerk, RBI Grade B/Assistant, NABARD Grade A, LIC AAO
- RRB Group D/JE/ALP, State Judicial Services, State TETs, remaining State PSCs
TRYIT_EOF
echo "wrote docs/exam-database/case3_batch5_ssc_je_sbi_clerk.md"

echo "Done. Run: python3 -m py_compile seed_exam_registry.py"

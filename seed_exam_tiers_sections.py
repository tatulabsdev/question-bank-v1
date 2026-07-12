"""
TryIT Exam Registry — Tiers & Sections Seeder
====================================================================
Populates exam_tiers and exam_sections with the REAL sourced structural
data (question counts, marks, negative marking, qualifying-vs-scoring
status) already documented in case3_batch1_flagship_govt_exams.md and
case_new_batch_pg_research_entrance.md.

SCOPE: covers exactly the 10 exams that have been deep-dived with real
structural detail so far. This is NOT a claim that these are the only
important exams — it's the honest boundary of what's actually been
researched. Extend this file as more batches get researched.

WHERE NUMBERS AREN'T SOURCED, THEY ARE LEFT AS None, not guessed. E.g.
SSC CGL Tier 2's exact question-count split between Maths and Reasoning
within its combined "Section I" was never independently sourced — only
the overall marks-share percentage was (see exam_syllabus_map seeder for
that). This script only records what's genuinely confirmed at the
tier/section level.
"""

import os
import requests

REQUEST_TIMEOUT = 30

# Each tier: (tier_id, exam_id, tier_name, tier_order, is_qualifying,
#             total_questions, total_marks, duration_minutes,
#             negative_marking_rate, mode, notes)
TIERS = [
    ("upsc_cse_prelims_prelims", "upsc_cse_prelims", "Prelims", 1, False,
     180, 400, 240, None, "offline_omr",
     "GS1 (100Q/200marks, scoring) + CSAT (80Q/200marks, qualifying-only) combined here as one tier — see sections for the split"),

    ("ssc_cgl_tier1", "ssc_cgl", "Tier 1", 1, True,
     100, 200, 60, 0.25, "online_cbt", "Qualifying only, does not decide merit"),
    ("ssc_cgl_tier2", "ssc_cgl", "Tier 2", 2, False,
     None, None, 120, 0.50, "online_cbt",
     "Scoring/merit-deciding stage. Paper 1 has Section I (Maths+Reasoning combined) and Section II (English+GA combined), each a separate fixed 1-hour window. Exact question-count split within each combined section not independently sourced."),

    ("ibps_po_prelims", "ibps_po", "Prelims", 1, True,
     100, 100, 60, 0.25, "online_cbt", "Qualifying only, never enters final merit"),
    ("ibps_po_mains", "ibps_po", "Mains", 2, False,
     170, 200, None, 0.25, "online_cbt",
     "Scoring stage, decides merit alongside Interview (80:20 Mains:Interview ratio). Plus a separate 25-mark Descriptive Test, not part of the 170 objective questions."),

    ("rrb_ntpc_cbt1", "rrb_ntpc", "CBT 1", 1, True,
     100, 100, 90, 0.333, "online_cbt", "Qualifying only. Exact section-wise split not independently confirmed."),
    ("rrb_ntpc_cbt2", "rrb_ntpc", "CBT 2", 2, False,
     120, 120, 90, 0.333, "online_cbt", "Scoring/merit-deciding stage. Same 3-section structure as CBT1, more questions."),

    ("tnpsc_group4_main", "tnpsc_group4", "Single Paper", 1, False,
     200, 300, 180, 0.0, "offline_omr",
     "No negative marking at all — a structural outlier vs every other exam in this registry. Qualifying mark 90/300 for all categories."),

    ("cuet_pg_main", "cuet_pg", "Single Paper (per subject)", 1, False,
     75, 300, 90, 0.25, "online_cbt",
     "One paper per subject code selected (up to 4 codes). General Aptitude section removed since 2025 cycle."),

    ("ugc_net_session", "ugc_net_jrf", "Single Session (Paper 1 + 2)", 1, False,
     150, 300, 180, 0.0, "online_cbt", "Both papers compulsory, no break, zero negative marking"),

    ("csir_net_session", "csir_net", "Single Paper (subject-dependent)", 1, False,
     None, 200, 180, None, "online_cbt",
     "Question count and negative-marking rate vary significantly by subject — see exam_sections for the 5 subject-specific breakdowns. A single flat number here would misrepresent at least 2 of the 5 subjects."),

    ("cat_main", "cat_mba", "Single Test (3 sections)", 1, False,
     68, 204, 120, None, "online_cbt",
     "Negative marking is -1 for MCQ, 0 for TITA questions within the SAME section — not a single flat rate, hence None here."),

    ("xat_part1", "xat", "Part 1 (VALR + DM + QA&DI)", 1, False,
     75, None, 170, 0.25, "online_cbt",
     "Additional -0.10 penalty for every unattempted question beyond the first 8 — a rule with no clean single-field representation, noted here."),
    ("xat_part2", "xat", "Part 2 (General Knowledge)", 2, False,
     20, None, 10, 0.0, "online_cbt",
     "Scored but explicitly EXCLUDED from percentile calculation — used only in XLRI's own final selection separately"),
]

# Each section: (section_id, tier_id, section_name, section_order,
#                num_questions, marks_per_question, total_marks,
#                time_minutes, negative_marking_override, subject_group, notes)
SECTIONS = [
    ("upsc_cse_gs1", "upsc_cse_prelims_prelims", "GS Paper 1", 1, 100, 2.0, 200, 120, None, "gk",
     "This is what actually decides the Prelims cutoff"),
    ("upsc_cse_csat", "upsc_cse_prelims_prelims", "CSAT Paper 2", 2, 80, 2.5, 200, 120, None, None,
     "Qualifying only (33% to pass), NOT added to merit. Mixed English/Quant/Reasoning/Decision-Making/DI — internal split not independently sourced, so subject_group left null rather than guessed."),

    ("ssc_cgl_t1_reasoning", "ssc_cgl_tier1", "General Intelligence & Reasoning", 1, 25, 2.0, 50, 15, None, "reasoning", None),
    ("ssc_cgl_t1_ga", "ssc_cgl_tier1", "General Awareness", 2, 25, 2.0, 50, 15, None, "gk", None),
    ("ssc_cgl_t1_quant", "ssc_cgl_tier1", "Quantitative Aptitude", 3, 25, 2.0, 50, 15, None, "quant", None),
    ("ssc_cgl_t1_english", "ssc_cgl_tier1", "English Comprehension", 4, 25, 2.0, 50, 15, None, "english", None),
    ("ssc_cgl_t2_combined", "ssc_cgl_tier2", "Section I+II (Maths+Reasoning / English+GA)", 1, None, None, None, 120, None, None,
     "See exam_syllabus_map for the sourced ~35/23/23/19 weightage split across English/Quant/Reasoning/GA — the exact question-count split within each combined section isn't independently confirmed."),

    ("ibps_po_prelims_quant", "ibps_po_prelims", "Quantitative Aptitude", 1, None, None, 30, 20, None, "quant", None),
    ("ibps_po_prelims_reasoning", "ibps_po_prelims", "Reasoning Ability", 2, None, None, 40, 20, None, "reasoning",
     "Highest-weighted Prelims section"),
    ("ibps_po_prelims_english", "ibps_po_prelims", "English Language", 3, None, None, 30, 20, None, "english", None),
    ("ibps_po_mains_combined", "ibps_po_mains", "Reasoning+Computer / DI / English / GA-Banking", 1, 170, None, 200, None, None, None,
     "See exam_syllabus_map for sourced weightage split — GA/Banking ~25%, Reasoning (merged w/ Computer Aptitude) highest, DI moderate-high, Quant/English moderate"),

    ("rrb_ntpc_cbt2_maths", "rrb_ntpc_cbt2", "Mathematics", 1, None, None, None, None, None, "quant", "Approx even 1/3 split, not independently confirmed"),
    ("rrb_ntpc_cbt2_reasoning", "rrb_ntpc_cbt2", "General Intelligence & Reasoning", 2, None, None, None, None, None, "reasoning", "Approx even 1/3 split, not independently confirmed"),
    ("rrb_ntpc_cbt2_ga", "rrb_ntpc_cbt2", "General Awareness", 3, None, None, None, None, None, "gk", "Approx even 1/3 split, not independently confirmed"),

    ("tnpsc_g4_tamil_eng", "tnpsc_group4_main", "Tamil Eligibility-cum-Scoring / English (alternative)", 1, 100, None, 150, None, None, "english",
     "Not part of the quant/reasoning/gk rebalancing group — a distinct language-proficiency subject worth exactly as much as GS+Aptitude combined"),
    ("tnpsc_g4_gs", "tnpsc_group4_main", "General Studies", 2, 75, None, 130, None, None, "gk",
     "Marks estimated at midpoint of sourced 112.5-150 range"),
    ("tnpsc_g4_aptitude", "tnpsc_group4_main", "Aptitude & Mental Ability", 3, 25, None, 44, None, None, None,
     "Marks estimated at midpoint of sourced 37.5-50 range. Covers exactly the topics reasoning_*/maths_arithmetic already contain."),

    ("cuet_pg_domain", "cuet_pg_main", "Domain-Specific Paper", 1, 75, 4.0, 300, 90, None, None,
     "Pure single-subject test per the subject code selected — no fixed reasoning/english/gk component the way govt exams have"),

    ("ugc_net_paper1", "ugc_net_session", "Paper 1 (General)", 1, 50, 2.0, 100, None, None, None,
     "10 units: Teaching Aptitude, Research Aptitude, Comprehension, Communication, Mathematical Reasoning, Logical Reasoning, Data Interpretation, ICT, People & Environment, Higher Education System — directly overlaps existing reasoning_*/data_interpretation_* topics"),
    ("ugc_net_paper2", "ugc_net_session", "Paper 2 (Subject-Specific)", 2, 100, 2.0, 200, None, None, None,
     "85-87 subjects available; per-subject syllabus not researched in this pass"),

    ("csir_net_parta", "csir_net_session", "Part A (Common, General Aptitude)", 1, None, 2.0, None, None, 0.25, "reasoning",
     "Common across all 5 subjects: logical reasoning, graphical analysis, analytical/numerical ability, quantitative comparison, series, puzzles"),
    ("csir_net_partb_c", "csir_net_session", "Part B + C (Subject-Specific)", 2, None, None, None, None, None, None,
     "Marking varies significantly by subject (2-33% negative marking depending on subject and part) — see research doc for the 5 subject-specific breakdowns. Maps to actual science topics, not the generic quant/reasoning/gk groups."),

    ("cat_varc", "cat_main", "VARC (Verbal Ability & Reading Comprehension)", 1, 24, 3.0, 72, 40, None, "english", None),
    ("cat_dilr", "cat_main", "DILR (Data Interp. & Logical Reasoning)", 2, 22, 3.0, 66, 40, None, None,
     "Genuinely mixed reasoning+data_interpretation — sourced research doesn't give an internal split between the two, so subject_group left null rather than guessed"),
    ("cat_qa", "cat_main", "QA (Quantitative Ability)", 3, 22, 3.0, 66, 40, None, "quant", None),

    ("xat_valr", "xat_part1", "Verbal Ability & Logical Reasoning", 1, 26, 1.0, None, None, 0.25, None,
     "Mixed verbal+reasoning, no sourced internal split"),
    ("xat_dm", "xat_part1", "Decision Making", 2, 21, 1.0, None, None, 0.25, None,
     "No existing TryIT topic group matches this — genuinely distinct ethics/prioritization caselet format, would need its own new topic/pattern design"),
    ("xat_qadi", "xat_part1", "Quantitative Ability & Data Interpretation", 3, 28, 1.0, None, None, 0.25, None,
     "Mixed quant+data_interpretation, no sourced internal split"),
    ("xat_gk", "xat_part2", "General Knowledge", 1, 20, 1.0, None, None, 0.0, "gk",
     "Scored but excluded from percentile — used only in XLRI's separate final selection"),
]


def push(rows, table, columns):
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()
    if not url or not key:
        print(f"SUPABASE_URL/SUPABASE_KEY not set — built {len(rows)} {table} rows, nothing pushed")
        return 0
    payload = [dict(zip(columns, row)) for row in rows]
    saved = 0
    for i in range(0, len(payload), 50):
        batch = payload[i:i + 50]
        r = requests.post(
            f"{url}/rest/v1/{table}",
            headers={"apikey": key, "Authorization": f"Bearer {key}",
                     "Content-Type": "application/json", "Prefer": "return=minimal,resolution=merge-duplicates"},
            json=batch, timeout=REQUEST_TIMEOUT,
        )
        if r.status_code in (200, 201):
            saved += len(batch)
        else:
            print(f"  error {r.status_code}: {r.text[:300]}")
    return saved


if __name__ == "__main__":
    tier_cols = ["tier_id", "exam_id", "tier_name", "tier_order", "is_qualifying",
                 "total_questions", "total_marks", "duration_minutes",
                 "negative_marking_rate", "mode", "notes"]
    section_cols = ["section_id", "tier_id", "section_name", "section_order",
                    "num_questions", "marks_per_question", "total_marks",
                    "time_minutes", "negative_marking_override", "subject_group", "notes"]

    print(f"Pushing {len(TIERS)} tiers across 10 exams...")
    saved_t = push(TIERS, "exam_tiers", tier_cols)
    print(f"  {saved_t}/{len(TIERS)} tiers saved")

    print(f"Pushing {len(SECTIONS)} sections...")
    saved_s = push(SECTIONS, "exam_sections", section_cols)
    print(f"  {saved_s}/{len(SECTIONS)} sections saved")

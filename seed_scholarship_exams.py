"""
TryIT Exam Registry — Scholarship Exam Seeder
====================================================================
Adds NTSE, NMMS, and INSPIRE-SHE to the exam registry, tiers,
sections, and syllabus_map. Based on real sourced research (July 2026).

RESEARCH SUMMARY:
- NTSE: 100Q MAT (reasoning) + 100Q SAT (Science 40Q, Social 40Q, Maths 20Q)
  200 marks total, no negative marking, Class 10 level. Conducted by NCERT.
- NMMS: 90Q MAT (reasoning) + 90Q SAT (Science ~35Q, Social ~35Q, Maths 20Q)
  180 marks total, no negative marking, Class 8 level. Conducted by state SCERTs.
- INSPIRE-SHE: NOT an aptitude test — merit-based scholarship (top 1% in
  Class 12 boards pursuing natural sciences, OR top 10,000 in JEE Advanced/
  NEET). KVPY was officially discontinued in 2022 and merged into INSPIRE.
  Added to registry as awareness entry, NO syllabus_map rows — there is no
  standalone exam to prepare for, students qualify through existing JEE/NEET.

WHY NO NEW TOPICS NEEDED: NTSE and NMMS test the exact same subjects already
in the 164-topic bank (reasoning, maths arithmetic/algebra, physics, chemistry,
biology, GK history/geography/polity). The only gap was these exams not being
in the registry and not having exam_tags on relevant questions.
"""

import os
import uuid
import requests

REQUEST_TIMEOUT = 30


def _push(table, rows, on_conflict=None):
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()
    if not url or not key:
        print(f"  SUPABASE_URL/SUPABASE_KEY not set — built {len(rows)} {table} rows, nothing pushed")
        return 0
    params = {}
    if on_conflict:
        params["on_conflict"] = on_conflict
    saved = 0
    for i in range(0, len(rows), 50):
        batch = rows[i:i + 50]
        r = requests.post(
            f"{url}/rest/v1/{table}",
            headers={"apikey": key, "Authorization": f"Bearer {key}",
                     "Content-Type": "application/json",
                     "Prefer": "return=minimal,resolution=merge-duplicates"},
            params=params,
            json=batch, timeout=REQUEST_TIMEOUT,
        )
        if r.status_code in (200, 201):
            saved += len(batch)
        else:
            print(f"  [{table}] error {r.status_code}: {r.text[:200]}")
    return saved


# ──────────────────────────────────────────────────────────
# 1. EXAM REGISTRY ROWS
# ──────────────────────────────────────────────────────────
REGISTRY_ROWS = [
    {
        "exam_id": "ntse",
        "exam_name": "NTSE (National Talent Search Examination)",
        "conducting_body": "NCERT",
        "category": "scholarship",
        "qualification_level": "10th",
        "frequency_type": "annual",
        "research_status": "deep_dived",
        "source_file": "case_scholarship_exams.md",
        "notes": "100Q MAT (reasoning) + 100Q SAT (Science 40Q, Social 40Q, Maths 20Q). No negative marking. Class 10 level. Stage 1 state-level, Stage 2 national.",
    },
    {
        "exam_id": "nmms",
        "exam_name": "NMMS (National Means-cum-Merit Scholarship)",
        "conducting_body": "State SCERTs / MHRD",
        "category": "scholarship",
        "qualification_level": "8th",
        "frequency_type": "annual",
        "research_status": "deep_dived",
        "source_file": "case_scholarship_exams.md",
        "notes": "90Q MAT (reasoning) + 90Q SAT (Science ~35Q, Social ~35Q, Maths 20Q). No negative marking. Class 7-8 syllabus. State-conducted.",
    },
    {
        "exam_id": "inspire_she",
        "exam_name": "INSPIRE-SHE Scholarship (formerly KVPY)",
        "conducting_body": "DST (Department of Science & Technology)",
        "category": "scholarship",
        "qualification_level": "12th",
        "frequency_type": "annual",
        "research_status": "deep_dived",
        "source_file": "case_scholarship_exams.md",
        "notes": "NOT an aptitude test — KVPY discontinued 2022, merged into INSPIRE. Merit-based: top 1% Class 12 boards pursuing natural sciences, OR top 10,000 JEE Advanced/NEET. No separate exam to prepare for.",
    },
]


# ──────────────────────────────────────────────────────────
# 2. EXAM TIERS
# ──────────────────────────────────────────────────────────
TIER_ROWS = [
    {
        "tier_id": "ntse_mat",
        "exam_id": "ntse",
        "tier_name": "MAT (Mental Ability Test)",
        "tier_order": 1,
        "is_qualifying": False,
        "total_questions": 100,
        "total_marks": 100,
        "duration_minutes": 120,
        "negative_marking_rate": 0.0,
        "mode": "offline_omr",
        "notes": "Tests verbal and non-verbal reasoning, logical thinking, pattern recognition. Equal 50% weight alongside SAT in final merit.",
    },
    {
        "tier_id": "ntse_sat",
        "exam_id": "ntse",
        "tier_name": "SAT (Scholastic Aptitude Test)",
        "tier_order": 2,
        "is_qualifying": False,
        "total_questions": 100,
        "total_marks": 100,
        "duration_minutes": 120,
        "negative_marking_rate": 0.0,
        "mode": "offline_omr",
        "notes": "Science 40Q + Social Science 40Q + Mathematics 20Q. Based on NCERT Class 9-10 syllabus.",
    },
    {
        "tier_id": "nmms_mat",
        "exam_id": "nmms",
        "tier_name": "MAT (Mental Ability Test)",
        "tier_order": 1,
        "is_qualifying": False,
        "total_questions": 90,
        "total_marks": 90,
        "duration_minutes": 90,
        "negative_marking_rate": 0.0,
        "mode": "offline_omr",
        "notes": "Tests verbal/non-verbal metacognitive abilities. Class 7-8 level reasoning.",
    },
    {
        "tier_id": "nmms_sat",
        "exam_id": "nmms",
        "tier_name": "SAT (Scholastic Aptitude Test)",
        "tier_order": 2,
        "is_qualifying": False,
        "total_questions": 90,
        "total_marks": 90,
        "duration_minutes": 90,
        "negative_marking_rate": 0.0,
        "mode": "offline_omr",
        "notes": "Science ~35Q + Social Science ~35Q + Mathematics 20Q. NCERT Class 7-8 syllabus. Exact split varies by state.",
    },
]


# ──────────────────────────────────────────────────────────
# 3. EXAM SECTIONS
# ──────────────────────────────────────────────────────────
SECTION_ROWS = [
    # NTSE MAT
    {
        "section_id": "ntse_mat_verbal",
        "tier_id": "ntse_mat",
        "section_name": "Verbal Reasoning",
        "section_order": 1,
        "num_questions": 50,
        "marks_per_question": 1.0,
        "total_marks": 50,
        "time_minutes": None,
        "negative_marking_override": 0.0,
        "subject_group": "reasoning",
        "notes": "Analogy, classification, series, blood relations, direction sense, coding-decoding",
    },
    {
        "section_id": "ntse_mat_nonverbal",
        "tier_id": "ntse_mat",
        "section_name": "Non-Verbal Reasoning",
        "section_order": 2,
        "num_questions": 50,
        "marks_per_question": 1.0,
        "total_marks": 50,
        "time_minutes": None,
        "negative_marking_override": 0.0,
        "subject_group": "reasoning",
        "notes": "Mirror image, embedded figures, paper folding, figure series — exact split between verbal/nonverbal not independently sourced",
    },
    # NTSE SAT
    {
        "section_id": "ntse_sat_science",
        "tier_id": "ntse_sat",
        "section_name": "Science (Physics/Chemistry/Biology)",
        "section_order": 1,
        "num_questions": 40,
        "marks_per_question": 1.0,
        "total_marks": 40,
        "time_minutes": None,
        "negative_marking_override": 0.0,
        "subject_group": None,
        "notes": "Mixed physics/chemistry/biology, NCERT Class 9-10. Internal split ~equal thirds not independently sourced.",
    },
    {
        "section_id": "ntse_sat_social",
        "tier_id": "ntse_sat",
        "section_name": "Social Science (History/Geography/Polity/Economics)",
        "section_order": 2,
        "num_questions": 40,
        "marks_per_question": 1.0,
        "total_marks": 40,
        "time_minutes": None,
        "negative_marking_override": 0.0,
        "subject_group": "gk",
        "notes": "History/Geography/Civics/Economics, NCERT Class 9-10. Internal split not independently sourced.",
    },
    {
        "section_id": "ntse_sat_maths",
        "tier_id": "ntse_sat",
        "section_name": "Mathematics",
        "section_order": 3,
        "num_questions": 20,
        "marks_per_question": 1.0,
        "total_marks": 20,
        "time_minutes": None,
        "negative_marking_override": 0.0,
        "subject_group": "quant",
        "notes": "Algebra, geometry, arithmetic, probability, statistics — NCERT Class 9-10",
    },
    # NMMS MAT
    {
        "section_id": "nmms_mat_reasoning",
        "tier_id": "nmms_mat",
        "section_name": "Mental Ability (Verbal + Non-Verbal)",
        "section_order": 1,
        "num_questions": 90,
        "marks_per_question": 1.0,
        "total_marks": 90,
        "time_minutes": 90,
        "negative_marking_override": 0.0,
        "subject_group": "reasoning",
        "notes": "Analogy, classification, numerical series, pattern recognition. Class 7-8 difficulty.",
    },
    # NMMS SAT
    {
        "section_id": "nmms_sat_science",
        "tier_id": "nmms_sat",
        "section_name": "Science",
        "section_order": 1,
        "num_questions": 35,
        "marks_per_question": 1.0,
        "total_marks": 35,
        "time_minutes": None,
        "negative_marking_override": 0.0,
        "subject_group": None,
        "notes": "Mixed physics/chemistry/biology, NCERT Class 7-8. State-wise exact count may vary slightly.",
    },
    {
        "section_id": "nmms_sat_social",
        "tier_id": "nmms_sat",
        "section_name": "Social Studies",
        "section_order": 2,
        "num_questions": 35,
        "marks_per_question": 1.0,
        "total_marks": 35,
        "time_minutes": None,
        "negative_marking_override": 0.0,
        "subject_group": "gk",
        "notes": "History/Geography/Civics/Economics, NCERT Class 7-8.",
    },
    {
        "section_id": "nmms_sat_maths",
        "tier_id": "nmms_sat",
        "section_name": "Mathematics",
        "section_order": 3,
        "num_questions": 20,
        "marks_per_question": 1.0,
        "total_marks": 20,
        "time_minutes": None,
        "negative_marking_override": 0.0,
        "subject_group": "quant",
        "notes": "Rational numbers, linear equations, geometry, data handling — NCERT Class 7-8.",
    },
]


# ──────────────────────────────────────────────────────────
# 4. SYLLABUS MAP — NTSE and NMMS only
# INSPIRE-SHE intentionally has NO rows: it's not a standalone
# prep exam, students qualify through JEE/NEET/board performance.
# Weightages sourced from official NCERT NTSE pattern and NMMS
# pattern documents, confirmed July 2026.
# ──────────────────────────────────────────────────────────

def build_syllabus_map_rows():
    """
    NTSE (200 marks total):
      MAT = 50% of total (100 marks)
        reasoning (all topics): 50%
      SAT = 50% of total (100 marks)
        Science (40Q = 40% of SAT = 20% of total):
          physics topics: 1/3 of 20% = 6.67%
          chemistry topics: 1/3 of 20% = 6.67%
          biology topics: 1/3 of 20% = 6.67%
        Social Science (40Q = 40% of SAT = 20% of total):
          gk_history topics: 1/3 of 20% = 6.67%
          gk_geography topics: 1/3 of 20% = 6.67%
          gk_polity topics: 1/3 of 20% = 6.67%
        Mathematics (20Q = 20% of SAT = 10% of total):
          maths_arithmetic topics: 50% of 10% = 5%
          maths_algebra topics: 50% of 10% = 5%

    NMMS (180 marks total, same structural split):
      MAT = 50% → reasoning topics
      SAT Science = ~19.4% → science topics
      SAT Social = ~19.4% → gk topics
      SAT Maths = ~11.1% → maths_arithmetic + maths_algebra
    """
    from supabase_data import fetch_topics

    topics = fetch_topics()
    if not topics:
        print("  Could not fetch topics from Supabase — no syllabus map rows built")
        return []

    # Group topics by subject
    by_subject = {}
    for t in topics:
        by_subject.setdefault(t["subject_id"], []).append(t["topic_id"])

    def rows_for(exam_id, section_id, subject_ids, total_weight_pct):
        """Even split of total_weight_pct across all topics in listed subjects."""
        topic_ids = []
        for subj in subject_ids:
            topic_ids.extend(by_subject.get(subj, []))
        if not topic_ids:
            return []
        per_topic = round(total_weight_pct / len(topic_ids), 4)
        return [
            {
                "map_id": f"map_{uuid.uuid4().hex[:12]}",
                "exam_id": exam_id,
                "section_id": section_id,
                "topic_id": tid,
                "weightage_percent": per_topic,
                "priority": 3,
                "notes": f"Even split of {total_weight_pct:.1f}% across {len(topic_ids)} topics in {', '.join(subject_ids)}",
            }
            for tid in topic_ids
        ]

    all_rows = []

    # ── NTSE ──
    # Reasoning (50% — all reasoning topics across verbal + nonverbal)
    all_rows += rows_for("ntse", "ntse_mat_verbal",
                         ["reasoning_verbal"], 25.0)
    all_rows += rows_for("ntse", "ntse_mat_nonverbal",
                         ["reasoning_nonverbal"], 25.0)
    # Science (20% — physics/chemistry/biology, ~equal thirds)
    all_rows += rows_for("ntse", "ntse_sat_science",
                         ["physics"], 6.67)
    all_rows += rows_for("ntse", "ntse_sat_science",
                         ["chemistry"], 6.67)
    all_rows += rows_for("ntse", "ntse_sat_science",
                         ["biology"], 6.67)
    # Social Science (20% — history/geography/polity, ~equal thirds)
    all_rows += rows_for("ntse", "ntse_sat_social",
                         ["gk_history"], 6.67)
    all_rows += rows_for("ntse", "ntse_sat_social",
                         ["gk_geography"], 6.67)
    all_rows += rows_for("ntse", "ntse_sat_social",
                         ["gk_polity"], 6.67)
    # Mathematics (10% — arithmetic + algebra, equal halves)
    all_rows += rows_for("ntse", "ntse_sat_maths",
                         ["maths_arithmetic"], 5.0)
    all_rows += rows_for("ntse", "ntse_sat_maths",
                         ["maths_algebra"], 5.0)

    # ── NMMS ──
    # Reasoning (50%)
    all_rows += rows_for("nmms", "nmms_mat_reasoning",
                         ["reasoning_verbal"], 25.0)
    all_rows += rows_for("nmms", "nmms_mat_reasoning",
                         ["reasoning_nonverbal"], 25.0)
    # Science (~19.4%)
    all_rows += rows_for("nmms", "nmms_sat_science",
                         ["physics"], 6.47)
    all_rows += rows_for("nmms", "nmms_sat_science",
                         ["chemistry"], 6.47)
    all_rows += rows_for("nmms", "nmms_sat_science",
                         ["biology"], 6.47)
    # Social Studies (~19.4%)
    all_rows += rows_for("nmms", "nmms_sat_social",
                         ["gk_history"], 6.47)
    all_rows += rows_for("nmms", "nmms_sat_social",
                         ["gk_geography"], 6.47)
    all_rows += rows_for("nmms", "nmms_sat_social",
                         ["gk_polity"], 6.47)
    # Mathematics (~11.1%)
    all_rows += rows_for("nmms", "nmms_sat_maths",
                         ["maths_arithmetic"], 5.56)
    all_rows += rows_for("nmms", "nmms_sat_maths",
                         ["maths_algebra"], 5.56)

    return all_rows


if __name__ == "__main__":
    print("=" * 60)
    print("TryIT — Scholarship Exam Seeder (NTSE, NMMS, INSPIRE-SHE)")
    print("=" * 60)

    # 1. Registry
    print(f"\nPushing {len(REGISTRY_ROWS)} exam registry rows...")
    saved = _push("exam_registry", REGISTRY_ROWS, on_conflict="exam_id")
    print(f"  {saved}/{len(REGISTRY_ROWS)} saved")

    # 2. Tiers
    print(f"\nPushing {len(TIER_ROWS)} tier rows...")
    saved = _push("exam_tiers", TIER_ROWS, on_conflict="tier_id")
    print(f"  {saved}/{len(TIER_ROWS)} saved")

    # 3. Sections
    print(f"\nPushing {len(SECTION_ROWS)} section rows...")
    saved = _push("exam_sections", SECTION_ROWS, on_conflict="section_id")
    print(f"  {saved}/{len(SECTION_ROWS)} saved")

    # 4. Syllabus map
    print("\nBuilding syllabus map rows (fetching live topics from Supabase)...")
    syllabus_rows = build_syllabus_map_rows()
    if syllabus_rows:
        print(f"  Built {len(syllabus_rows)} rows across NTSE + NMMS")
        by_exam = {}
        for r in syllabus_rows:
            by_exam[r["exam_id"]] = by_exam.get(r["exam_id"], 0) + 1
        for exam_id, count in by_exam.items():
            print(f"    {exam_id}: {count} topic rows")
        saved = _push("exam_syllabus_map", syllabus_rows,
                      on_conflict="exam_id,section_id,topic_id")
        print(f"  {saved}/{len(syllabus_rows)} saved")
    else:
        print("  No rows built (check Supabase connection)")

    print("\n" + "=" * 60)
    print("INSPIRE-SHE: added to registry only — no syllabus_map rows")
    print("(it is merit-based, not a standalone aptitude exam to prep for)")
    print("=" * 60)


#!/usr/bin/env bash
# Run from the ROOT of your question-bank-v1 repo in the Codespaces terminal:
#   bash apply_fixes_round3.sh
set -e
mkdir -p docs/exam-database

cat > topic_exam_weightage.py << 'TRYIT_EOF'

"""
TryIT Question Engine — Topic/Exam Weightage Analyzer (Phase 1)
====================================================================
Reads your LIVE topics table from Supabase, computes what each topic's
question_target WOULD become if rebalanced using real, sourced exam
weightage data (case3_batch1_flagship_govt_exams.md), and prints a
before/after diff report for you to review.

THIS SCRIPT NEVER WRITES TO SUPABASE. It only reads topics and prints a
report. Applying the suggested changes is a separate, deliberate step
(see apply_suggested_targets() at the bottom, commented out) — you
should read the report first and decide if the rebalancing makes sense.

WHY THIS IS "PHASE 1", NOT FINAL:
Only 5 exams have real, sourced marks-weightage data as of this run
(UPSC CSE Prelims, SSC CGL, IBPS PO, RRB NTPC, TNPSC Group 4 — see
case3_batch1_flagship_govt_exams.md). Case 3's own Pass-1 mapping file
lists 100+ distinct exams; most (SSC CHSL/MTS, IBPS Clerk/SO, RRB Group D,
other State PSCs, UPSC's non-CSE exams) still have ZERO weightage data.

This script does NOT invent numbers for those. It computes a rebalancing
multiplier per subject-group (quant/reasoning/english/gk/data_interpretation)
using ONLY the 5 confirmed exams, and applies that multiplier evenly
within each group — meaning results for topics whose primary exams are
already covered (e.g., maths_arithmetic, which SSC/Banking/RRB/TNPSC all
test) are more trustworthy right now than topics tied mostly to
uncovered exams. Re-run this script after each new Case 3 deep-dive
batch to sharpen the numbers further.

CANDIDATE VOLUME CAVEAT: Only UPSC CSE (10 lakh+ applicants) and SSC CGL
(28.15 lakh applicants) have a confirmed applicant-volume figure from
sourced research. IBPS PO, RRB NTPC, and TNPSC Group 4 do NOT have a
confirmed volume figure in this pass, so they are weighted as "medium"
placeholders (not fabricated as an exact number) until confirmed.
"""

import os
import requests

REQUEST_TIMEOUT = 30

# ──────────────────────────────────────────────────────────
# EXAM PROFILES — sourced from case3_batch1_flagship_govt_exams.md
# Each exam: which subject-group gets what SHARE of the MERIT-DECIDING
# stage's marks (not the qualifying stage, where one exists), plus a
# volume weight. volume_confirmed=True means the number is sourced;
# False means it's an unconfirmed placeholder (weight=2, "medium").
# ──────────────────────────────────────────────────────────
EXAM_PROFILES = {
    "upsc_cse_prelims": {
        # GS Paper 1 decides the cutoff; CSAT (quant/reasoning/english) is
        # qualifying-only and doesn't move merit — weighted near-zero here
        # deliberately, per the sourced structural finding.
        "weights": {"gk": 0.90, "reasoning": 0.04, "quant": 0.03, "english": 0.03, "data_interpretation": 0.0},
        "volume_confirmed": True,
        "volume_lakh": 10,  # "10 lakh+ applicants" — sourced
    },
    "ssc_cgl": {
        # Tier 2 marks decide merit: English ~35%, Maths ~23%, Reasoning ~23%, GA ~19%
        "weights": {"english": 0.35, "quant": 0.23, "reasoning": 0.23, "gk": 0.19, "data_interpretation": 0.0},
        "volume_confirmed": True,
        "volume_lakh": 28.15,  # "2,815,445 applicants" 2025 cycle — sourced
    },
    "ibps_po": {
        # Mains decides merit: GA/Banking ~25%, Reasoning+Computer high,
        # Quant/DI moderate, English moderate. Approximate split from
        # sourced section list (170 Q / 200 marks across 4 sections).
        "weights": {"gk": 0.25, "reasoning": 0.30, "data_interpretation": 0.20, "quant": 0.15, "english": 0.10},
        "volume_confirmed": False,
        "volume_lakh": None,  # not confirmed in this pass — placeholder weight used instead
    },
    "rrb_ntpc": {
        # CBT2 decides merit: 3 roughly-comparable sections, exact split
        # NOT confirmed (flagged honestly in the batch file) — using an
        # even 1/3 split as the stated approximation, no English at all.
        "weights": {"gk": 0.33, "quant": 0.335, "reasoning": 0.335, "english": 0.0, "data_interpretation": 0.0},
        "volume_confirmed": False,
        "volume_lakh": None,
    },
    "tnpsc_group4": {
        # GS+Aptitude portion only (Tamil/English language paper itself
        # isn't part of the maths/reasoning/english/gk topic groups we're
        # rebalancing — it's a distinct language-proficiency subject).
        # Of the non-language 150 marks: GS ~112.5-150, Aptitude ~37.5-50.
        # Using GS 75%, Aptitude split evenly across quant/reasoning.
        "weights": {"gk": 0.75, "quant": 0.125, "reasoning": 0.125, "english": 0.0, "data_interpretation": 0.0},
        "volume_confirmed": False,
        "volume_lakh": None,
    },
}

UNCONFIRMED_VOLUME_PLACEHOLDER = 5  # "medium" weight in lakh-equivalent units, NOT a real figure

# ──────────────────────────────────────────────────────────
# topic_id prefix -> subject_group. Extend this as new topics are added.
# ──────────────────────────────────────────────────────────
def subject_group_for_topic(topic_id: str) -> str | None:
    if topic_id.startswith("data_interpretation"):
        return "data_interpretation"
    if topic_id.startswith("maths_"):
        return "quant"
    if topic_id.startswith("reasoning_"):
        return "reasoning"
    if topic_id.startswith("english_"):
        return "english"
    if topic_id.startswith("gk_") or topic_id.startswith("current_affairs"):
        return "gk"
    return None  # topics outside these 4 groups (science, commerce, etc.) are untouched by this phase


def compute_group_demand():
    """Returns {group: demand_score} using confirmed-volume-weighted average
    of each exam's marks-share for that group."""
    demand = {"gk": 0.0, "reasoning": 0.0, "quant": 0.0, "english": 0.0, "data_interpretation": 0.0}
    total_volume = 0.0
    for exam, profile in EXAM_PROFILES.items():
        vol = profile["volume_lakh"] if profile["volume_confirmed"] else UNCONFIRMED_VOLUME_PLACEHOLDER
        total_volume += vol
        for group, weight in profile["weights"].items():
            demand[group] += weight * vol
    # normalize to a multiplier centered at 1.0 across the 4 core groups
    core = {g: demand[g] for g in ("gk", "reasoning", "quant", "english")}
    avg = sum(core.values()) / len(core)
    multipliers = {g: (demand[g] / avg if avg else 1.0) for g in demand}
    return multipliers, total_volume


def fetch_topics():
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()
    if not url or not key:
        print("SUPABASE_URL/SUPABASE_KEY not set — cannot fetch live topics")
        return []
    r = requests.get(
        f"{url}/rest/v1/topics?select=topic_id,subject_id,question_target,coverage_score",
        headers={"apikey": key, "Authorization": f"Bearer {key}"},
        timeout=REQUEST_TIMEOUT,
    )
    if r.status_code != 200:
        print(f"error {r.status_code}: {r.text[:200]}")
        return []
    return r.json()


def main():
    multipliers, total_volume = compute_group_demand()

    print("=" * 70)
    print("PHASE 1 REBALANCING — based on 5 confirmed exams only")
    print("=" * 70)
    print(f"{'Group':<20}{'Demand multiplier':<20}{'Interpretation'}")
    for group in ("gk", "reasoning", "quant", "english", "data_interpretation"):
        m = multipliers[group]
        interp = "INCREASE target" if m > 1.05 else ("DECREASE target" if m < 0.95 else "roughly unchanged")
        print(f"{group:<20}{m:<20.2f}{interp}")
    print()
    print("NOTE: 3 of 5 exams (IBPS PO, RRB NTPC, TNPSC Group 4) have an")
    print("UNCONFIRMED volume figure and are using a flat placeholder weight.")
    print("Only UPSC CSE and SSC CGL volumes are sourced. Treat this as a")
    print("directional signal, not a final answer, until more exams are")
    print("researched with confirmed applicant volumes.")
    print()

    topics = fetch_topics()
    if not topics:
        print("(No live topics fetched — set SUPABASE_URL/SUPABASE_KEY to see the per-topic diff.)")
        return

    print("=" * 70)
    print("PER-TOPIC DIFF (current question_target -> suggested)")
    print("=" * 70)
    changed = 0
    for t in sorted(topics, key=lambda x: x["topic_id"]):
        group = subject_group_for_topic(t["topic_id"])
        if group is None:
            continue  # untouched in this phase
        current = t["question_target"] or 0
        suggested = round(current * multipliers[group] / 500) * 500  # round to nearest 500
        if suggested != current:
            changed += 1
            print(f"  {t['topic_id']:<55}{current:>7} -> {suggested:>7}  ({group})")

    print()
    print(f"{changed}/{len(topics)} topics would change under this Phase 1 rebalancing.")
    print("This script has NOT written anything to Supabase. Review the diff,")
    print("then decide whether to apply it — and keep researching Case 3")
    print("Batches 2+ to sharpen this further before treating it as final.")


if __name__ == "__main__":
    main()
TRYIT_EOF
echo "wrote topic_exam_weightage.py"

cat > docs/exam-database/case3_batch1_flagship_govt_exams.md << 'TRYIT_EOF'
# TRYIT EDUCATIONS — CASE 3 DEEP-DIVE, BATCH 1 (FLAGSHIP EXAMS)
# UPSC CSE, SSC CGL, IBPS PO, RRB NTPC, TNPSC Group 4
# Verified against live sources, July 2026
# This is the FIRST deep-dive batch closing the gap flagged in case3_competitive_exams_map.md
# (that file was Pass-1 mapping only — no marks/section data). Batches 2+ still needed for
# full Case 3 coverage (SSC CHSL/MTS, IBPS Clerk/SO, RRB Group D/JE, other State PSCs).

---

## GROUND RULES (same as all previous batches)
- Difficulty Score: not assigned in this batch — these are all "must-clear" competitive exams where difficulty framing works differently (see structural findings below).
- PYQ: format/question-type description only, no reproduced questions.

---

# 1. UPSC CSE PRELIMS (Civil Services Examination) — Graduate level

| Field | Detail |
|---|---|
| Conducting Body | UPSC |
| Structure | 2 papers, same day: GS Paper 1 + CSAT (Paper 2) |
| GS Paper 1 | 100 questions, 200 marks (2 marks/question), 2 hours. Subjects: History, Geography, Polity, Economy, Science, Environment, Current Affairs — this is the paper that actually decides the Prelims cutoff. |
| CSAT (Paper 2) | 80 questions, 200 marks (2.5 marks/question), 2 hours. Subjects: English comprehension, Quantitative Aptitude, Logical Reasoning, Decision-Making, Data Interpretation (up to Class 10 level numeracy). **Qualifying only** — candidates need 33% (66/200) to pass, but CSAT marks are NOT added to the merit-deciding score. |
| Negative Marking | 1/3rd of the question's marks deducted for each wrong answer, both papers (0.66 for GS1, 0.83 for CSAT). No penalty for unattempted questions. |
| Mains | 9 descriptive papers (2 qualifying language papers + Essay + GS I-IV + 2 Optional papers), no negative marking. |
| Interview | 275 marks, included in final merit with Mains. |
| Key structural note | Because CSAT is qualifying-only, GS Paper 1's General-Knowledge-heavy content is what actually drives competitive differentiation at Prelims stage — Quant/Reasoning/English prep matters for clearing the 33% bar, but doesn't move the merit needle the way GK/Current-Affairs depth does. |

---

# 2. SSC CGL (Combined Graduate Level) — Graduate level

| Field | Detail |
|---|---|
| Conducting Body | SSC |
| Tier 1 | 100 questions, 200 marks, 60 minutes, **qualifying only**. 4 equal sections, each individually sectionally-timed (15 min/section): General Intelligence & Reasoning (25Q/50 marks), General Awareness (25Q/50 marks), Quantitative Aptitude (25Q/50 marks), English Comprehension (25Q/50 marks). |
| Tier 1 Negative Marking | 0.50 marks per wrong answer. |
| Tier 2 | Scoring stage — this is what decides final merit. Paper 1 (compulsory, all posts): Section I (Maths+Reasoning) and Section II (English+GA) each have a fixed, non-transferable 1-hour window. English carries the single highest weight of any subject in final scoring (~35% of Tier 2 Paper 1 marks), with Maths and Reasoning at ~23% each and GA at ~19%. Paper 2 (JSO/Statistical Investigator posts only) tests Statistics. |
| Tier 2 Negative Marking | 1 mark deducted per wrong answer in Paper 1's Sections I-II (double the Tier 1 penalty), 0.50 in Paper 2. |
| Key structural note | Tier 1 is a flat 25/25/25/25 split across Reasoning/GA/Quant/English — but Tier 2, which is what actually decides your rank, weights English highest, and English+Maths+Reasoning together account for ~81% of the scoring marks, with GA at only ~19%. |

---

# 3. IBPS PO (Probationary Officer) — Graduate level, Banking

| Field | Detail |
|---|---|
| Conducting Body | IBPS |
| Prelims | 100 questions, 100 marks, 60 min, **qualifying only** (not added to final merit). 3 sections, each individually timed: Quantitative Aptitude (30 marks), Reasoning Ability (40 marks — highest-weighted Prelims section), English Language (30 marks). No General Awareness at all in Prelims. |
| Mains | 170 objective questions, 200 marks + 25-mark Descriptive Test (essay/comprehension). Sections: Reasoning & Computer Aptitude, Data Analysis & Interpretation, English Language, General/Economy/Banking Awareness (~50 marks — a much heavier GA weight than Prelims). |
| Negative Marking | 0.25 marks per wrong answer, both Prelims and Mains objective sections. No penalty for unattempted or on the Descriptive Test. |
| Final Selection | Mains + Interview combined at an 80:20 ratio. Prelims marks never enter final merit at all. |
| Key structural note | Banking exams structurally front-load Reasoning + Quant + English at Prelims (no GA at all), then shift hard toward Banking/Economy Awareness + Data Interpretation at Mains — a very different shape from SSC/UPSC's GK-heavy pattern. |

---

# 4. RRB NTPC (Railways, Non-Technical Popular Categories) — 12th-pass to Graduate level, varies by post

| Field | Detail |
|---|---|
| Conducting Body | Railway Recruitment Board (RRB) |
| CBT 1 | 100 questions, 100 marks, 90 min, **qualifying only**. 3 sections: Mathematics, General Intelligence & Reasoning, General Awareness. Exact section-wise question split not independently confirmed in this pass — sources consistently describe 3 roughly-comparable sections without a single authoritative breakdown; recommend confirming exact split from the official RRB NTPC CBT1 notification PDF before treating any specific ratio as final. |
| CBT 2 | 120 questions, 120 marks, 90 min, **scoring** — this is the merit-deciding stage. Same 3 sections as CBT1, more questions. |
| Negative Marking | 1/3 mark deducted per wrong answer, both CBT1 and CBT2. No penalty for unattempted. |
| CBAT (Station Master/Traffic Assistant only) | No negative marking; weighted 30% against CBT2's 70% for these specific posts' final merit. |
| Key structural note | RRB is available in 15 languages for the exam itself — a genuinely unique accessibility feature versus SSC/UPSC/Banking, which are English/Hindi only. This matters directly for your translation-stage prioritization. |

---

# 5. TNPSC GROUP 4 (CCSE-IV) — SSLC (10th pass) level, Tamil Nadu state government

| Field | Detail |
|---|---|
| Conducting Body | Tamil Nadu Public Service Commission (TNPSC) |
| Structure | Single written paper, 200 questions, 300 marks, 3 hours, offline OMR. No interview at all. |
| Sections | Part A: Tamil Eligibility-cum-Scoring Test (100Q, 150 marks) — SSLC-standard Tamil grammar/literature; General English is confirmed still available as an alternative language choice, contrary to some reports of its removal. Part B: General Studies (75Q, ~112.5-150 marks depending on source) — General Science, Current Events, Geography, History, Polity, Economy, with mandatory Tamil Nadu-specific history/culture/socio-political-movements content. Part C: Aptitude & Mental Ability (25Q, ~37.5-50 marks depending on source) — covers exactly the topics your `reasoning_*` and `maths_arithmetic` topic groups already contain (Number Series, Analogies, Coding-Decoding, Blood Relations, Simplification, Percentages, Ratio, Profit/Loss, Time & Work). |
| Negative Marking | **NONE** — a structural outlier versus all 4 exams above. Candidates are explicitly advised to attempt every question since guessing carries zero downside. |
| Qualifying Mark | 90/300 minimum for all categories. |
| Key structural note | Since the Tamil/English language paper is worth exactly as much as General Studies + Aptitude combined, TNPSC Group 4 puts unusually heavy weight on the language-proficiency component compared to any other exam in this database — a genuinely distinct pattern versus SSC/Banking/Railways/UPSC, none of which have a dedicated language-scoring section of this size. |

---

## CROSS-EXAM COMPARISON — BATCH 1

| Exam | Merit-deciding stage | GA/GK weight at merit stage | Reasoning weight | Quant weight | English weight | Negative marking |
|---|---|---|---|---|---|---|
| UPSC CSE | Prelims GS1 (Mains+Interview for final) | Very high (GS1 is ~100% GK/current-affairs) | Low (CSAT qualifying only) | Low (CSAT qualifying only) | Low (CSAT qualifying only) | 1/3 mark |
| SSC CGL | Tier 2 | ~19% | ~23% | ~23% | ~35% (highest) | 1 mark (Tier 2) |
| IBPS PO | Mains | ~25% (Banking Awareness) | High (merged w/ Computer Aptitude) | Moderate | Moderate | 0.25 mark |
| RRB NTPC | CBT 2 | ~33% (approx, unconfirmed exact split) | ~33% (approx) | ~33% (approx) | Not tested at all | 1/3 mark |
| TNPSC Group 4 | Single paper | ~37.5-50% (GS) | ~12.5-16% (part of Aptitude) | ~12.5-16% (part of Aptitude) | 50% (Tamil/English language paper) | **None** |

## KEY OBSERVATIONS FOR QUESTION-BANK WEIGHTING

1. **GK/General Awareness weight varies enormously by exam** — from ~100% effective weight at UPSC Prelims down to ~19% at SSC CGL Tier 2. A single flat `gk_*` question_target can't serve both audiences well; weighting needs to account for which exams a topic's users are actually prepping for.
2. **English is SSC CGL's highest-weighted subject (35%) but RRB NTPC doesn't test English at all.** These are both core TryIT exams per your platform's target list — this is a genuine, evidence-based reason to NOT apply uniform targets across `english_*` topics regardless of which exam family a student is using them for.
3. **TNPSC Group 4's zero negative marking is a real product-design signal** — practice questions/mock tests for TNPSC audiences should probably not penalize guessing the way SSC/UPSC/Banking/RRB content does, since real-exam strategy actually differs.
4. **RRB NTPC's exact section-wise question split (Maths vs Reasoning vs GA counts within the 100/120 total) was not independently confirmed** in this pass — multiple sources describe "3 sections" without a single authoritative ratio. Flagging honestly rather than guessing a specific number.

## WHAT'S STILL MISSING (Case 3 Batches 2+)
- SSC: CHSL, MTS, GD Constable, CPO, JE (12th/10th-pass tier — high volume, not yet researched)
- Banking: IBPS Clerk, IBPS SO, SBI PO/Clerk, RBI Grade B/Assistant (only IBPS PO done)
- Railways: RRB Group D, RRB JE, RRB ALP (only NTPC done)
- State PSCs beyond TNPSC Group 4: TNPSC Group 1/2/2A, and other major states (UPPSC, BPSC, MPPSC, KPSC etc. — none done)
- UPSC: only CSE Prelims done; CDS, CAPF AC, ESE not yet researched

Recommend continuing in this same batch style — this file proves the approach works and the data is genuinely obtainable per-exam.
TRYIT_EOF
echo "wrote docs/exam-database/case3_batch1_flagship_govt_exams.md"

echo "Done. Run: python3 -m py_compile topic_exam_weightage.py"

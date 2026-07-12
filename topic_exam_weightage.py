
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

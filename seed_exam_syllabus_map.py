"""
TryIT Exam Registry — Syllabus Map Seeder (Phase 1)
====================================================================
Populates exam_syllabus_map — the table that actually links a real
topic_id to a real exam_id with a weightage percentage. This is the
piece that finally lets you answer "does our Number System L6 content
serve SSC-CGL?" for real, rather than just knowing exam structure.

SCOPE, STATED HONESTLY: only 5 exams get real rows here — the same 5
already used in topic_exam_weightage.py's EXAM_PROFILES, because those
are the only 5 with a genuinely sourced subject-group weightage split
(not just section structure). CAT, XAT, UGC-NET, and CSIR-NET have real
exam_tiers/exam_sections (see seed_exam_tiers_sections.py) but their
sections often mix two concepts together (e.g. CAT's DILR = reasoning +
data_interpretation combined) with no sourced split between them —
inventing a 50/50 split here would be a fabricated number, not research.
Those 4 exams are intentionally left with ZERO syllabus_map rows until
a dedicated research pass sources their actual internal split.

METHOD: for each of the 5 exams, each subject-group's overall weightage
(from EXAM_PROFILES, e.g. SSC CGL: english=35%, quant=23%, ...) is
divided EVENLY across every live topic currently tagged to that group.
This is a real, honest first pass — not "every topic within a group
matters equally in reality" (some almost certainly matter more than
others), but an even split is the correct default when no per-topic
data exists yet, rather than guessing which topics matter more.
"""

import os
import requests
import uuid

REQUEST_TIMEOUT = 30

# Reused directly from topic_exam_weightage.py so there's exactly ONE
# source of truth for these sourced weights, not two copies that could
# drift apart.
from topic_exam_weightage import EXAM_PROFILES, subject_group_for_topic

# Maps exam_id -> the specific exam_sections rows its weightage actually
# applies to, since exam_syllabus_map needs a section_id, not just an
# exam_id. Sourced from the same batch files as EXAM_PROFILES itself.
EXAM_TO_SECTIONS = {
    "upsc_cse_prelims": {
        "gk": "upsc_cse_gs1",
        # CSAT's internal split isn't sourced — reasoning/quant/english
        # weights for this exam are near-zero anyway per EXAM_PROFILES,
        # so skipping a dedicated CSAT section mapping here is honest,
        # not a meaningful omission.
    },
    "ssc_cgl": {
        "english": "ssc_cgl_t2_combined",
        "quant": "ssc_cgl_t2_combined",
        "reasoning": "ssc_cgl_t2_combined",
        "gk": "ssc_cgl_t2_combined",
    },
    "ibps_po": {
        "gk": "ibps_po_mains_combined",
        "reasoning": "ibps_po_mains_combined",
        "data_interpretation": "ibps_po_mains_combined",
        "quant": "ibps_po_mains_combined",
        "english": "ibps_po_mains_combined",
    },
    "rrb_ntpc": {
        "gk": "rrb_ntpc_cbt2_ga",
        "quant": "rrb_ntpc_cbt2_maths",
        "reasoning": "rrb_ntpc_cbt2_reasoning",
    },
    "tnpsc_group4": {
        "gk": "tnpsc_g4_gs",
        "quant": "tnpsc_g4_aptitude",
        "reasoning": "tnpsc_g4_aptitude",
    },
}


def fetch_topics():
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()
    if not url or not key:
        print("SUPABASE_URL/SUPABASE_KEY not set — cannot fetch live topics")
        return []
    r = requests.get(
        f"{url}/rest/v1/topics?select=topic_id",
        headers={"apikey": key, "Authorization": f"Bearer {key}"},
        timeout=REQUEST_TIMEOUT,
    )
    if r.status_code != 200:
        print(f"error fetching topics {r.status_code}: {r.text[:200]}")
        return []
    return [t["topic_id"] for t in r.json()]


def build_rows():
    topics = fetch_topics()
    if not topics:
        return []

    by_group = {}
    for tid in topics:
        group = subject_group_for_topic(tid)
        if group:
            by_group.setdefault(group, []).append(tid)

    rows = []
    for exam_id, profile in EXAM_PROFILES.items():
        section_map = EXAM_TO_SECTIONS.get(exam_id, {})
        for group, weight in profile["weights"].items():
            if weight <= 0:
                continue  # don't create a 0%-weightage row, it's not meaningful
            section_id = section_map.get(group)
            if not section_id:
                continue
            group_topics = by_group.get(group, [])
            if not group_topics:
                continue
            per_topic_pct = round((weight * 100) / len(group_topics), 3)
            for tid in group_topics:
                rows.append({
                    "map_id": f"map_{uuid.uuid4().hex[:12]}",
                    "exam_id": exam_id,
                    "section_id": section_id,
                    "topic_id": tid,
                    "weightage_percent": per_topic_pct,
                    "priority": 3,  # default "normal" priority; not yet individually reviewed
                    "notes": f"Even split of {exam_id}'s sourced {group} weightage ({weight*100:.1f}%) across {len(group_topics)} topics — not yet individually reviewed for which topics matter most within the group.",
                })
    return rows


def push(rows):
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()
    if not url or not key:
        print(f"SUPABASE_URL/SUPABASE_KEY not set — built {len(rows)} rows, nothing pushed")
        return 0
    saved = 0
    for i in range(0, len(rows), 50):
        batch = rows[i:i + 50]
        r = requests.post(
            f"{url}/rest/v1/exam_syllabus_map",
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
    rows = build_rows()
    print(f"Built {len(rows)} exam_syllabus_map rows across {len(EXAM_PROFILES)} exams (the 5 with sourced subject-group weightage).")
    by_exam = {}
    for r in rows:
        by_exam[r["exam_id"]] = by_exam.get(r["exam_id"], 0) + 1
    for exam_id, count in by_exam.items():
        print(f"  {exam_id}: {count} rows")
    saved = push(rows)
    print(f"Pushed {saved}/{len(rows)} to Supabase")
    print()
    print("NOT covered (need dedicated subject-group-split research before they")
    print("can get real syllabus_map rows): cat_mba, xat, ugc_net_jrf, csir_net, cuet_pg")

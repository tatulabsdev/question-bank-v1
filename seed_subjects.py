
"""
TryIT Question Engine — Subject Seeder
==========================================
Populates the `subjects` table. This table was previously never created
or populated anywhere in the codebase, even though supabase_data.py reads
from it and pipeline.py calls fetch_subjects() on every single run — on
a fresh Supabase project this would crash the pipeline immediately with
a 404/"relation does not exist" error before a single question got
generated.

Two kinds of rows:
  1. Four UMBRELLA PARENTS (maths, english, reasoning, general_knowledge)
     — display-grouping only, per seed_topics.py's own docstring
     ("Only LEAF subjects get topics ... umbrella parents for display
     grouping"). These have parent_id = None.
  2. The 40 LEAF subjects that seed_topics.py's SUBJECT_TOPICS actually
     attaches topics to. Each leaf's parent_id points at one of the 4
     umbrellas where applicable, or stays None for standalone leaves
     (physics, chemistry, history, accountancy, etc. — these don't
     nest under any umbrella today).

ASSUMPTION — `stream` grouping (general/science/arts/commerce/law/
professional/language) is not defined anywhere else in the codebase, so
this is a first-pass default grouping for filtering/display purposes.
Confirm/adjust these against your own product taxonomy before treating
them as final — they don't affect question generation itself (only
questions.subject_id / topics.subject_id do that), just how subjects
might get grouped in a UI.
"""

import os
import requests

REQUEST_TIMEOUT = 30

# ──────────────────────────────────────────────────────────
# UMBRELLA PARENTS — display grouping only, no topics attach directly
# ──────────────────────────────────────────────────────────
UMBRELLA_PARENTS = {
    "maths":             ("Mathematics", "general"),
    "english":           ("English", "general"),
    "reasoning":         ("Reasoning", "general"),
    "general_knowledge": ("General Knowledge", "general"),
}

# ──────────────────────────────────────────────────────────
# LEAF SUBJECTS — subject_id -> (subject_name, parent_id_or_None, stream)
# subject_id values match SUBJECT_TOPICS keys in seed_topics.py exactly —
# this list is NOT auto-derived from there on purpose, so a change to
# seed_topics.py doesn't silently rename/reparent a subject in prod
# without a deliberate matching edit here.
# ──────────────────────────────────────────────────────────
LEAF_SUBJECTS = {
    "maths_arithmetic":   ("Arithmetic", "maths", "general"),
    "maths_algebra":      ("Algebra", "maths", "general"),
    "maths_geometry":     ("Geometry", "maths", "general"),
    "maths_trigonometry": ("Trigonometry", "maths", "general"),
    "maths_stats":        ("Statistics", "maths", "general"),
    "data_interpretation":("Data Interpretation", "maths", "general"),
    "maths_calculus":     ("Calculus", "maths", "science"),

    "reasoning_verbal":    ("Verbal Reasoning", "reasoning", "general"),
    "reasoning_nonverbal": ("Non-Verbal Reasoning", "reasoning", "general"),
    "reasoning_critical":  ("Critical Reasoning", "reasoning", "general"),

    "english_grammar": ("English Grammar", "english", "general"),
    "english_vocab":   ("English Vocabulary", "english", "general"),
    "english_reading": ("English Reading Comprehension", "english", "general"),
    "english_writing": ("English Writing", "english", "general"),

    "gk_history":      ("History (GK)", "general_knowledge", "general"),
    "gk_polity":       ("Polity (GK)", "general_knowledge", "general"),
    "gk_geography":    ("Geography (GK)", "general_knowledge", "general"),
    "gk_economy":      ("Economy (GK)", "general_knowledge", "general"),
    "gk_science":      ("Science (GK)", "general_knowledge", "general"),
    "gk_sports":       ("Sports (GK)", "general_knowledge", "general"),
    "gk_awards":       ("Awards and Honours (GK)", "general_knowledge", "general"),
    "gk_india":        ("India Static GK", "general_knowledge", "general"),
    "current_affairs": ("Current Affairs", "general_knowledge", "general"),

    "physics":    ("Physics", None, "science"),
    "chemistry":  ("Chemistry", None, "science"),
    "biology":    ("Biology", None, "science"),
    "science_gen":("General Science", None, "science"),
    "computer":   ("Computer Science", None, "science"),
    "environment":("Environmental Science", None, "science"),

    "history":   ("History (Detailed)", None, "arts"),
    "geography": ("Geography (Detailed)", None, "arts"),
    "polity":    ("Polity (Detailed)", None, "arts"),
    "economy":   ("Economy (Detailed)", None, "arts"),

    "accountancy":     ("Accountancy", None, "commerce"),
    "management_sub":  ("Management", None, "commerce"),
    "law_sub":         ("Law", None, "law"),
    "agriculture_sub": ("Agriculture", None, "professional"),
    "engineering_sub": ("Engineering", None, "professional"),
    "hindi":           ("Hindi", None, "language"),
    "regional_lang":   ("Regional Languages", None, "language"),
}


def build_subject_rows():
    rows = []
    for subject_id, (name, stream) in UMBRELLA_PARENTS.items():
        rows.append({
            "subject_id": subject_id,
            "subject_name": name,
            "parent_id": None,
            "stream": stream,
        })
    for subject_id, (name, parent_id, stream) in LEAF_SUBJECTS.items():
        rows.append({
            "subject_id": subject_id,
            "subject_name": name,
            "parent_id": parent_id,
            "stream": stream,
        })
    return rows


def push_subjects(rows, batch_size=50):
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()
    if not url or not key:
        print("SUPABASE_URL/SUPABASE_KEY not set — nothing pushed")
        return 0

    saved = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        r = requests.post(
            f"{url}/rest/v1/subjects",
            headers={"apikey": key, "Authorization": f"Bearer {key}",
                     "Content-Type": "application/json", "Prefer": "return=minimal"},
            json=batch, timeout=REQUEST_TIMEOUT,
        )
        if r.status_code in (200, 201):
            saved += len(batch)
        else:
            print(f"  error {r.status_code}: {r.text[:200]}")
    return saved


if __name__ == "__main__":
    rows = build_subject_rows()
    print(f"Built {len(rows)} subjects "
          f"({len(UMBRELLA_PARENTS)} umbrella parents + {len(LEAF_SUBJECTS)} leaves)")
    saved = push_subjects(rows)
    print(f"Pushed {saved}/{len(rows)} to Supabase")

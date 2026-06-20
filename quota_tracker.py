"""
TryIT Question Engine — Quota Tracker
========================================
Before generating anything, this asks Supabase "how many verified
questions do we already have for each topic+level?" and compares that
against the tier floor (30k/20k/10k). It then builds today's job list,
crowded topics first, skipping anything that's already hit its floor.

This avoids keeping a separate progress file that could drift out of
sync with what's actually saved — Supabase's own count is the source
of truth.
"""

import os
import requests

from config import TOPICS, TIER_QUOTAS, GENERATION_ORDER

REQUEST_TIMEOUT = 30


def _supabase_conf():
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()
    return url, key


def get_current_count(topic_id: str, level: int) -> int:
    """Returns how many verified questions already exist for this
    topic+level. Returns -1 if Supabase isn't reachable (caller should
    treat -1 as 'unknown, proceed cautiously' rather than 'zero')."""
    url, key = _supabase_conf()
    if not url or not key:
        return -1
    try:
        r = requests.get(
            f"{url}/rest/v1/questions",
            headers={
                "apikey": key, "Authorization": f"Bearer {key}",
                "Prefer": "count=exact",
            },
            params={
                "topic_id": f"eq.{topic_id}",
                "level": f"eq.{level}",
                "verified": "eq.true",
                "select": "id",
                "limit": 1,
            },
            timeout=REQUEST_TIMEOUT,
        )
        if r.status_code in (200, 206):
            content_range = r.headers.get("Content-Range", "")
            if "/" in content_range:
                total = content_range.split("/")[-1]
                if total.isdigit():
                    return int(total)
        return -1
    except requests.RequestException:
        return -1


def build_today_jobs(questions_per_job: int = 15, max_jobs: int = None) -> list:
    """Returns a list of (topic_id, level, count_to_generate) tuples,
    crowded tier first, skipping topic+level cells that already meet
    their tier floor. `max_jobs` caps the list length (use this to keep
    a single GitHub Actions run within its time budget — see
    daily_generation.yml for how this is chunked across runs)."""
    jobs = []

    for tier in GENERATION_ORDER:  # crowded, medium, niche — locked order
        floor = TIER_QUOTAS[tier]
        topics_in_tier = {tid: t for tid, t in TOPICS.items() if t["tier"] == tier}

        for topic_id, meta in topics_in_tier.items():
            if not meta.get("auto_generate", True):
                continue  # paused topic — e.g. needs a diagram check we don't have yet
            levels = meta["levels"]
            # split the floor evenly across this topic's applicable levels
            per_level_floor = max(floor // len(levels), questions_per_job)

            for level in levels:
                current = get_current_count(topic_id, level)
                if current == -1:
                    # Supabase unreachable — generate a conservative single
                    # job rather than skipping the topic entirely or assuming
                    # zero and over-generating.
                    jobs.append((topic_id, level, questions_per_job))
                    continue
                remaining = per_level_floor - current
                if remaining <= 0:
                    continue  # floor already met for this topic+level
                jobs.append((topic_id, level, min(remaining, questions_per_job)))

    if max_jobs:
        jobs = jobs[:max_jobs]
    return jobs


def progress_report() -> str:
    """Human-readable summary of floor progress per tier — useful to
    print at the start/end of each run so you can see where things stand
    without opening Supabase."""
    lines = []
    for tier in GENERATION_ORDER:
        floor = TIER_QUOTAS[tier]
        topics_in_tier = {tid: t for tid, t in TOPICS.items() if t["tier"] == tier}
        lines.append(f"\n--- {tier.upper()} tier (floor: {floor:,} per topic) ---")
        for topic_id, meta in topics_in_tier.items():
            if not meta.get("auto_generate", True):
                lines.append(f"  {topic_id:40s} PAUSED — {meta.get('auto_generate_note', 'auto_generate=False')}")
                continue
            total = 0
            unreachable = False
            for level in meta["levels"]:
                c = get_current_count(topic_id, level)
                if c == -1:
                    unreachable = True
                else:
                    total += c
            status = "?" if unreachable else f"{total:,}/{floor:,}"
            lines.append(f"  {topic_id:40s} {status}")
    return "\n".join(lines)

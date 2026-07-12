#!/usr/bin/env bash
# Run this from the ROOT of your question-bank-v1 repo in the Codespaces terminal:
#   bash apply_fixes.sh
# It overwrites the 4 fixed files in place. Safe to re-run.
set -e

cat > schema.sql << 'TRYIT_EOF'
-- Run this once in Supabase: Dashboard -> SQL Editor -> New query -> paste -> Run
-- FIXED: previous version's column names (subject, chapter, topic, tier,
-- diagram_required, diagram, exam_mapping) did NOT match the keys
-- pipeline.py's to_final_record() actually produces. PostgREST rejects
-- inserts containing unknown JSON keys, so every push_to_supabase() call
-- was silently failing (logged as a 400 error, run continued anyway).
-- This version's columns are a 1:1 match with to_final_record()'s dict keys.

create table if not exists questions (
  id                  text primary key,
  topic_id            text not null,
  subject_id          text,
  level               int,
  difficulty          text,        -- "Easy" | "Medium" | "Hard" | "Expert"
  pattern_type        text,        -- e.g. "standalone_mcq4"
  question_en         text,
  options_en          jsonb,
  correct_answer      int,
  explanation         jsonb,       -- the 7-layer explanation object
  translations        jsonb default '{}'::jsonb,
  exam_tags           jsonb default '[]'::jsonb,
  has_visual          boolean default false,
  visual_type         text,        -- diagram_kind, e.g. "geometry_svg"
  visual_data         jsonb,
  access_tier         text,        -- "free" | "pro"
  copyright_original  boolean default true,
  verified            boolean default true,
  quality_score       numeric,
  report_count        int default 0,
  generated_by        text,        -- e.g. "tryit_engine:call_cerebras"
  created_at          timestamptz default now()
);

-- Speeds up the quota_tracker's per-topic-per-level count checks, which
-- run before every generation job.
create index if not exists idx_questions_topic_level on questions (topic_id, level);

-- Useful for B2B/B2G exports and exam-pattern filtering at scale.
create index if not exists idx_questions_access_tier on questions (access_tier);
create index if not exists idx_questions_exam_tags on questions using gin (exam_tags);

-- Row Level Security is on by default for new Supabase projects. The
-- pipeline writes with the SERVICE ROLE key (not the anon/public key),
-- which bypasses RLS automatically — so no policy is required for the
-- pipeline itself to work. If you also want your TryIT app's frontend to
-- READ questions using the public anon key, uncomment and adjust this:

-- alter table questions enable row level security;
-- create policy "Public read access" on questions
--   for select using (true);
TRYIT_EOF
echo "wrote schema.sql"

cat > providers.py << 'TRYIT_EOF'

"""
TryIT Question Engine — Providers
====================================
Thin wrapper around several free-tier LLM providers, with automatic
failover (try the next provider if one is rate-limited) and exponential
backoff. All keys come from environment variables / GitHub Secrets —
NEVER hardcode a key in this file, this repo is public.

Required environment variables (set these as GitHub Secrets):
  CEREBRAS_API_KEY
  GROQ_API_KEY
  GEMINI_API_KEY
  OPENROUTER_API_KEY
  MISTRAL_API_KEY

Any of these can be left unset — the failover chain just skips providers
with no key configured. At least ONE must be set for anything to work.
"""

import os
import time
import json
import random
import requests

from config import PROVIDER_MODELS

REQUEST_TIMEOUT = 60
MAX_RETRIES_PER_PROVIDER = 2


def _env(name):
    return os.environ.get(name, "").strip()


# ──────────────────────────────────────────────────────────
# Individual provider callers. Each returns (text_or_None, status_string).
# status_string is one of: "ok", "rate_limit", "auth_error", "error"
# ──────────────────────────────────────────────────────────

def call_cerebras(prompt, model=None):
    key = _env("CEREBRAS_API_KEY")
    if not key:
        return None, "no_key"
    model = model or PROVIDER_MODELS["cerebras"]
    try:
        r = requests.post(
            "https://api.cerebras.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.7, "max_tokens": 12000},
            timeout=REQUEST_TIMEOUT,
        )
        return _handle_openai_style_response(r)
    except requests.RequestException as e:
        return None, f"error:{e}"


def call_groq(prompt, model=None):
    key = _env("GROQ_API_KEY")
    if not key:
        return None, "no_key"
    model = model or PROVIDER_MODELS["groq_fast"]
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.7, "max_tokens": 12000},
            timeout=REQUEST_TIMEOUT,
        )
        return _handle_openai_style_response(r)
    except requests.RequestException as e:
        return None, f"error:{e}"


def call_gemini(prompt, model=None):
    key = _env("GEMINI_API_KEY")
    if not key:
        return None, "no_key"
    model = model or PROVIDER_MODELS["gemini"]
    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=REQUEST_TIMEOUT,
        )
        if r.status_code == 429:
            return None, "rate_limit"
        if r.status_code in (401, 403):
            return None, "auth_error"
        if r.status_code != 200:
            return None, f"error:{r.status_code}"
        data = r.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return text, "ok"
    except (requests.RequestException, KeyError, IndexError) as e:
        return None, f"error:{e}"


def call_openrouter(prompt, model=None):
    key = _env("OPENROUTER_API_KEY")
    if not key:
        return None, "no_key"
    model = model or PROVIDER_MODELS["openrouter"]
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.7, "max_tokens": 12000},
            timeout=REQUEST_TIMEOUT,
        )
        return _handle_openai_style_response(r)
    except requests.RequestException as e:
        return None, f"error:{e}"


def call_mistral(prompt, model=None):
    key = _env("MISTRAL_API_KEY")
    if not key:
        return None, "no_key"
    model = model or PROVIDER_MODELS["mistral"]
    try:
        r = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.7, "max_tokens": 12000},
            timeout=REQUEST_TIMEOUT,
        )
        return _handle_openai_style_response(r)
    except requests.RequestException as e:
        return None, f"error:{e}"


def _handle_openai_style_response(r):
    if r.status_code == 429:
        return None, "rate_limit"
    if r.status_code in (401, 403):
        return None, "auth_error"
    if r.status_code != 200:
        return None, f"error:{r.status_code}:{r.text[:150]}"
    try:
        data = r.json()
        return data["choices"][0]["message"]["content"], "ok"
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        return None, f"error:parse:{e}"


# ──────────────────────────────────────────────────────────
# FAILOVER CHAINS — order matters. Generation favors high-volume free
# providers; verification favors stronger-reasoning models.
# ──────────────────────────────────────────────────────────
GENERATION_CHAIN = [call_cerebras, call_groq, call_openrouter, call_mistral]
VERIFICATION_CHAIN_1 = [call_groq, call_cerebras]          # uses groq_strong model, see call_with_failover
VERIFICATION_CHAIN_2 = [call_gemini, call_mistral, call_openrouter]
TRANSLATION_CHAIN = [call_mistral, call_cerebras, call_groq, call_openrouter]


def call_with_failover(prompt, chain, model_override=None, label="call"):
    """Try each provider in order. On rate_limit/auth_error/error, back off
    briefly and move to the next provider. Returns (text, provider_name) or
    (None, None) if every provider in the chain failed.

    NOTE: model_override is provider-specific (e.g. a Groq model id isn't a
    valid Cerebras model id), so it must ONLY be applied to the first
    provider in the chain — never carried over to the fallback providers
    that follow it, or they'll get called with a model name that doesn't
    exist on their platform."""
    for attempt, fn in enumerate(chain):
        use_override = model_override if attempt == 0 else None
        for retry in range(MAX_RETRIES_PER_PROVIDER):
            text, status = fn(prompt, use_override) if use_override else fn(prompt)
            if status == "ok" and text:
                return text, fn.__name__
            if status == "no_key":
                break  # don't retry a provider with no key configured, just skip it
            if status == "rate_limit":
                backoff = (2 ** retry) + random.uniform(0, 1)
                time.sleep(backoff)
                continue
            if status == "auth_error":
                print(f"  [{label}] {fn.__name__} auth error — check the API key secret")
                break
            # generic error — one quick retry then move on
            time.sleep(1)
    return None, None
TRYIT_EOF
echo "wrote providers.py"

cat > quota_tracker.py << 'TRYIT_EOF'

"""
TryIT Question Engine — Quota Tracker
========================================
Reads real topic quotas straight from Supabase: each topic row already
has question_target (the floor) and questions_available (the live
count, auto-maintained by the database per your confirmation). No more
guessed crowded/medium/niche tiers — topics are processed in
coverage_score order, which seed_topics.py set from real exam-section
frequency data, not a guess.
"""

from config import levels_from_difficulty_range
from supabase_data import fetch_topics


def build_today_jobs(questions_per_job: int = 10, max_jobs: int = None) -> list:
    """Returns a list of (topic_id, level, count_to_generate) tuples,
    highest coverage_score first, skipping any topic+level cell that's
    already met its question_target."""
    jobs = []
    topics = fetch_topics()  # already ordered by coverage_score desc

    for topic in topics:
        topic_id = topic["topic_id"]
        target = topic.get("question_target") or 0
        available = topic.get("questions_available") or 0
        if target <= 0:
            continue

        levels = levels_from_difficulty_range(topic.get("difficulty_range", ""))

        # questions_available is a topic-level total (not per-level), so
        # split the remaining work evenly across this topic's levels —
        # an approximation, since the database doesn't track progress
        # per-level, only per-topic.
        remaining_total = target - available
        if remaining_total <= 0:
            continue

        # Distribute remaining_total across levels using ceiling division
        # rather than floor division — floor division rounds small
        # remainders (e.g. remaining_total=3, len(levels)=5) down to 0 for
        # every level, which would silently stall a topic forever right
        # before it hits its target. Ceiling division guarantees any
        # nonzero remainder still produces at least one job.
        num_levels = len(levels)
        remaining_per_level = -(-remaining_total // num_levels)  # ceil

        for level in levels:
            count = min(remaining_per_level, questions_per_job)
            if count <= 0:
                continue
            jobs.append((topic_id, level, count))

    if max_jobs:
        jobs = jobs[:max_jobs]
    return jobs


def progress_report() -> str:
    """Human-readable summary of floor progress, highest-priority topics first."""
    lines = []
    topics = fetch_topics()
    for topic in topics:
        target = topic.get("question_target") or 0
        available = topic.get("questions_available") or 0
        pct = (available / target * 100) if target else 0
        lines.append(f"  {topic['topic_id']:45s} {available:>6}/{target:<6} ({pct:5.1f}%)  coverage={topic.get('coverage_score')}")
    return "\n".join(lines)
TRYIT_EOF
echo "wrote quota_tracker.py"

cat > config.py << 'TRYIT_EOF'

"""
TryIT Question Engine — Configuration
=======================================
Topics and subjects now live in your real Supabase tables (seeded by
seed_topics.py) — this file no longer hand-types them. What's left here:
the difficulty level scale, provider model defaults, and a small
topic_id -> diagram_kind lookup for the visual topics (since "which kind
of diagram" isn't a real column in the topics table — only is_visual is;
the specific kind comes from the same source seed_topics.py used).
"""

from seed_topics import SUBJECT_TOPICS

# ──────────────────────────────────────────────────────────
# DIFFICULTY LEVELS — unchanged from before, still the right scale
# ──────────────────────────────────────────────────────────
LEVELS = {
    1:  "LKG-UKG, picture-based, very simple",
    2:  "Class 1-4, basic operations",
    3:  "Class 5-7 (includes 6th standard), foundation concepts",
    4:  "Class 8-10, intermediate school",
    5:  "Class 11-12, advanced school",
    6:  "Graduate / foundation competitive level",
    7:  "SSC, Banking, Railways, TNPSC, State PSC — core competitive level",
    8:  "Professional: GATE, CAT, CLAT, NEET, JEE Advanced",
    9:  "UPSC Prelims / State PSC Mains / PG entrance",
    10: "UPSC Mains advanced, PhD entrance, research level",
}


def difficulty_label_for_level(level: int) -> str:
    """Maps the integer level scale to the text `difficulty` column your
    real questions table expects. Assumption — confirm this matches your
    actual convention if you have one already in use elsewhere."""
    if level <= 3:
        return "Easy"
    if level <= 6:
        return "Medium"
    if level <= 8:
        return "Hard"
    return "Expert"


def levels_from_difficulty_range(difficulty_range: str) -> list:
    """Parses a topics.difficulty_range string like '2-7' into [2,3,4,5,6,7].
    Falls back to a safe single mid-level if the format is unexpected,
    rather than crashing a whole job on one malformed row."""
    try:
        lo, hi = difficulty_range.split("-")
        lo, hi = int(lo), int(hi)
        return list(range(lo, hi + 1))
    except (ValueError, AttributeError):
        return [6]


# ──────────────────────────────────────────────────────────
# DIAGRAM KIND LOOKUP — derived from seed_topics.py, the same source that
# set is_visual on the real topics rows, so the two can't drift apart.
# ──────────────────────────────────────────────────────────
def _build_diagram_kind_lookup():
    lookup = {}
    for subject_id, (tier, topics) in SUBJECT_TOPICS.items():
        for topic_name, is_visual, diagram_kind, is_headline in topics:
            if not is_visual:
                continue
            slug = (
                topic_name.lower()
                .replace(",", "").replace("(", "").replace(")", "")
                .replace("/", "_").replace("-", "_").replace(" ", "_")
            )
            topic_id = f"{subject_id}_{slug}"
            lookup[topic_id] = diagram_kind
    return lookup


DIAGRAM_KIND_BY_TOPIC_ID = _build_diagram_kind_lookup()

# ──────────────────────────────────────────────────────────
# PROVIDER MODEL DEFAULTS
# ──────────────────────────────────────────────────────────
PROVIDER_MODELS = {
    "cerebras":   "gpt-oss-120b",
    "groq_fast":  "llama-3.1-8b-instant",
    "groq_strong":"llama-3.3-70b-versatile",
    "gemini":     "gemini-2.5-flash",
    "openrouter": "meta-llama/llama-3.3-70b-instruct:free",
    "mistral":    "mistral-small-latest",
}

QUALITY_SCORE_THRESHOLD = 7  # out of 10
JSON_BATCH_SIZE = 300        # questions per output JSON file
def access_tier_for_level(level: int) -> str:
    """Free tier: Easy/Medium (levels 1-6) — PYQ-based practice plus
    AI-generated questions at this range. Hard/Expert (levels 7-10)
    require Pro or Ultra subscription. Ultra is a superset of Pro, so
    "pro" is the correct minimum tier to write here — Ultra subscribers
    get access to anything Pro does automatically on the app side."""
    return "free" if level <= 6 else "pro"
DEFAULT_PATTERN_TYPE = "standalone_mcq4"  # assumption — adjust per topic/exam pattern as needed

# ──────────────────────────────────────────────────────────
# INDIAN STATES / UTS — canonical list used by diagrams.py's
# validate_map_region() to check the model named a real region. This was
# referenced but never defined, which would have raised a NameError the
# first time a topic used diagram_kind == "map_region" (currently no
# topic in seed_topics.py does — this is here so it doesn't crash later).
# ──────────────────────────────────────────────────────────
INDIAN_STATES_UTS = {
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
    "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim",
    "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
    "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Jammu and Kashmir",
    "Ladakh", "Lakshadweep", "Puducherry",
}
TRYIT_EOF
echo "wrote config.py"

echo "Done. Run: python3 -m py_compile providers.py quota_tracker.py config.py"

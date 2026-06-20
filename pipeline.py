"""
TryIT Question Engine — Main Pipeline
========================================
Run this file. It pulls today's job list from quota_tracker (crowded
topics first), and for each job: generates -> parses -> decency-checks
-> dedup-checks -> verifies with two independent models -> writes a
local JSON batch file -> pushes the verified rows to Supabase.

Usage:
    python pipeline.py                  # run the full crowded-first queue
    python pipeline.py --max-jobs 5     # just a handful, for testing
    python pipeline.py --report         # print quota progress and exit
    python pipeline.py --dry-run        # generate+verify but don't push to Supabase
"""

import os
import sys
import json
import time
import uuid
import argparse
from datetime import datetime, timezone

import requests

from config import (
    TOPICS, EXAMS, LEVELS, PROVIDER_MODELS,
    QUALITY_SCORE_THRESHOLD, JSON_BATCH_SIZE,
)
from content_rules import (
    COPYRIGHT_INSTRUCTION, build_explanation_prompt_block, DECENCY_RULES,
    PROFANITY_TRIPWIRE_EN,
)
from diagrams import diagram_instruction_for, validate_diagram
import geometry_engine
from providers import (
    call_with_failover, GENERATION_CHAIN, VERIFICATION_CHAIN_1,
    VERIFICATION_CHAIN_2,
)
from dedup import filter_duplicates
from quota_tracker import build_today_jobs, progress_report

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
PENDING_REVIEW_PATH = os.path.join(OUTPUT_DIR, "pending_review.jsonl")


# ──────────────────────────────────────────────────────────
# STAGE A — GENERATION
# ──────────────────────────────────────────────────────────
def build_generation_prompt(topic_id: str, level: int, count: int) -> str:
    meta = TOPICS[topic_id]
    level_desc = LEVELS.get(level, "competitive level")
    exam_list = ", ".join(meta["exam_tags"])

    diagram_block = ""
    if meta.get("diagram_required") and meta.get("auto_generate", True):
        diagram_block = "\n" + diagram_instruction_for(meta["diagram_kind"]) + "\n"

    return f"""You are an expert Indian competitive exam question writer.

SUBJECT: {meta['subject']} | CHAPTER: {meta['chapter']} | TOPIC: {meta['topic']}
DIFFICULTY LEVEL: {level} ({level_desc})
RELEVANT EXAMS: {exam_list}
NUMBER OF QUESTIONS: {count}

{COPYRIGHT_INSTRUCTION}

{DECENCY_RULES}

FORMAT: Standard MCQ with exactly 4 options (A, B, C, D), only one correct.

{build_explanation_prompt_block()}
{diagram_block}
Return ONLY a JSON array, no markdown fences, no commentary. Each item:
{{
  "question": "...",
  "options": ["A text", "B text", "C text", "D text"],
  "correct_answer": 0,
  "why_correct": "...",
  "why_wrong_option_b": "...",
  "why_wrong_option_c": "...",
  "why_wrong_option_d": "...",
  "story_explanation": "...",
  "shortcut_tips": "...",
  "cross_exam_intelligence": "..."
}}
{"Also include the diagram fields described above in EVERY item — a question in this topic without its diagram is incomplete and will be rejected." if diagram_block else ""}
"""


def generate_batch(topic_id: str, level: int, count: int):
    prompt = build_generation_prompt(topic_id, level, count)
    text, provider = call_with_failover(prompt, GENERATION_CHAIN, label=f"generate:{topic_id}:L{level}")
    return text, provider


# ──────────────────────────────────────────────────────────
# GEOMETRY-FIRST PATH — paper folding & embedded figures
# Code constructs the geometry (and therefore the correct answer) FIRST.
# The LLM is only asked to write question text and explanations around
# a scenario whose answer is already fixed — it never invents geometry,
# so there's nothing for it to get wrong on the visual/correctness side.
# ──────────────────────────────────────────────────────────
GEOMETRY_GENERATORS = {
    "paper_fold": geometry_engine.generate_paper_fold_geometry,
    "embedded_figure": geometry_engine.generate_embedded_figure_geometry,
}


def build_geometry_first_prompt(topic_id: str, level: int, scenarios: list) -> str:
    meta = TOPICS[topic_id]
    level_desc = LEVELS.get(level, "competitive level")
    items_desc = "\n".join(
        f"{i + 1}. {s['scenario_text']} The correct option is option "
        f"{s['correct_letter']} — this is FIXED, do not contradict it or "
        f"invent different reasoning."
        for i, s in enumerate(scenarios)
    )

    return f"""You are an expert Indian competitive exam question writer.

SUBJECT: {meta['subject']} | CHAPTER: {meta['chapter']} | TOPIC: {meta['topic']}
DIFFICULTY LEVEL: {level} ({level_desc})

{COPYRIGHT_INSTRUCTION}

{DECENCY_RULES}

The diagrams for these questions are ALREADY BUILT and already correct —
your only job is the question stem and explanation text. Do not describe,
redraw, or second-guess the geometry; just write around it.

{build_explanation_prompt_block()}

SCENARIOS:
{items_desc}

Return ONLY a JSON array of {len(scenarios)} objects, in the same order,
each with exactly these fields (no "options" or "correct_answer" — those
are already fixed):
{{
  "question": "...",
  "why_correct": "...",
  "why_wrong_option_b": "...",
  "why_wrong_option_c": "...",
  "why_wrong_option_d": "...",
  "story_explanation": "...",
  "shortcut_tips": "...",
  "cross_exam_intelligence": "..."
}}
"""


def generate_geometry_first_batch(topic_id: str, level: int, count: int):
    """Builds `count` geometry scenarios with code (correct answer fixed
    by construction), then makes ONE batched LLM call for just the text
    fields, and merges them back together. Returns a list of merged
    question dicts ready for the decency/dedup/diagram-gate stages."""
    meta = TOPICS[topic_id]
    generator_fn = GEOMETRY_GENERATORS[meta["diagram_kind"]]

    geometries = [generator_fn() for _ in range(count)]
    scenarios = [
        {"scenario_text": g["scenario_text"], "correct_letter": "ABCD"[g["correct_answer"]]}
        for g in geometries
    ]

    prompt = build_geometry_first_prompt(topic_id, level, scenarios)
    text, provider = call_with_failover(prompt, GENERATION_CHAIN, label=f"geo-generate:{topic_id}:L{level}")
    if not text:
        return [], None

    text_items = parse_questions(text)
    if len(text_items) != len(geometries):
        # Model didn't return one item per scenario — keep whatever pairs
        # we can match positionally, drop the rest rather than guess.
        n = min(len(text_items), len(geometries))
        text_items, geometries = text_items[:n], geometries[:n]

    merged = []
    for text_fields, geom in zip(text_items, geometries):
        q = dict(text_fields)
        q["options"] = ["Option A", "Option B", "Option C", "Option D"]
        q["correct_answer"] = geom["correct_answer"]  # forced by construction, not by the LLM
        q["diagram_svg"] = geom["diagram_svg"]
        q["option_svgs"] = geom["option_svgs"]
        q["diagram_meta"] = geom["diagram_meta"]
        merged.append(q)
    return merged, provider


def parse_questions(raw_text: str):
    """Extracts a JSON array from a model response, tolerating markdown
    fences and stray text before/after the array."""
    if not raw_text:
        return []
    text = raw_text.strip()
    text = text.replace("```json", "").replace("```", "")
    start = text.find("[")
    end = text.rfind("]") + 1
    if start == -1 or end <= start:
        return []
    try:
        result = json.loads(text[start:end])
        return result if isinstance(result, list) else []
    except json.JSONDecodeError:
        return []


# ──────────────────────────────────────────────────────────
# STAGE B — DECENCY / SAFETY CHECK (fast keyword pass)
# Real protection is the AI verification stage below asking the model
# directly; this is just a cheap tripwire that costs no API call.
# ──────────────────────────────────────────────────────────
def decency_tripwire(question: dict) -> bool:
    """Returns True if the question looks SAFE (passes), False if it
    should be dropped/flagged."""
    blob = json.dumps(question).lower()
    return not any(bad in blob for bad in PROFANITY_TRIPWIRE_EN)


# ──────────────────────────────────────────────────────────
# STAGE C — VERIFICATION (two independent models, not one)
# ──────────────────────────────────────────────────────────
def build_verification_prompt(question: dict) -> str:
    return f"""Check this exam question for correctness and quality.

QUESTION: {question.get('question')}
OPTIONS: {question.get('options')}
MARKED CORRECT ANSWER (0-indexed): {question.get('correct_answer')}

Respond with ONLY a JSON object, no commentary:
{{
  "answer_is_correct": true or false,
  "factual_error_found": true or false,
  "quality_score": 1-10,
  "reason": "one short sentence"
}}

Score 1-10 based on: clarity (2pts), plausibility of wrong options (2pts),
explanation quality (2pts), cultural relevance (2pts), uniqueness (2pts).
"""


def verify_question(question: dict):
    """Runs two independent verification calls. Returns
    (passed: bool, quality_score: int, needs_human_review: bool)."""
    prompt = build_verification_prompt(question)

    text1, _ = call_with_failover(prompt, VERIFICATION_CHAIN_1,
                                   model_override=PROVIDER_MODELS["groq_strong"],
                                   label="verify1")
    text2, _ = call_with_failover(prompt, VERIFICATION_CHAIN_2, label="verify2")

    result1 = _parse_verification(text1)
    result2 = _parse_verification(text2)

    votes_correct = sum(1 for r in (result1, result2) if r and r.get("answer_is_correct"))
    any_factual_error = any(r and r.get("factual_error_found") for r in (result1, result2) if r)
    scores = [r["quality_score"] for r in (result1, result2) if r and isinstance(r.get("quality_score"), (int, float))]
    avg_score = sum(scores) / len(scores) if scores else 0

    if any_factual_error:
        return False, avg_score, False  # straight reject, not worth a human review slot

    if votes_correct == 2:
        passed = avg_score >= QUALITY_SCORE_THRESHOLD
        return passed, avg_score, False
    if votes_correct == 1:
        # verifiers disagree — route to human review instead of auto-deciding
        return False, avg_score, True
    return False, avg_score, False  # 0/2 — reject


def _parse_verification(text):
    if not text:
        return None
    text = text.strip().replace("```json", "").replace("```", "")
    start, end = text.find("{"), text.rfind("}") + 1
    if start == -1 or end <= start:
        return None
    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError:
        return None


# ──────────────────────────────────────────────────────────
# STAGE D — OUTPUT (local JSON batches + Supabase push)
# ──────────────────────────────────────────────────────────
def to_final_record(question: dict, topic_id: str, level: int) -> dict:
    meta = TOPICS[topic_id]
    exam_mapping = {}
    for exam_id in meta["exam_tags"]:
        exam_meta = EXAMS.get(exam_id, {})
        exam_mapping[exam_id] = {
            "pattern": exam_meta.get("pattern", "standalone_mcq4"),
            "negative_marking": exam_meta.get("negative_marking"),
            "time_allowed_seconds": exam_meta.get("time_per_q_sec"),
        }

    diagram_kind = meta.get("diagram_kind")
    diagram_payload = None
    if diagram_kind == "chart_data":
        diagram_payload = {"kind": "chart_data", "data": question.get("chart_data")}
    elif diagram_kind == "geometry_svg":
        diagram_payload = {
            "kind": "geometry_svg",
            "svg": question.get("diagram_svg"),
            "meta": question.get("diagram_meta"),
        }
    elif diagram_kind == "nonverbal_mirror_svg":
        diagram_payload = {
            "kind": "nonverbal_mirror_svg",
            "original_svg": question.get("original_svg"),
            "option_svgs": question.get("option_svgs"),
        }
    elif diagram_kind in ("paper_fold", "embedded_figure"):
        diagram_payload = {
            "kind": diagram_kind,
            "diagram_svg": question.get("diagram_svg"),   # the "before" figure shown with the question
            "option_svgs": question.get("option_svgs"),   # the 4 answer-choice figures
            "meta": question.get("diagram_meta"),
        }
    elif diagram_kind == "map_region":
        diagram_payload = {"kind": "map_region", "map_data": question.get("map_data")}

    return {
        "id": f"q_{uuid.uuid4().hex[:16]}",
        "created": datetime.now(timezone.utc).isoformat(),
        "topic_id": topic_id,
        "subject": meta["subject"],
        "chapter": meta["chapter"],
        "topic": meta["topic"],
        "level": level,
        "tier": meta["tier"],
        "question_en": question.get("question", ""),
        "options_en": question.get("options", []),
        "correct_answer": question.get("correct_answer", 0),
        "explanation": {
            "why_correct": question.get("why_correct", ""),
            "why_wrong_option_b": question.get("why_wrong_option_b", ""),
            "why_wrong_option_c": question.get("why_wrong_option_c", ""),
            "why_wrong_option_d": question.get("why_wrong_option_d", ""),
            "story_explanation": question.get("story_explanation", ""),
            "shortcut_tips": question.get("shortcut_tips", ""),
            "cross_exam_intelligence": question.get("cross_exam_intelligence", ""),
        },
        "diagram_required": meta.get("diagram_required", False),
        "diagram": diagram_payload,  # None for text-only topics; validated payload otherwise
        "exam_mapping": exam_mapping,
        "exam_tags": meta["exam_tags"],
        "verified": True,
        "quality_score": question.get("_quality_score", 0),
        "copyright_original": True,
        "translations": {},  # filled in by a separate translation pass — see README
    }


def write_json_batch(records: list, batch_label: str):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for i in range(0, len(records), JSON_BATCH_SIZE):
        chunk = records[i:i + JSON_BATCH_SIZE]
        filename = f"{batch_label}_{i // JSON_BATCH_SIZE:03d}_{uuid.uuid4().hex[:8]}.json"
        path = os.path.join(OUTPUT_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(chunk, f, ensure_ascii=False, indent=2)
        print(f"  wrote {len(chunk)} questions -> {filename}")


def push_to_supabase(records: list) -> int:
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()
    if not url or not key:
        print("  [supabase] SUPABASE_URL/SUPABASE_KEY not set — skipping push, JSON files still saved")
        return 0

    saved = 0
    for i in range(0, len(records), 50):
        batch = records[i:i + 50]
        try:
            r = requests.post(
                f"{url}/rest/v1/questions",
                headers={
                    "apikey": key, "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json", "Prefer": "return=minimal",
                },
                json=batch, timeout=30,
            )
            if r.status_code in (200, 201):
                saved += len(batch)
            else:
                print(f"  [supabase] error {r.status_code}: {r.text[:150]}")
        except requests.RequestException as e:
            print(f"  [supabase] request failed: {e}")
    return saved


def append_pending_review(question: dict, topic_id: str, level: int, reason: str):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    record = {"topic_id": topic_id, "level": level, "reason": reason, "question": question}
    with open(PENDING_REVIEW_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ──────────────────────────────────────────────────────────
# JOB PROCESSOR
# ──────────────────────────────────────────────────────────
def process_job(topic_id: str, level: int, count: int, dry_run: bool = False) -> dict:
    print(f"\n-> {topic_id} | L{level} | requesting {count}")

    meta = TOPICS[topic_id]
    is_geometry_first = meta.get("diagram_kind") in GEOMETRY_GENERATORS

    if is_geometry_first:
        questions, provider = generate_geometry_first_batch(topic_id, level, count)
        if not questions:
            print("   x geometry-first generation failed (no text returned from any provider)")
            return {"generated": 0, "verified": 0, "saved": 0}
        print(f"   generated {len(questions)} via {provider} (geometry built by code, not the LLM)")
    else:
        raw_text, provider = generate_batch(topic_id, level, count)
        if not raw_text:
            print("   x generation failed on every provider in the chain")
            return {"generated": 0, "verified": 0, "saved": 0}

        questions = parse_questions(raw_text)
        if not questions:
            print(f"   x no valid JSON parsed from {provider} response")
            return {"generated": 0, "verified": 0, "saved": 0}
        print(f"   generated {len(questions)} via {provider}")

    # decency tripwire — drop silently, don't even send these to verification
    questions = [q for q in questions if decency_tripwire(q)]

    # in-batch duplicate filter
    questions = filter_duplicates(questions, text_key="question")

    # diagram gate — if this topic requires a diagram, a question without
    # a VALID one (checked computationally, not just "is the field present")
    # is rejected outright. A geometry question with no figure, or a wrong
    # figure, is worse than no question at all.
    if meta.get("diagram_required") and meta.get("auto_generate", True):
        diagram_kind = meta["diagram_kind"]
        before = len(questions)
        questions = [q for q in questions if validate_diagram(q, diagram_kind)]
        dropped = before - len(questions)
        if dropped:
            print(f"   diagram gate dropped {dropped}/{before} (missing or geometrically inconsistent)")

    verified_records = []
    for q in questions:
        passed, score, needs_review = verify_question(q)
        if needs_review:
            append_pending_review(q, topic_id, level, "verifier_disagreement")
            continue
        if not passed:
            continue
        q["_quality_score"] = score
        verified_records.append(to_final_record(q, topic_id, level))

    print(f"   verified {len(verified_records)}/{len(questions)} (threshold {QUALITY_SCORE_THRESHOLD}/10)")

    if verified_records:
        write_json_batch(verified_records, batch_label=f"{topic_id}_L{level}")

    saved = 0
    if verified_records and not dry_run:
        saved = push_to_supabase(verified_records)
        print(f"   pushed {saved} to Supabase")

    return {"generated": len(questions), "verified": len(verified_records), "saved": saved}


# ──────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-jobs", type=int, default=None, help="limit number of jobs this run (use to fit a GitHub Actions time window)")
    parser.add_argument("--questions-per-job", type=int, default=15)
    parser.add_argument("--dry-run", action="store_true", help="generate + verify but skip the Supabase push")
    parser.add_argument("--report", action="store_true", help="print quota progress and exit, no generation")
    args = parser.parse_args()

    if args.report:
        print(progress_report())
        return

    jobs = build_today_jobs(questions_per_job=args.questions_per_job, max_jobs=args.max_jobs)
    print("=" * 60)
    print(f"TryIT Question Engine — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Jobs queued this run: {len(jobs)} (crowded tier first)")
    print("=" * 60)

    totals = {"generated": 0, "verified": 0, "saved": 0}
    for topic_id, level, count in jobs:
        result = process_job(topic_id, level, count, dry_run=args.dry_run)
        for k in totals:
            totals[k] += result[k]
        time.sleep(1)  # gentle pacing between jobs, on top of per-provider backoff

    print("\n" + "=" * 60)
    print(f"DONE. generated={totals['generated']} verified={totals['verified']} saved={totals['saved']}")
    print("=" * 60)


if __name__ == "__main__":
    main()

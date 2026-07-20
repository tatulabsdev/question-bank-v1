"""
TryIT Concept Learning — Generation Pipeline
====================================================================
Generates the 3-depth (quick/standard/deep_dive) concept-teaching
content for topics, storing into concept_content. This is SEPARATE
from pipeline.py (the MCQ question bank) — different table, different
prompts, different quality bar ("no mentor needed" teaching, not MCQ
correctness).

Usage:
    python concept_pipeline.py --topic-id maths_arithmetic_number_system
    python concept_pipeline.py --max-topics 10   # process N topics, highest coverage_score first
    python concept_pipeline.py --dry-run          # generate+verify but don't push

GENERATION ORDER PER TOPIC: standard first (the anchor, including the
India Example), then quick and deep_dive both reference that same
example so a student moving between depths sees one consistent mental
picture, not three disconnected explanations.
"""
import os
import json
import uuid
import argparse
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from concept_rules import build_standard_prompt, build_quick_prompt, build_deep_dive_prompt
from providers import call_with_failover, rotated_chain, CONCEPT_CHAIN
from supabase_data import fetch_topics, fetch_subjects, fetch_exam_tags_for_topic

REQUEST_TIMEOUT = 30


def _parse_concept_json(text):
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


def _generate_depth(prompt, label):
    text, provider = call_with_failover(prompt, rotated_chain(CONCEPT_CHAIN), label=label)
    result = _parse_concept_json(text)
    if result is None:
        if text is None:
            print(f"      [{label}] NO PROVIDER RESPONDED (all 8 in CONCEPT_CHAIN exhausted)")
        else:
            print(f"      [{label}] got text from {provider} but FAILED TO PARSE as JSON")
    return result, provider


def build_verification_prompt(depth: str, explanation_text: str, india_example: str) -> str:
    if depth == "quick":
        self_sufficient_definition = (
            '"self_sufficient": Quick is a FAST RECALL AID for a student who '
            "already learned this concept once via the Standard or Deep Dive "
            "version — it is NOT trying to teach from zero, and should NOT be "
            "penalized for being condensed. False only if it's actually "
            "misleading or would cause a student to recall the concept "
            "WRONG — not merely for being brief."
        )
    else:
        self_sufficient_definition = (
            '"self_sufficient": could a student with NO outside help (no '
            "teacher, no tutor, no forum) genuinely understand this from the "
            "text alone? False if it skips a step, uses unexplained jargon, "
            'or hand-waves ("it can be shown that", "obviously", "clearly").'
        )

    return f"""Check this {depth}-depth concept-teaching content against a
strict "no mentor needed" bar — a student with zero outside help must
be able to genuinely understand this, not just technically read it.
{"Note: Quick depth has its own appropriately different bar, see below." if depth == "quick" else ""}

EXPLANATION: {explanation_text}
INDIA EXAMPLE: {india_example}

Respond with ONLY a JSON object:
{{
  "factually_accurate": true or false,
  "self_sufficient": true or false,
  "india_example_is_genuine": true or false,
  "quality_score": 1-10,
  "reason": "one short sentence"
}}

Field definitions — be strict:
- "factually_accurate": is the explanation actually correct, with no
  errors in the concept, formula, or reasoning?
- {self_sufficient_definition}
- "india_example_is_genuine": is this a real, specific, relatable
  Indian everyday scenario (not generic, not Western-context, not
  vague)?
"""


def verify_concept_content(depth, explanation_text, india_example):
    prompt = build_verification_prompt(depth, explanation_text, india_example)
    text, provider = call_with_failover(prompt, rotated_chain(CONCEPT_CHAIN), label=f"concept-verify:{depth}")
    result = _parse_concept_json(text)
    if not result:
        return False, 0, "verifier produced no parseable result"

    if not result.get("factually_accurate", False):
        return False, result.get("quality_score", 0), f"factually inaccurate: {result.get('reason')}"
    if not result.get("self_sufficient", False):
        return False, result.get("quality_score", 0), f"not self-sufficient: {result.get('reason')}"
    if not result.get("india_example_is_genuine", False):
        return False, result.get("quality_score", 0), f"India example not genuine: {result.get('reason')}"

    score = result.get("quality_score", 0)
    return score >= 7, score, result.get("reason", "")


def push_concept_content(rows: list) -> int:
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()
    if not url or not key:
        print(f"  SUPABASE_URL/SUPABASE_KEY not set — built {len(rows)} rows, nothing pushed")
        return 0
    saved = 0
    for i in range(0, len(rows), 50):
        batch = rows[i:i + 50]
        r = requests.post(
            f"{url}/rest/v1/concept_content",
            headers={"apikey": key, "Authorization": f"Bearer {key}",
                     "Content-Type": "application/json", "Prefer": "return=minimal,resolution=merge-duplicates"},
            # on_conflict tells PostgREST WHICH unique constraint to treat
            # as the merge target. Without this, it only knows about the
            # primary key (concept_id, always a fresh UUID so it never
            # actually conflicts) — the real (topic_id, depth) uniqueness
            # rule was silently ignored, causing every re-run on an
            # already-generated topic to fail with a 409 instead of
            # cleanly updating.
            params={"on_conflict": "topic_id,level,depth"},
            json=batch, timeout=REQUEST_TIMEOUT,
        )
        if r.status_code in (200, 201):
            saved += len(batch)
        else:
            print(f"  error {r.status_code}: {r.text[:300]}")
    return saved


def _parse_difficulty_range(difficulty_range: str) -> list:
    """'2-7' -> [2,3,4,5,6,7]. Matches exactly the same range already
    used to gate MCQ question generation for this topic — concept
    content only ever needs to cover levels the topic actually has
    questions for."""
    try:
        lo, hi = difficulty_range.split("-")
        return list(range(int(lo), int(hi) + 1))
    except (ValueError, AttributeError):
        return [5]  # sane fallback if a topic is somehow missing a range


def process_topic_level(topic_id: str, topic_name: str, subject_name: str,
                         level: int, exam_tags: list, dry_run: bool = False) -> dict:
    """Generates and verifies one full Standard->Quick->Deep Dive set
    for ONE level of ONE topic. Called once per valid level within a
    topic's difficulty_range by process_topic() below."""
    rows = []

    std_prompt = build_standard_prompt(topic_id, topic_name, subject_name, level)
    std_result, std_provider = _generate_depth(std_prompt, f"concept-std:{topic_id}:L{level}")
    if not std_result or not std_result.get("explanation_text"):
        print(f"   [{topic_id} L{level}] x standard generation failed — skipping this level entirely (quick/deep_dive need it as anchor)")
        return {"generated": 0, "verified": 0, "saved": 0}

    std_explanation = std_result["explanation_text"]
    std_example = std_result.get("india_example", "")

    for depth, prompt in [
        ("standard", None),  # already generated above
        ("quick", build_quick_prompt(topic_id, topic_name, subject_name, level, std_explanation, std_example)),
        ("deep_dive", build_deep_dive_prompt(topic_id, topic_name, subject_name, level, std_explanation, std_example)),
    ]:
        if depth == "standard":
            result, provider = std_result, std_provider
        else:
            result, provider = _generate_depth(prompt, f"concept-{depth}:{topic_id}:L{level}")

        if not result or not result.get("explanation_text"):
            print(f"   [{topic_id} L{level}] x {depth} generation failed")
            continue

        explanation_text = result["explanation_text"]
        india_example = result.get("india_example", "")
        passed, score, reason = verify_concept_content(depth, explanation_text, india_example)
        print(f"   [{topic_id} L{level}] {depth}: {'PASS' if passed else 'FAIL'} (score {score}/10) {'' if passed else '- ' + reason}")

        if not passed:
            continue

        rows.append({
            "concept_id": f"cc_{uuid.uuid4().hex[:16]}",
            "topic_id": topic_id,
            "level": level,
            "depth": depth,
            "explanation_text": explanation_text,
            "india_example": india_example,
            "exam_tags": exam_tags,
            "generated_by": f"tryit_concept_engine:{provider}",
            "verified": True,
            "quality_score": score,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    saved = 0
    if rows and not dry_run:
        saved = push_concept_content(rows)
        print(f"   [{topic_id} L{level}] pushed {saved}/{len(rows)} depths to Supabase")

    return {"generated": 3, "verified": len(rows), "saved": saved}


def process_topic(topic: dict, subject_name: str, dry_run: bool = False) -> dict:
    topic_id = topic["topic_id"]
    topic_name = topic.get("topic_name", topic_id)
    levels = _parse_difficulty_range(topic.get("difficulty_range", "5-5"))
    print(f"\n-> {topic_id} (levels {levels[0]}-{levels[-1]}, {len(levels)} total)")

    exam_tags = fetch_exam_tags_for_topic(topic_id)

    totals = {"generated": 0, "verified": 0, "saved": 0}
    for level in levels:
        result = process_topic_level(topic_id, topic_name, subject_name, level, exam_tags, dry_run=dry_run)
        for k in totals:
            totals[k] += result[k]
    return totals


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic-id", type=str, default=None, help="Process just this one topic_id")
    parser.add_argument("--max-topics", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-workers", type=int, default=4)
    args = parser.parse_args()

    subjects = fetch_subjects()

    if args.topic_id:
        from supabase_data import fetch_topic_by_id
        topic = fetch_topic_by_id(args.topic_id)
        if not topic:
            print(f"topic_id '{args.topic_id}' not found")
            return
        topics = [topic]
    else:
        topics = fetch_topics()
        if args.max_topics:
            topics = topics[:args.max_topics]

    print("=" * 60)
    print(f"TryIT Concept Learning Engine — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Topics queued: {len(topics)}")
    print("=" * 60)

    totals = {"generated": 0, "verified": 0, "saved": 0}

    def run_one(topic):
        subject_name = subjects.get(topic["subject_id"], {}).get("subject_name", topic["subject_id"])
        try:
            return process_topic(topic, subject_name, dry_run=args.dry_run), None
        except Exception as e:
            return None, (topic["topic_id"], e)

    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = [executor.submit(run_one, t) for t in topics]
        for future in as_completed(futures):
            result, err = future.result()
            if err:
                topic_id, e = err
                print(f"   !! UNEXPECTED ERROR on {topic_id}: {type(e).__name__}: {e}")
                continue
            for k in totals:
                totals[k] += result[k]

    print("\n" + "=" * 60)
    print(f"DONE. topics_generated={totals['generated']//3 if totals['generated'] else 0} depths_verified={totals['verified']} depths_saved={totals['saved']}")
    print("=" * 60)


if __name__ == "__main__":
    main()


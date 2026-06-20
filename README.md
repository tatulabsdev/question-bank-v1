# TryIT Question Engine

Generates exam-prep MCQs across difficulty levels L1-L10, cross-tagged to
every exam they're relevant for, with a 7-layer explanation, then verifies
each one with two independent AI models before it's saved.

## Diagrams — generated AND verified at the same time as the question

For Geometry, Trigonometry, Mensuration, Data Interpretation, and
mirror-image Reasoning, the diagram is generated in the **same call** as
the question (see `diagrams.py`), then checked with actual coordinate
math before the question is allowed to pass — not just trusted because
the model said so:

- **Data Interpretation** → no image at all. The model emits numbers
  (`chart_data`), the TryIT app renders the bar/line/pie chart client-side.
  Cheaper, sharper, themeable, and accessible — better than a static image.
- **Geometry/Trigonometry/Mensuration** → the model emits an SVG figure
  plus the exact values it used (`diagram_meta`). The pipeline independently
  recomputes the figure's side-length ratios from the SVG coordinates and
  rejects it if they don't match the question's stated numbers.
- **Mirror-image reasoning** → the model emits the original shape plus 4
  option shapes. The pipeline checks computationally that the marked
  "correct" option is a true geometric reflection of the original, not
  just visually plausible.

A question whose diagram fails this check is **dropped, not saved without
its diagram** — for these topics, an incomplete or wrong figure is worse
than no question at all.

**Paused on purpose, not faked:** `reason_embedded_paperfold` and
`geo_indian_physical` are marked `auto_generate: False` in `config.py`.
Embedded-figure and paper-folding puzzles have no reliable computational
correctness check yet, and an LLM should not freehand India's coastline
for a map question. Both are skipped by the job queue entirely until
there's a verified way to check them — see the `auto_generate_note` on
each topic in `config.py` for specifics.

**Paper folding and embedded figures now work too — built differently
on purpose.** These don't go through the LLM-draws-then-we-check flow
that geometry/mirror-image use. Instead, `geometry_engine.py` constructs
the figure and the correct answer FIRST, with plain coordinate math
(fold = reflection across an axis; embedding = literally placing a
target shape's edges as a subset of a bigger figure's lines). The LLM
is only asked to write the question stem and explanations around an
answer that's already fixed — it has no opportunity to invent wrong
geometry because it never generates any. Both generators carry their
own self-check function and were stress-tested across 500 random seeds
each with zero failures, plus a negative test confirming the self-check
actually rejects a deliberately wrong answer rather than rubber-stamping.

**Maps now work too, the same way Data Interpretation charts do — data,
not images.** `geo_state_identification` lets the LLM pick a real state
or UT name from a canonical closed list (`INDIAN_STATES_UTS` in
`config.py`) — never asked to draw a coastline. Wire your frontend's
actual map rendering to an openly-licensed boundary dataset (e.g.
india-geodata, CC0/CC-BY-4.0) — this backend only validates that the
named place is real; factual accuracy of the question itself goes
through the normal two-model GK verification, same as any other fact.

**Still genuinely paused:** broader physical geography (rivers,
mountains, plateaus) stays text-only in `geo_indian_physical` — that
would need its own sourced canonical list the same way states/UTs got
one, and that hasn't been built yet.

## What this does NOT do yet (be aware before you rely on it)

- **Full 40-language translation** isn't wired into `pipeline.py` yet —
  `translations: {}` is left empty on every record on purpose. The
  translation instruction logic exists in `content_rules.py`
  (`build_translation_instruction`) and is ready to plug in, but the
  actual translation API calls + the sampled back-translation audit need
  a dedicated `translate.py` pass once English generation is stable and
  you're happy with question quality. Don't translate before the English
  source content is right — you'd just be translating mistakes 40 times.
- **Human review queue** — disagreements between the two verifiers get
  written to `output/pending_review.jsonl`. Nothing currently reads that
  file back out for you to act on — that's the "separate case, handle at
  the end" item from our planning conversation.

## One-time setup

1. **Get free API keys** (no credit card needed for any of these):
   - Cerebras: https://cloud.cerebras.ai
   - Groq: https://console.groq.com
   - Google AI Studio (Gemini): https://aistudio.google.com
   - OpenRouter: https://openrouter.ai
   - Mistral: https://console.mistral.ai

   You don't need all five to start — the pipeline skips any provider
   with no key set. More providers = more daily throughput and better
   failover when one is rate-limited.

2. **Push this repo to GitHub as a public repo.** Public = unlimited free
   Actions minutes. The repo only ever contains code, never keys or
   question data, so this is safe.

3. **Add your keys as repo secrets**: Settings → Secrets and variables →
   Actions → New repository secret. Add each of:
   `CEREBRAS_API_KEY`, `GROQ_API_KEY`, `GEMINI_API_KEY`,
   `OPENROUTER_API_KEY`, `MISTRAL_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`

4. **Create the `questions` table in Supabase** with at least these
   columns (matches the fields in `pipeline.py:to_final_record`):
   `id` (text, primary key), `topic_id`, `subject`, `chapter`, `topic`,
   `level` (int), `tier`, `question_en`, `options_en` (jsonb),
   `correct_answer` (int), `explanation` (jsonb), `diagram_required` (bool),
   `diagram` (jsonb), `exam_mapping` (jsonb),
   `exam_tags` (jsonb), `verified` (bool), `quality_score` (numeric),
   `copyright_original` (bool), `translations` (jsonb), `created` (text).

5. That's it — the GitHub Actions workflow (`.github/workflows/daily_generation.yml`)
   runs three times a day automatically. No laptop, no Codespace needs to
   stay open.

## Running it yourself (testing, before trusting the automation)

```bash
pip install -r requirements.txt
cp .env.example .env        # fill in at least one provider key for testing
export $(cat .env | xargs)  # or use python-dotenv / your own method

python pipeline.py --report                          # see quota progress, no generation
python pipeline.py --max-jobs 2 --dry-run             # generate+verify 2 small jobs, don't push
python pipeline.py --max-jobs 5                       # generate+verify+push 5 jobs for real
```

Check the `output/` folder after a run — that's where the JSON batch
files land (200-500 questions per file, matching your original spec),
plus `pending_review.jsonl` if any verifier disagreements came up.

## Errors you will see, and what they mean

| What you'll see | What it means | What to do |
|---|---|---|
| `[provider] auth error — check the API key secret` | A key is missing, wrong, or revoked | Re-check the GitHub Secret value |
| Generation returns 0 questions, no error printed | Every provider in the chain is rate-limited or unset right now | Normal during heavy use — the next scheduled run picks it back up |
| `no valid JSON parsed from <provider> response` | The model didn't return clean JSON (rambled, added commentary) | Happens occasionally with every model; this batch is just skipped, nothing is saved incorrectly |
| Low verified-to-generated ratio (e.g. 15/30) | Normal. Expect roughly 70-85% of raw generations to pass verification — that's the quality gate working, not a bug | Only worth investigating if the ratio drops below ~50% consistently for one topic |
| `[supabase] error 401` / `403` | `SUPABASE_KEY` is wrong or the table's row-level security is blocking inserts | Check the key and your Supabase table's RLS policy |
| `[supabase] error 409` or similar on insert | Likely a duplicate `id` — extremely unlikely with UUIDs, but possible if a run is interrupted and retried with the exact same batch | Safe to ignore; that batch's JSON file is still saved locally either way |

## Output quality — what "good" looks like

- **Verification threshold is 7/10**, scored on clarity, plausibility of
  wrong options, explanation quality, cultural relevance, and uniqueness.
  This was inconsistent in the old scripts (6 vs 7) — now standardized.
- **Two independent models must agree** the answer is correct before a
  question is saved. If they disagree, it goes to `pending_review.jsonl`
  instead of being auto-rejected or auto-accepted — a coin-flip there
  would be worse than a queue.
- **Any factual error flagged by either verifier is an instant reject**,
  regardless of the other verifier's opinion or the quality score.
- Expect the verified rate to vary by topic: factual/GK topics
  (History, Polity, Science) will reject more often than pure-logic
  topics (Percentage, Analogy) — verifying a fact is harder than
  verifying arithmetic, so this is expected, not a sign of breakage.

## The quota system, in practice

- Topics are tiered **crowded (30k floor) → medium (20k floor) →
  niche (10k floor)** and the job builder always processes crowded
  topics first, every run, until they're filled.
- Quotas are checked live against Supabase, not a separate progress
  file — so the count is always accurate even if a run crashes
  halfway through.
- Add new topics in `config.py` following the exact schema already
  there — the rest of the pipeline picks them up automatically, no
  other file needs to change.

## Extending to more languages

`content_rules.py` already encodes the rule that matters most: Northeast
languages (`FORMAL_ONLY_LANGUAGES`) never get the slang layer, only
warm, standard, encouraging translation. When you're ready to wire up
the actual translation pass, call `build_translation_instruction(lang_code)`
to get the correctly-scoped prompt instruction for any language —
slang-aware for the eight languages in `SLANG_GLOSSARY`, formal for
everything else, automatically.

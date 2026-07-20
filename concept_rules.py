"""
TryIT Concept Learning — Content Rules
====================================================================
Prompts for the CONCEPT-TEACHING layer, distinct from the MCQ question
bank. Each topic now gets content across TWO axes:

1. LEVEL (1-10) — matches the exact same difficulty ladder used by the
   MCQ question bank (see config.py's LEVELS). This is the axis that
   determines WHO the explanation is for — a Class 2 student and a PhD
   aspirant need genuinely different vocabulary, abstraction, and
   worked-example complexity for the "same" topic, not just more or
   less detail. Only levels within a topic's existing difficulty_range
   get generated (matches the same range already used for questions).

2. DEPTH (quick/standard/deep_dive) — how much time a student at THAT
   level wants to spend reading right now. This is orthogonal to level:
   it doesn't change who the audience is, only how much of the same
   sophistication gets unpacked.

So a single topic like Number System (difficulty_range 2-7) generates
up to 6 levels × 3 depths = 18 rows, each one genuinely rewritten for
that level's audience, not just re-labeled copies of one explanation.

GENERATION ORDER PER LEVEL: "standard" is generated FIRST for that
level, since it's the anchor — its India Example gets passed into both
"quick" (condense it) and "deep_dive" (expand on it) AT THE SAME LEVEL,
so a student moving between depths within one level sees a consistent
mental picture. Different levels are independent of each other — a
Level 8 explanation is not built from the Level 3 one, since the
audience is different enough that reusing the same example across
levels would be forcing a school-age scenario onto a PhD-level
treatment or vice versa.

THE CORE BAR: "no mentor needed" is the actual design target, not a
slogan — meaning a student with zero access to a teacher, tutor, or
even a doubt-clearing forum should be able to read this and genuinely
understand the concept well enough to attempt questions on it. This is
a much higher bar than "technically explains the topic" — it means
anticipating the exact place a student gets stuck and addressing it
BEFORE they ask, not after.
"""

from config import LEVELS
from diversity_pool import random_diversity_injection

CORE_TEACHING_INSTRUCTION = """
You are writing concept-teaching content for TryIT, an Indian exam-prep
platform. Your writing must meet a "no mentor needed" bar: a student
studying completely alone — no teacher, no tutor, no doubt-clearing
forum available — must be able to read this and genuinely understand
the concept well enough to attempt real exam questions on it
afterward. This is a much higher bar than "technically correct and
complete" — it means anticipating the EXACT place a student typically
gets confused and addressing it before they even ask, not leaving a
gap they'd need outside help to fill.

MANDATORY — a real India Example: every explanation must include one
genuinely relatable, everyday Indian scenario that makes the abstract
concept concrete (festivals, household routines, local transport,
common family situations, familiar shopping/market scenarios, school
life). This is not decoration — it should be the thing a student
actually remembers when the concept itself gets fuzzy later. Avoid
generic or Western-context examples entirely.

Never write in a way that assumes the student already has outside help
available to fill gaps — if a prerequisite idea is needed, explain it
briefly inline rather than assuming it or waving past it.

MANDATORY — no unexplained notation: never use a symbol, term, or
notation (e.g. a formula symbol, mathematical notation, technical
vocabulary) without defining what it means the FIRST time it appears.
If you would need a footnote to explain something, put that
explanation directly in the sentence instead — there is no footnote a
student can click on.

MANDATORY — a real worked example: include at least one CONCRETE
numerical example showing the actual step-by-step arithmetic/reasoning
worked out in full — not a description of the method in words, an
actual worked-through instance with real numbers a student can follow
line by line and verify themselves.

SELF-CHECK BEFORE FINALIZING: re-read your own explanation as if you
were a skeptical student. Is every mathematical or factual claim you
made actually true? Work through your own worked example again and
confirm the arithmetic is genuinely correct — do not state a property
or result you have not actually double-checked.
"""


def _level_instruction(level: int) -> str:
    level_desc = LEVELS.get(level, "competitive level")
    return f"""
TARGET AUDIENCE — LEVEL {level} ({level_desc}): this explanation is
being written for THIS specific audience, not a generic student. This
changes real things, not just tone:
- Vocabulary: use words this specific age/stage would actually know.
  Don't use terms a Class 2 student hasn't encountered yet; don't
  under-explain in a way that insults a PhD-level reader's intelligence.
- Abstraction level: a school-age explanation should stay concrete and
  example-driven; a competitive/research-level explanation can and
  should engage with the underlying structure, edge cases, and
  connections to other concepts a student at that stage would be
  expected to already reason with.
- The India Example itself must fit this audience's real life — a
  Class 2 example should involve things a 7-year-old actually
  experiences (sharing sweets, counting siblings); a UPSC Mains/PhD
  level example can involve more adult, abstract, or professional
  scenarios.
This is NOT the same content simplified or complicated — write it
genuinely FOR this specific audience from the start.
"""


def _exam_tags_for_topic(topic_id: str) -> list:
    """Pulls REAL exam relevance from exam_syllabus_map (built earlier
    this session) rather than guessing or hardcoding exam names. Returns
    exam_id values only for the 5 exams with genuinely sourced
    topic-level weightage — see seed_exam_syllabus_map.py for why only
    those 5 have real per-topic data."""
    from supabase_data import fetch_exam_tags_for_topic  # thin Supabase query, see supabase_data.py
    return fetch_exam_tags_for_topic(topic_id)


def build_standard_prompt(topic_id: str, topic_name: str, subject_name: str, level: int) -> str:
    return f"""{CORE_TEACHING_INSTRUCTION}
{_level_instruction(level)}
{random_diversity_injection()}

TOPIC: {topic_name} (subject: {subject_name})
DEPTH: Standard (~10 minute read) — the main, anchor explanation for
THIS level's audience specifically.

Write:
1. "explanation_text": a clear, complete explanation of the concept —
   what it is, the core method/formula (if any), and WHY it works, not
   just what to do mechanically. Include the single most exam-useful
   fact or shortcut if one genuinely exists for this concept AT THIS
   LEVEL.
2. "india_example": one vivid, realistic Indian everyday scenario,
   appropriate to this specific audience's age/stage, that makes this
   concept concrete — this is the example a student should still
   remember weeks later even if they forget the formal definition.

Return ONLY a JSON object:
{{
  "explanation_text": "...",
  "india_example": "..."
}}
"""


def build_quick_prompt(topic_id: str, topic_name: str, subject_name: str, level: int,
                        standard_explanation: str, standard_example: str) -> str:
    return f"""{CORE_TEACHING_INSTRUCTION}
{_level_instruction(level)}

OVERRIDE FOR THIS DEPTH SPECIFICALLY: the "mandatory worked example" and
"no unexplained notation" rules above apply to Standard and Deep Dive,
which teach from scratch. Quick is different — it's a fast recall aid
for a student who ALREADY learned this once, so it does NOT need a full
worked example or first-principles notation definitions. It still must
be factually accurate and must not mislead — just don't force a full
teaching structure into 2-3 sentences.

TOPIC: {topic_name} (subject: {subject_name})
DEPTH: Quick (~2 minute read) — a fast pre-exam refresher, NOT a first
introduction. Assume the student already learned this once; they need
the core idea back in their head fast, not a full re-teach.

Here is the Standard-depth version already written for this topic AT
THIS SAME LEVEL, to keep consistent with:
STANDARD EXPLANATION: {standard_explanation}
STANDARD INDIA EXAMPLE: {standard_example}

Write:
1. "explanation_text": the single most essential 2-3 sentences — the
   core method/formula only, stripped to what's needed to solve a
   question right now, not the full reasoning.
2. "india_example": a ONE-LINE condensed callback to the SAME example
   above (don't invent a new one) — just enough to re-trigger the
   memory of it.

Return ONLY a JSON object:
{{
  "explanation_text": "...",
  "india_example": "..."
}}
"""


def build_deep_dive_prompt(topic_id: str, topic_name: str, subject_name: str, level: int,
                            standard_explanation: str, standard_example: str) -> str:
    return f"""{CORE_TEACHING_INSTRUCTION}
{_level_instruction(level)}

TOPIC: {topic_name} (subject: {subject_name})
DEPTH: Deep Dive (~30 minute read) — full mastery for THIS level's
audience, including the edge cases and misconceptions that trip
students up at this specific stage.

Here is the Standard-depth version already written for this topic AT
THIS SAME LEVEL — EXPAND on this same example, don't invent an
unrelated new one:
STANDARD EXPLANATION: {standard_explanation}
STANDARD INDIA EXAMPLE: {standard_example}

Write:
1. "explanation_text": the full concept including: the underlying
   reasoning (not just the method), at least one common misconception
   students AT THIS LEVEL have and why it's wrong, and how this concept
   connects to 1-2 related topics a student at this stage will see it
   combined with in real exams.
2. "india_example": EXPAND the same India Example from Standard into a
   richer, multi-step version that walks through a harder variation of
   the same everyday scenario, still appropriate to this audience.

Return ONLY a JSON object:
{{
  "explanation_text": "...",
  "india_example": "..."
}}
"""


"""
TryIT Concept Learning — Content Rules
====================================================================
Prompts for the CONCEPT-TEACHING layer, distinct from the MCQ question
bank. Each topic gets exactly 3 rows in concept_content (quick,
standard, deep_dive) — this is a DEPTH axis, not a DIFFICULTY axis.
The existing 1-10 difficulty ladder lives entirely in the questions
table; concept_content is orthogonal to it, teaching the underlying
idea itself before a student ever sees a graded question.

GENERATION ORDER MATTERS: "standard" is generated FIRST, since it's the
anchor — its India Example gets passed into both "quick" (condense it)
and "deep_dive" (expand on it), so a student moving between depths
sees the same mental picture getting sharper or richer, not three
disconnected explanations of the same topic.

THE CORE BAR: "no mentor needed" is the actual design target, not a
slogan — meaning a student with zero access to a teacher, tutor, or
even a doubt-clearing forum should be able to read this and genuinely
understand the concept well enough to attempt questions on it. This is
a much higher bar than "technically explains the topic" — it means
anticipating the exact place a student gets stuck and addressing it
BEFORE they ask, not after.
"""

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


def _exam_tags_for_topic(topic_id: str) -> list:
    """Pulls REAL exam relevance from exam_syllabus_map (built earlier
    this session) rather than guessing or hardcoding exam names. Returns
    exam_id values only for the 5 exams with genuinely sourced
    topic-level weightage — see seed_exam_syllabus_map.py for why only
    those 5 have real per-topic data."""
    from supabase_data import fetch_exam_tags_for_topic  # thin Supabase query, see supabase_data.py
    return fetch_exam_tags_for_topic(topic_id)


def build_standard_prompt(topic_id: str, topic_name: str, subject_name: str) -> str:
    return f"""{CORE_TEACHING_INSTRUCTION}

TOPIC: {topic_name} (subject: {subject_name})
DEPTH: Standard (~10 minute read) — the main, anchor explanation.

Write:
1. "explanation_text": a clear, complete explanation of the concept —
   what it is, the core method/formula (if any), and WHY it works, not
   just what to do mechanically. Include the single most exam-useful
   fact or shortcut if one genuinely exists for this concept.
2. "india_example": one vivid, realistic Indian everyday scenario that
   makes this concept concrete — this is the example a student should
   still remember weeks later even if they forget the formal
   definition.

Return ONLY a JSON object:
{{
  "explanation_text": "...",
  "india_example": "..."
}}
"""


def build_quick_prompt(topic_id: str, topic_name: str, subject_name: str,
                        standard_explanation: str, standard_example: str) -> str:
    return f"""{CORE_TEACHING_INSTRUCTION}

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

Here is the Standard-depth version already written for this topic, to
keep consistent with:
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


def build_deep_dive_prompt(topic_id: str, topic_name: str, subject_name: str,
                            standard_explanation: str, standard_example: str) -> str:
    return f"""{CORE_TEACHING_INSTRUCTION}

TOPIC: {topic_name} (subject: {subject_name})
DEPTH: Deep Dive (~30 minute read) — full mastery, including the
edge cases and misconceptions that trip students up in real exams.

Here is the Standard-depth version already written for this topic —
EXPAND on this same example, don't invent an unrelated new one:
STANDARD EXPLANATION: {standard_explanation}
STANDARD INDIA EXAMPLE: {standard_example}

Write:
1. "explanation_text": the full concept including: the underlying
   reasoning (not just the method), at least one common misconception
   students have and why it's wrong, and how this concept connects to
   1-2 related topics a student will see it combined with in real
   exams.
2. "india_example": EXPAND the same India Example from Standard into a
   richer, multi-step version that walks through a harder variation of
   the same everyday scenario.

Return ONLY a JSON object:
{{
  "explanation_text": "...",
  "india_example": "..."
}}
"""


"""
TryIT Question Engine — Content Rules
========================================
Everything about HOW content must be written: copyright safety,
the 7-layer explanation spec (with per-option wrong-answer reasons),
the language slang glossary, and the decency/profanity filter.
"""

# ──────────────────────────────────────────────────────────
# COPYRIGHT — non-negotiable, injected into every generation prompt
# ──────────────────────────────────────────────────────────
COPYRIGHT_INSTRUCTION = """
CRITICAL COPYRIGHT RULES (do not break these):
- Generate 100% ORIGINAL questions inspired by concepts and patterns only.
- NEVER copy, closely paraphrase, or lightly reword any textbook, question
  paper, or published source. Renaming or relocating copied text is NOT
  original and is NOT acceptable — if you recognize a question as similar
  to a known source, discard it and write a genuinely new one.
- Invent new scenarios, new numbers, new character names, new settings.
- Use Indian names (Ramu, Priya, Abdul, Kavitha, Sundar, Meena) and Indian
  places (Chennai, Coimbatore, Surat, Patna, Bhopal) freely — these are
  generic, not copyrighted.
- Numbers and scenarios must differ from any specific known previous-year
  question. "Inspired by the pattern" is fine. "The same question with
  different numbers" is not.
"""

# ──────────────────────────────────────────────────────────
# 7-LAYER EXPLANATION SPEC — matches your original brief exactly,
# including per-wrong-option reasons (this was missing from the old schema)
# ──────────────────────────────────────────────────────────
EXPLANATION_LAYER_INSTRUCTION = """
For EACH question, produce exactly these explanation fields. Write like an
experienced, warm human mentor talking directly to ONE student sitting
next to you — not like an AI summarizing steps. Avoid formulaic,
repetitive sentence patterns (don't structure every story the same way,
e.g. always "Name does X, then realizes Y, so the answer is Z"). Vary
your voice and phrasing the way a real teacher naturally would.

1. "why_correct": why the correct option is right (clear, step-by-step).

2. "why_wrong_option_b" / "why_wrong_option_c" / "why_wrong_option_d":
   covers the three incorrect options. Use judgment on depth:
   - If each wrong option reflects a genuinely DIFFERENT misconception
     worth understanding separately, explain each one in its own field.
   - If the wrong options are just simple slips (arithmetic errors, minor
     misreads) that don't need individual depth, write ONE combined
     sentence covering all three together in the "why_wrong_option_b"
     field, and leave "why_wrong_option_c" and "why_wrong_option_d" as
     empty strings ("") — don't pad these just to fill three fields.
   (If the correct answer is B, C, or D, still label these three fields
   by the OTHER three option letters, not always B/C/D literally.)

3. "story_explanation": a short, relatable story-style walkthrough, in the
   voice of a favorite teacher explaining it one-on-one — warm, direct,
   plain language. Not a generic AI recap of the calculation steps.

4. "shortcut_tips": MUST include an actual memorable mnemonic — a short
   acronym, rhyme, or catchy phrase a student could recall in an exam
   hall under pressure (e.g. "PEMDAS", "SOH-CAH-TOA", "Roygbiv"-style).
   A generic time-saving method alone is NOT enough — invent or apply a
   genuine memory device specific to this question's concept, then add
   any additional quick-calculation trick after it. Write it like a
   mentor sharing their own trick, not a listicle.

5. "cross_exam_intelligence": name which other exams ask this type of
   question. Do NOT include frequency callouts ("appears 2-4 times per
   paper"), difficulty ratings, or any other meta-scoring language — just
   the exam names and, if genuinely useful, what angle they test it from.
"""

# ──────────────────────────────────────────────────────────
# DECENCY / SAFETY FILTER
# Applied as its own pipeline stage AFTER generation and AFTER translation.
# This is a guardrail layer, not a creativity layer — keep it boring and strict.
# ──────────────────────────────────────────────────────────
DECENCY_RULES = """
CONTENT SAFETY — strict, no exceptions (this platform is used by school
children from age ~10 upward):
- No sexual content, innuendo, or double-meaning words in any language.
- No profanity, slurs, or vulgar language in any language or dialect.
- No content that mocks a religion, caste, region, or community.
- No graphic violence or distressing imagery in word problems.
- Address terms and exclamations (see glossary) must stay strictly
  platonic and encouraging — never romantic, never body-related.
"""

# A lightweight keyword tripwire — NOT a substitute for the AI decency pass,
# just a fast first filter to catch obvious misses before they reach review.
# Extend this list over time; keep it boring on purpose.
PROFANITY_TRIPWIRE_EN = [
    "sex", "nude", "porn", "rape", "slur_placeholder",
]

# ──────────────────────────────────────────────────────────
# SLANG / CULTURAL TONE GLOSSARY
# Used only in the cultural-adaptation translation pass, and ONLY for the
# languages listed here. Every entry is an address term or an encouragement
# exclamation — nothing else is approved for use.
#
# NORTHEAST LANGUAGES ARE DELIBERATELY EXCLUDED FROM THIS GLOSSARY.
# Per your decision: Assamese, Bodo, Manipuri/Meitei, Khasi, Mizo, Nagamese,
# etc. get standard, formal, warm translation — encouraging tone is fine,
# but no slang/idiom layer until a native reviewer signs off per language.
# See FORMAL_ONLY_LANGUAGES below — the translator must check this list
# and skip the slang layer entirely for these.
# ──────────────────────────────────────────────────────────
SLANG_GLOSSARY = {
    "ta": {"address": ["anna", "akka", "thambi", "nanba"], "exclaim": ["Semma!", "Super da!"]},
    "te": {"address": ["anna", "akka", "babu"],             "exclaim": ["Bagundi!"]},
    "hi": {"address": ["yaar", "bhai", "didi"],             "exclaim": ["Ekdum sahi!"]},
    "kn": {"address": ["anna", "akka", "guru"],             "exclaim": ["Super kano!"]},
    "ml": {"address": ["chetta", "chechi"],                 "exclaim": ["Kidu!"]},
    "bn": {"address": ["dada", "didi", "bondhu"],           "exclaim": ["Darun!"]},
    "mr": {"address": ["dada", "tai", "mitra"],             "exclaim": ["Bharach!"]},
    "pa": {"address": ["yaar", "bhai", "paaji"],            "exclaim": ["Bilkul sahi!"]},
}

# Languages that get formal, warm, standard-register translation ONLY —
# no entries in SLANG_GLOSSARY should ever be applied to these, even if
# someone adds them later by mistake. The translator checks this list first.
FORMAL_ONLY_LANGUAGES = {
    "as": "Assamese", "brx": "Bodo", "mni": "Manipuri (Meitei)",
    "kha": "Khasi", "lus": "Mizo", "nag": "Nagamese",
    "grt": "Garo", "kok": "Konkani", "doi": "Dogri",
    "sat": "Santali", "mai": "Maithili", "ks": "Kashmiri",
    "sd": "Sindhi", "ne": "Nepali", "sa": "Sanskrit",
}

# All other supported languages without a curated glossary yet default to
# formal/standard translation too — slang only applies where explicitly
# listed in SLANG_GLOSSARY above.

SLANG_LAYER_INSTRUCTION_TEMPLATE = """
Apply the cultural-adaptation pass for language code "{lang_code}".

{slang_block}

Rules:
- Use ONLY the address terms and exclamations listed above, nowhere else
  in the sentence — don't invent new slang.
- Keep all numbers, technical terms (percentage, profit, force, etc.)
  and the core question logic unchanged.
- Tone must stay encouraging and warm, never romantic, never edgy.
"""

FORMAL_INSTRUCTION_TEMPLATE = """
Apply standard, formal, warm translation for language code "{lang_code}"
({lang_name}). Do NOT use slang, regional idioms, or colloquialisms — this
language is on the formal-only list pending native-speaker review of any
informal tone. Keep the translation encouraging and positive in register
(e.g., "well done," "let's work through this together") without using
casual slang words.
"""


def build_explanation_prompt_block():
    return EXPLANATION_LAYER_INSTRUCTION


def build_translation_instruction(lang_code: str) -> str:
    """Returns the correct instruction block for a given language code —
    slang-aware for glossary languages, formal-only for everything else."""
    if lang_code in FORMAL_ONLY_LANGUAGES:
        return FORMAL_INSTRUCTION_TEMPLATE.format(
            lang_code=lang_code, lang_name=FORMAL_ONLY_LANGUAGES[lang_code]
        )
    if lang_code in SLANG_GLOSSARY:
        g = SLANG_GLOSSARY[lang_code]
        slang_block = (
            f"Approved address terms: {', '.join(g['address'])}\n"
            f"Approved exclamations: {', '.join(g['exclaim'])}"
        )
        return SLANG_LAYER_INSTRUCTION_TEMPLATE.format(lang_code=lang_code, slang_block=slang_block)
    # default: formal, no curated glossary yet
    return FORMAL_INSTRUCTION_TEMPLATE.format(lang_code=lang_code, lang_name=lang_code)
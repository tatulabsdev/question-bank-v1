"""
TryIT Question Engine — Duplicate Detection
==============================================
Catches near-duplicate questions before they're saved: same scenario
reworded with different names/numbers, or the model regenerating
something it already produced earlier in the run.

This is intentionally simple (normalized text + word-overlap similarity)
rather than embeddings, so it runs with zero extra API cost and no extra
dependency. It's a first filter, not a perfect one — pair it with the
quality/verification stage, not instead of it.
"""

import re

_WORD_RE = re.compile(r"[a-zA-Z]+")


def _normalize(text: str) -> set:
    """Lowercase, strip numbers/punctuation, return a set of significant words."""
    words = _WORD_RE.findall(text.lower())
    # drop very common filler words so two unrelated questions don't look similar
    # just because they both contain "the", "is", "a", etc.
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "of", "in", "on", "at",
        "to", "for", "and", "or", "if", "what", "which", "how", "many", "much",
        "find", "calculate", "value", "given", "following", "each",
    }
    return {w for w in words if w not in stopwords and len(w) > 2}


def similarity(text_a: str, text_b: str) -> float:
    """Jaccard similarity between the significant-word sets of two questions.
    Returns 0.0 (completely different) to 1.0 (identical wording)."""
    set_a, set_b = _normalize(text_a), _normalize(text_b)
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union else 0.0


def is_duplicate(new_question_text: str, existing_texts: list, threshold: float = 0.75) -> bool:
    """Checks a new question against a list of existing question texts
    (e.g. everything already generated for this topic+level today, plus
    a sample of what's already in the bank). Flags as duplicate if any
    single comparison exceeds the threshold."""
    for existing in existing_texts:
        if similarity(new_question_text, existing) >= threshold:
            return True
    return False


def filter_duplicates(questions: list, text_key: str = "question") -> list:
    """Given a freshly generated batch, drops any question that's a
    near-duplicate of an earlier one IN THE SAME BATCH. Cross-batch /
    cross-bank duplicate checking happens in pipeline.py against
    Supabase, since that needs the existing bank's text, not just
    this batch's.
    """
    kept = []
    seen_texts = []
    for q in questions:
        text = q.get(text_key, "")
        if not text:
            continue
        if is_duplicate(text, seen_texts):
            continue
        seen_texts.append(text)
        kept.append(q)
    return kept

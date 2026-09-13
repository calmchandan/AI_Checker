"""
style_rules.py
Transition-word density, filler-phrase density, and passive-voice
percentage (via spaCy dependency parse: nsubjpass / auxpass, or the
morphological Voice=Pass feature in newer spaCy pipelines).
"""

from text_utils import get_nlp, word_count
from config import TRANSITION_WORDS, FILLER_PHRASES


def _count_phrase_hits(text_lower: str, phrases: set[str]) -> tuple[int, dict]:
    hits = {}
    for phrase in phrases:
        c = text_lower.count(phrase)
        if c:
            hits[phrase] = c
    return sum(hits.values()), hits


def analyze_style(text: str) -> dict:
    total_words = max(1, word_count(text))
    text_lower = text.lower()

    trans_count, trans_hits = _count_phrase_hits(text_lower, TRANSITION_WORDS)
    filler_count, filler_hits = _count_phrase_hits(text_lower, FILLER_PHRASES)

    transition_density = 100 * trans_count / total_words
    filler_density = 100 * filler_count / total_words

    nlp = get_nlp()
    doc = nlp(text)
    sents = [s for s in doc.sents if s.text.strip()]
    passive_sents = 0
    passive_examples = []
    for s in sents:
        is_passive = any(
            tok.dep_ in ("nsubjpass", "auxpass") or
            (tok.morph.get("Voice") == ["Pass"])
            for tok in s
        )
        if is_passive:
            passive_sents += 1
            if len(passive_examples) < 8:
                passive_examples.append(s.text.strip())

    passive_pct = 100 * passive_sents / max(1, len(sents))

    return {
        "transition_density_pct": round(transition_density, 2),
        "transition_word_hits": sorted(trans_hits.items(), key=lambda x: -x[1]),
        "filler_density_pct": round(filler_density, 2),
        "filler_phrase_hits": sorted(filler_hits.items(), key=lambda x: -x[1]),
        "passive_voice_pct": round(passive_pct, 1),
        "passive_sentence_examples": passive_examples,
        "total_sentences": len(sents),
    }

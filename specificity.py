"""
specificity.py
Assesses specificity via proper-noun-like entities, numeric data, domain
terminology density, and vague-quantifier usage — via regex heuristics (no
spaCy dependency; see text_utils.py for why).

Entity detection here is a proper-noun heuristic (capitalized word runs,
plus standalone acronyms), not true named-entity recognition. It will miss
lowercase entities and occasionally catch a sentence-initial capitalized
common word — a known trade-off of avoiding a full NLP pipeline.
"""

import re
from text_utils import word_count, split_sentences
from config import VAGUE_QUANTIFIERS

_NUMBER_RE = re.compile(r"\b\d+(?:[.,]\d+)?%?\b")
_MULTIWORD_ENTITY_RE = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4}\b")
_ACRONYM_RE = re.compile(r"\b[A-Z]{2,6}\b")

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "in", "on", "at", "to",
    "for", "with", "is", "are", "was", "were", "be", "been", "being",
    "this", "that", "these", "those", "it", "its", "as", "by", "from",
    "which", "who", "their", "his", "her", "they", "he", "she", "we",
    "you", "i", "will", "would", "should", "could", "can", "not",
}


def _strip_sentence_initial_false_positives(sentences: list[str], hits: set) -> set:
    """Drop a single-word 'entity' if it only ever appears as the first word
    of a sentence (likely just capitalization from sentence start, not a
    genuine proper noun)."""
    cleaned = set()
    for h in hits:
        if " " in h:
            cleaned.add(h)
            continue
        appears_non_initial = False
        for s in sentences:
            s_stripped = s.strip()
            if s_stripped.startswith(h):
                rest = s_stripped[len(h):]
                if h in rest:
                    appears_non_initial = True
                    break
                continue
            if h in s_stripped:
                appears_non_initial = True
                break
        if appears_non_initial or len(h) <= 5:  # short acronyms kept regardless (RBI, UPI, GDP)
            cleaned.add(h)
    return cleaned


def analyze_specificity(text: str) -> dict:
    total_words = max(1, word_count(text))
    sentences = split_sentences(text)

    multiword_hits = set(_MULTIWORD_ENTITY_RE.findall(text))
    acronym_hits = {a for a in _ACRONYM_RE.findall(text) if a not in ("I", "A")}
    acronym_hits = _strip_sentence_initial_false_positives(sentences, acronym_hits)

    all_entities = multiword_hits | acronym_hits
    numbers = _NUMBER_RE.findall(text)

    tokens_lower = [w.lower() for w in re.findall(r"[A-Za-z']+", text)]
    domain_terms = set()
    for i in range(len(tokens_lower) - 1):
        w1, w2 = tokens_lower[i], tokens_lower[i + 1]
        if len(w1) > 3 and len(w2) > 3 and w1 not in _STOPWORDS and w2 not in _STOPWORDS:
            domain_terms.add(f"{w1} {w2}")

    text_lower = text.lower()
    vague_hits = []
    for phrase in VAGUE_QUANTIFIERS:
        count = text_lower.count(phrase)
        if count:
            vague_hits.append({"phrase": phrase, "count": count})

    entity_density = 100 * len(all_entities) / total_words
    number_density = 100 * len(numbers) / total_words
    domain_density = 100 * len(domain_terms) / total_words

    specificity_signals = entity_density + number_density + (domain_density * 0.5)
    vague_penalty = sum(v["count"] for v in vague_hits)

    raw_score = max(0.0, min(100.0, specificity_signals * 4 - vague_penalty * 2))

    return {
        "entity_count": len(all_entities),
        "unique_entities": sorted(all_entities),
        "number_count": len(numbers),
        "domain_term_count": len(domain_terms),
        "top_domain_terms": sorted(domain_terms, key=len, reverse=True)[:15],
        "vague_quantifier_hits": sorted(vague_hits, key=lambda x: -x["count"]),
        "entity_density_pct": round(entity_density, 2),
        "number_density_pct": round(number_density, 2),
        "specificity_score": round(raw_score, 1),
    }

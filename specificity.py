"""
specificity.py
Assesses specificity via named entities, numeric data, domain terminology
density, and vague-quantifier usage (unsupported "many", "several", etc.).
"""

import re
from text_utils import get_nlp, word_count
from config import VAGUE_QUANTIFIERS

_NUMBER_RE = re.compile(r"\b\d+(?:[.,]\d+)?%?\b")


def analyze_specificity(text: str) -> dict:
    nlp = get_nlp()
    doc = nlp(text)
    total_words = max(1, word_count(text))

    entities = [(ent.text, ent.label_) for ent in doc.ents
                if ent.label_ in ("PERSON", "ORG", "GPE", "LOC", "PRODUCT",
                                  "EVENT", "WORK_OF_ART", "LAW", "NORP", "FAC")]
    numbers = _NUMBER_RE.findall(text)

    # Domain terminology proxy: multi-token noun chunks with a modifier
    # (technical-sounding compound nouns), deduplicated.
    domain_terms = set()
    for chunk in doc.noun_chunks:
        if len(chunk) >= 2 and any(t.pos_ == "NOUN" for t in chunk):
            domain_terms.add(chunk.text.lower())

    text_lower = text.lower()
    vague_hits = []
    for phrase in VAGUE_QUANTIFIERS:
        count = text_lower.count(phrase)
        if count:
            vague_hits.append({"phrase": phrase, "count": count})

    entity_density = 100 * len(entities) / total_words
    number_density = 100 * len(numbers) / total_words
    domain_density = 100 * len(domain_terms) / total_words

    specificity_signals = entity_density + number_density + (domain_density * 0.5)
    vague_penalty = sum(v["count"] for v in vague_hits)

    # Normalize to a 0-100 sub-score (heuristic calibration)
    raw_score = max(0.0, min(100.0, specificity_signals * 4 - vague_penalty * 2))

    return {
        "entity_count": len(entities),
        "unique_entities": sorted(set(e for e, _ in entities)),
        "number_count": len(numbers),
        "domain_term_count": len(domain_terms),
        "top_domain_terms": sorted(domain_terms, key=len, reverse=True)[:15],
        "vague_quantifier_hits": sorted(vague_hits, key=lambda x: -x["count"]),
        "entity_density_pct": round(entity_density, 2),
        "number_density_pct": round(number_density, 2),
        "specificity_score": round(raw_score, 1),
    }

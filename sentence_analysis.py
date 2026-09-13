"""
sentence_analysis.py
Sentence length, complexity, and structural variation.

Uses regex/word-list heuristics rather than a dependency parse (no spaCy
dependency — see text_utils.py for why). "Complex sentence" here means:
contains a subordinating conjunction / relative pronoun, or coordinates two
clauses with a comma + coordinating conjunction. This is an approximation,
not a syntactic parse, but it correlates well with genuine clause structure
for the purpose of a variation metric.
"""

import re
import statistics
from text_utils import split_sentences, word_count

_SUBORDINATORS = {
    "although", "because", "since", "while", "whereas", "though", "unless",
    "until", "if", "when", "before", "after", "as", "that", "which", "who",
    "whom", "whose", "where", "once", "provided", "whenever", "wherever",
}
_COORD_RE = re.compile(r",\s*(and|but|or|so|yet|nor)\b", re.I)

_DETERMINERS = {"the", "a", "an", "this", "that", "these", "those", "some",
                "many", "several", "each", "every", "any", "no", "all"}
_PRONOUNS = {"i", "we", "you", "he", "she", "it", "they", "this", "these", "those"}
_PREPOSITIONS = {"in", "on", "at", "by", "with", "from", "for", "of", "to",
                  "over", "under", "during", "despite", "without", "within"}
_CONJUNCTIONS = {"and", "but", "or", "so", "yet", "although", "because",
                  "since", "while", "if", "when", "however", "therefore"}


def _opener_category(first_word: str) -> str:
    w = re.sub(r"[^A-Za-z]", "", first_word).lower()
    if w in _CONJUNCTIONS:
        return "conjunction/connector"
    if w in _PREPOSITIONS:
        return "preposition"
    if w in _DETERMINERS:
        return "determiner"
    if w in _PRONOUNS:
        return "pronoun"
    if w.endswith("ly") and len(w) > 3:
        return "adverb"
    if first_word[:1].isupper() and w not in _DETERMINERS and w not in _PRONOUNS:
        return "proper_noun/other"
    return "other"


def _is_complex(sentence: str, tokens_lower: list[str]) -> bool:
    has_subordinator = any(t in _SUBORDINATORS for t in tokens_lower)
    has_coordination = bool(_COORD_RE.search(sentence))
    return has_subordinator or has_coordination


def analyze_sentences(text: str) -> dict:
    raw_sents = split_sentences(text)
    lengths = [word_count(s) for s in raw_sents]

    if not lengths:
        return {
            "sentence_count": 0, "mean_length": 0, "median_length": 0,
            "stdev_length": 0, "cv": 0, "length_distribution": [],
            "complex_sentence_pct": 0, "opener_variation_pct": 0,
            "flagged_sentences": [],
        }

    mean_len = statistics.fmean(lengths)
    stdev_len = statistics.pstdev(lengths) if len(lengths) > 1 else 0.0
    cv = (stdev_len / mean_len) if mean_len else 0.0

    complex_flags = []
    openers = []
    flagged = []
    for s, length in zip(raw_sents, lengths):
        tokens_lower = [w.lower() for w in re.findall(r"[A-Za-z']+", s)]
        complex_flags.append(_is_complex(s, tokens_lower))
        if tokens_lower:
            first_word_match = re.match(r"\s*(\S+)", s)
            openers.append(_opener_category(first_word_match.group(1) if first_word_match else ""))

        if length > 35:
            flagged.append({"text": s.strip(), "reason": f"Very long sentence ({length} words)"})
        elif length < 5:
            flagged.append({"text": s.strip(), "reason": f"Very short/fragment-like ({length} words)"})

    complex_pct = 100 * sum(complex_flags) / len(raw_sents)

    distinct_openers = len(set(openers))
    opener_variation_pct = min(100.0, 100 * distinct_openers / max(1, min(len(raw_sents), 6)))

    return {
        "sentence_count": len(raw_sents),
        "mean_length": round(mean_len, 2),
        "median_length": round(statistics.median(lengths), 2),
        "stdev_length": round(stdev_len, 2),
        "cv": round(cv, 3),
        "length_distribution": lengths,
        "complex_sentence_pct": round(complex_pct, 1),
        "opener_variation_pct": round(opener_variation_pct, 1),
        "flagged_sentences": flagged[:15],
    }

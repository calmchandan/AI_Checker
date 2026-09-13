"""
sentence_analysis.py
Sentence length, complexity, and structural variation.
"""

import statistics
from text_utils import get_nlp, word_count


def analyze_sentences(text: str) -> dict:
    nlp = get_nlp()
    doc = nlp(text)
    sents = [s for s in doc.sents if s.text.strip()]

    lengths = [word_count(s.text) for s in sents]
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

    # Structural complexity: sentences with a subordinate/relative clause
    # or more than one independent clause (coordinated main verbs).
    complex_flags = []
    openers = []
    flagged = []
    for s, length in zip(sents, lengths):
        has_subclause = any(tok.dep_ in ("advcl", "relcl", "ccomp", "csubj") for tok in s)
        conj_roots = sum(1 for tok in s if tok.dep_ == "conj" and tok.pos_ == "VERB")
        is_complex = has_subclause or conj_roots > 0
        complex_flags.append(is_complex)

        first_tok = s[0]
        openers.append(first_tok.pos_)

        if length > 35:
            flagged.append({"text": s.text.strip(), "reason": f"Very long sentence ({length} words)"})
        elif length < 5:
            flagged.append({"text": s.text.strip(), "reason": f"Very short/fragment-like ({length} words)"})

    complex_pct = 100 * sum(complex_flags) / len(sents)

    # Opener variation: how many distinct POS-types start sentences,
    # relative to a "monotonous" baseline where every sentence starts the
    # same way.
    distinct_openers = len(set(openers))
    opener_variation_pct = 100 * distinct_openers / max(1, min(len(sents), 6))
    opener_variation_pct = min(opener_variation_pct, 100.0)

    return {
        "sentence_count": len(sents),
        "mean_length": round(mean_len, 2),
        "median_length": round(statistics.median(lengths), 2),
        "stdev_length": round(stdev_len, 2),
        "cv": round(cv, 3),
        "length_distribution": lengths,
        "complex_sentence_pct": round(complex_pct, 1),
        "opener_variation_pct": round(opener_variation_pct, 1),
        "flagged_sentences": flagged[:15],
    }

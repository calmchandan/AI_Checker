"""
repetition.py
Detects repeated words, phrases, and n-grams (3-grams, 4-grams) as
percentages of total n-gram occurrences, per the spec thresholds.
"""

from collections import Counter
from text_utils import words, normalize_tokens, ngrams


def _repeated_ngram_pct(tokens: list[str], n: int, min_count: int = 2):
    grams = ngrams(tokens, n)
    if not grams:
        return 0.0, []
    counts = Counter(grams)
    repeated = {g: c for g, c in counts.items() if c >= min_count}
    repeated_occurrences = sum(repeated.values())
    pct = 100 * repeated_occurrences / len(grams)
    top = sorted(repeated.items(), key=lambda x: -x[1])[:10]
    top_readable = [{"phrase": " ".join(g), "count": c} for g, c in top]
    return round(pct, 2), top_readable


def analyze_repetition(text: str) -> dict:
    raw_tokens = words(text)
    tokens = normalize_tokens(raw_tokens)

    trigram_pct, top_trigrams = _repeated_ngram_pct(tokens, 3)
    fourgram_pct, top_fourgrams = _repeated_ngram_pct(tokens, 4)

    # Repeated single content words (excluding very short/common function words)
    stop_short = {"the", "a", "an", "of", "to", "in", "and", "is", "are",
                  "was", "were", "for", "on", "at", "as", "it", "that", "this"}
    content_words = [t for t in tokens if t not in stop_short and len(t) > 3]
    word_counts = Counter(content_words)
    overused_words = [
        {"word": w, "count": c} for w, c in word_counts.most_common(10) if c >= 5
    ]

    return {
        "repeated_trigram_pct": trigram_pct,
        "repeated_fourgram_pct": fourgram_pct,
        "top_repeated_trigrams": top_trigrams,
        "top_repeated_fourgrams": top_fourgrams,
        "overused_words": overused_words,
    }

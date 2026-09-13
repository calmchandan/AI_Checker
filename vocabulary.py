"""
vocabulary.py
Vocabulary diversity: raw TTR plus length-robust measures (MTLD, HD-D),
which the spec calls for on longer documents where raw TTR degrades.
"""

import math
import random
from collections import Counter
from text_utils import words, normalize_tokens
from config import RANDOM_SEED


def _ttr(tokens: list[str]) -> float:
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)


def _mtld_one_direction(tokens: list[str], ttr_threshold: float = 0.72) -> float:
    """Measure of Textual Lexical Diversity (McCarthy & Jarvis, 2010)."""
    if not tokens:
        return 0.0
    factor_count = 0
    types = set()
    token_count = 0
    for tok in tokens:
        types.add(tok)
        token_count += 1
        ttr = len(types) / token_count
        if ttr <= ttr_threshold:
            factor_count += 1
            types = set()
            token_count = 0
    # partial factor for remaining tokens
    if token_count > 0:
        ttr = len(types) / token_count
        partial = (1 - ttr) / (1 - ttr_threshold) if ttr_threshold != 1 else 0
        factor_count += min(max(partial, 0), 1)
    if factor_count == 0:
        return len(tokens)
    return len(tokens) / factor_count


def _mtld(tokens: list[str]) -> float:
    if len(tokens) < 10:
        return float(len(set(tokens)))
    forward = _mtld_one_direction(tokens)
    backward = _mtld_one_direction(list(reversed(tokens)))
    return round((forward + backward) / 2, 2)


def _hdd(tokens: list[str], sample_size: int = 42, trials: int = 30) -> float:
    """
    HD-D (McCarthy & Jarvis, 2007): approximates the hypergeometric
    probability of each type appearing in a random sample, via repeated
    sub-sampling (a common practical approximation).
    """
    n = len(tokens)
    if n < sample_size:
        return round(_ttr(tokens), 3)
    rng = random.Random(RANDOM_SEED)
    counts = Counter(tokens)
    total_contrib = 0.0
    for _ in range(trials):
        sample = rng.sample(tokens, sample_size)
        total_contrib += len(set(sample)) / sample_size
    return round(total_contrib / trials, 3)


def analyze_vocabulary(text: str) -> dict:
    raw_tokens = words(text)
    tokens = normalize_tokens(raw_tokens)
    n = len(tokens)

    ttr = _ttr(tokens)
    mtld = _mtld(tokens)
    hdd = _hdd(tokens)

    counts = Counter(tokens)
    most_common = counts.most_common(15)
    unique_words = len(counts)

    return {
        "token_count": n,
        "unique_word_count": unique_words,
        "ttr": round(ttr, 3),
        "mtld": mtld,
        "hdd": hdd,
        "top_words": most_common,
        "recommended_metric": "MTLD/HD-D" if n > 400 else "TTR",
    }

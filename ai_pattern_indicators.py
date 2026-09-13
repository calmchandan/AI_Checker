"""
ai_pattern_indicators.py

Heuristic indicators of AI-typical writing PATTERNS — burstiness, word-choice
predictability, structural uniformity, and generic phrasing density.

READ THIS BEFORE USING THIS MODULE'S OUTPUT FOR ANY DECISION:

1. This is NOT an AI detector. There is no reliable way — from text alone —
   to determine whether a human or a model wrote it, and every vendor that
   claims otherwise (Turnitin's AI score, GPTZero, etc.) has published,
   nontrivial false-positive rates, especially on:
     - non-native English writers (their prose is often more uniform/
       formulaic because it's learned from textbooks and templates)
     - technical/legal/scientific writing (naturally low burstiness,
       naturally high hedging and passive voice)
     - heavily-edited human writing (a careful human editor also reduces
       "burstiness" and removes idiosyncrasy)
     - short texts (all statistical signal here gets noisier below ~300
       words; treat anything under that as not meaningfully scoreable)

2. The score below is a composite of surface statistics that CORRELATE with
   typical LLM output on average, across large samples. Correlation on
   average tells you very little about one specific document. Do not
   present this score to anyone as evidence of misconduct, and do not use
   it as the sole or primary basis for an accusation against a specific
   person. If you are an instructor: use it, at most, as one input that
   might prompt a conversation with the student — never as a verdict.

3. All underlying numbers (burstiness, predictability, repetition, generic
   phrase density) are reported individually and in the same units used
   elsewhere in this report, specifically so you can see WHY the composite
   moved, rather than trusting an opaque single number.
"""

import statistics
from text_utils import words, normalize_tokens

try:
    from wordfreq import zipf_frequency
    _HAS_WORDFREQ = True
except ImportError:
    _HAS_WORDFREQ = False

# Phrases disproportionately common in generic LLM output (not exclusive to
# it — used only as a density signal, same caveat as everywhere else).
_GENERIC_AI_PHRASES = {
    "it is important to note", "it is worth noting", "in today's world",
    "in today's society", "in conclusion", "in summary", "overall,",
    "plays a crucial role", "plays a significant role", "plays a vital role",
    "delve into", "a testament to", "underscores the importance",
    "navigate the complexities", "in the realm of", "furthermore,",
    "moreover,", "additionally,", "on the other hand,", "as a result,",
    "in essence", "it is essential to", "it is crucial to",
    "serves as a reminder", "the ever-evolving", "fast-paced world",
    "in an era of", "at its core", "ultimately,", "in order to fully",
    "holistic approach", "multifaceted", "landscape of",
}


def _burstiness(sentence_lengths: list[int]) -> float:
    """
    Burstiness B = (sigma - mu) / (sigma + mu) over sentence lengths.
    Human writing tends toward B closer to 0 or positive (bursty: mixes
    short/long sentences). Very uniform sentence lengths push B toward -1.
    Range: [-1, 1].
    """
    if len(sentence_lengths) < 3:
        return 0.0
    mu = statistics.fmean(sentence_lengths)
    sigma = statistics.pstdev(sentence_lengths)
    if (sigma + mu) == 0:
        return 0.0
    return round((sigma - mu) / (sigma + mu), 3)


def _predictability_score(tokens: list[str]) -> float:
    """
    Average word-frequency rank (Zipf scale, 0-8ish) across content tokens.
    Higher = text leans on very common, high-frequency words more heavily
    (a mild correlate of lower lexical surprise). Not a real perplexity
    measure — no language model is used here, only static frequency.
    """
    if not _HAS_WORDFREQ or not tokens:
        return 0.0
    freqs = [zipf_frequency(t, "en") for t in tokens if len(t) > 2]
    freqs = [f for f in freqs if f > 0]
    if not freqs:
        return 0.0
    return round(statistics.fmean(freqs), 2)


def _generic_phrase_density(text: str, total_words: int) -> tuple[float, list]:
    text_lower = text.lower()
    hits = []
    count = 0
    for phrase in _GENERIC_AI_PHRASES:
        c = text_lower.count(phrase)
        if c:
            hits.append({"phrase": phrase, "count": c})
            count += c
    density = 100 * count / max(1, total_words)
    return round(density, 2), sorted(hits, key=lambda x: -x["count"])


def _paragraph_uniformity(paragraph_lengths: list[int]) -> float:
    """Coefficient of variation of paragraph lengths; low = very uniform."""
    if len(paragraph_lengths) < 3:
        return 1.0  # not enough data to judge, treat as neutral/high
    mu = statistics.fmean(paragraph_lengths)
    if mu == 0:
        return 1.0
    sigma = statistics.pstdev(paragraph_lengths)
    return round(sigma / mu, 3)


def analyze_ai_patterns(text: str, sentence_lengths: list[int],
                         paragraph_lengths: list[int]) -> dict:
    raw_tokens = words(text)
    tokens = normalize_tokens(raw_tokens)
    total_words = max(1, len(tokens))

    burstiness = _burstiness(sentence_lengths)
    predictability = _predictability_score(tokens)
    generic_density, generic_hits = _generic_phrase_density(text, total_words)
    para_uniformity = _paragraph_uniformity(paragraph_lengths)

    # --- composite heuristic score (0-100, higher = more AI-typical PATTERNS) ---
    # Each component mapped to 0-100 then averaged. All mappings are rough
    # heuristic calibrations, not empirically fitted thresholds.
    burst_component = max(0, min(100, (0 - burstiness) * 100))  # more negative burstiness -> higher
    predict_component = max(0, min(100, (predictability - 3.0) / (5.5 - 3.0) * 100)) if predictability else 0
    generic_component = max(0, min(100, (generic_density / 3.0) * 100))
    uniformity_component = max(0, min(100, (0.5 - min(para_uniformity, 0.5)) / 0.5 * 100))

    components = {
        "sentence_uniformity": round(burst_component, 1),
        "word_predictability": round(predict_component, 1),
        "generic_phrasing": round(generic_component, 1),
        "paragraph_uniformity": round(uniformity_component, 1),
    }
    composite = round(statistics.fmean(components.values()), 1)

    if total_words < 300:
        confidence = "Low — text is too short for these statistics to be meaningful"
    elif total_words < 800:
        confidence = "Moderate — enough text for a rough read, still noisy"
    else:
        confidence = "Higher (but still not proof) — longer text gives more stable statistics"

    return {
        "caveat": (
            "This is a heuristic pattern score, not an AI detector. It reflects "
            "surface statistics that on average correlate with typical LLM output "
            "across large samples, but says very little about any single document. "
            "Non-native English writing, technical/legal writing, and heavily-edited "
            "human prose commonly score in the same range. Do not use this as "
            "evidence in any accusation of misconduct."
        ),
        "composite_pattern_score": composite,
        "confidence_note": confidence,
        "components": components,
        "raw_metrics": {
            "burstiness": burstiness,
            "burstiness_note": "Range -1 to 1. Closer to -1 = more uniform sentence lengths (a pattern common in unedited LLM output).",
            "word_predictability_zipf": predictability,
            "word_predictability_note": "Average word-frequency rank (0-8 Zipf scale). Higher = heavier reliance on very common words.",
            "generic_phrase_density_pct": generic_density,
            "paragraph_uniformity_cv": para_uniformity,
            "paragraph_uniformity_note": "Coefficient of variation of paragraph lengths. Lower = more uniform paragraph sizes.",
        },
        "generic_phrase_hits": generic_hits,
    }

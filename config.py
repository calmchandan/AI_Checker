"""
config.py
Central configuration: thresholds, weights, and word lists used across the
Academic Writing Analyzer. Values are taken directly from the project spec.
"""

# ---------------------------------------------------------------------------
# Metric thresholds (target / flag ranges from spec)
# ---------------------------------------------------------------------------

THRESHOLDS = {
    "mean_sentence_length": {"low": 12, "high": 24, "flag_high": 35},
    "sentence_length_cv":   {"low": 0.35, "high": 0.70, "flag_low": 0.20},
    "repeated_trigrams_pct":  {"target": 2.0, "flag": 5.0},
    "repeated_fourgrams_pct": {"target": 1.0, "flag": 3.0},
    "transition_density_pct": {"low": 2.0, "high": 6.0, "flag": 10.0},
    "ttr": {"low": 0.40, "high": 0.65, "flag_low": 0.30},
    "passive_voice_pct": {"low": 10.0, "high": 30.0, "flag": 45.0},
    "paragraph_length": {"low": 60, "high": 150, "flag_high": 250},
    "filler_density_pct": {"target": 1.0, "flag": 3.0},
}

# ---------------------------------------------------------------------------
# Overall score weights (must sum to 1.0)
# ---------------------------------------------------------------------------

SCORE_WEIGHTS = {
    "sentence_variation": 0.20,
    "vocabulary_diversity": 0.15,
    "repetition": 0.15,
    "specificity": 0.15,
    "readability": 0.10,
    "syntactic_variation": 0.10,
    "paragraph_structure": 0.10,
    "filler_control": 0.05,
}

SCORE_BANDS = [
    (80, 100, "Strong writing characteristics"),
    (65, 79, "Good; minor refinement recommended"),
    (50, 64, "Needs refinement"),
    (0, 49, "Substantial revision recommended"),
]

# ---------------------------------------------------------------------------
# Word / phrase lists
# ---------------------------------------------------------------------------

TRANSITION_WORDS = {
    "however", "moreover", "furthermore", "additionally", "consequently",
    "therefore", "thus", "hence", "nevertheless", "nonetheless",
    "in addition", "as a result", "for instance", "for example",
    "in conclusion", "in summary", "on the other hand", "in contrast",
    "notably", "importantly", "significantly", "overall", "in essence",
    "to summarize", "in other words", "that is to say", "accordingly",
    "subsequently", "likewise", "similarly", "meanwhile", "ultimately",
}

# Generic filler / hedging phrases that tend to inflate word count without
# adding content. This list intentionally overlaps with phrases that are
# common in generic AI-style prose, but the tool never uses it to claim
# authorship — only to flag low-specificity padding.
FILLER_PHRASES = {
    "it is important to note that", "it should be noted that",
    "in today's world", "in today's society", "in the modern era",
    "plays a crucial role", "plays a vital role", "plays a significant role",
    "it is worth mentioning", "needless to say", "at the end of the day",
    "when it comes to", "in order to", "due to the fact that",
    "a wide range of", "a variety of", "in the realm of",
    "serves as a", "stands as a", "is a testament to",
    "underscores the importance of", "highlights the importance of",
    "delve into", "deep dive into", "shed light on", "pave the way for",
    "in a nutshell", "all in all", "with that being said",
    "it goes without saying", "the fact of the matter is",
}

# Auxiliary verbs used for passive-voice detection (be + past participle)
PASSIVE_AUX = {"is", "are", "was", "were", "be", "been", "being", "am"}

# Vague quantifiers that reduce specificity when unaccompanied by numbers
VAGUE_QUANTIFIERS = {
    "many", "several", "various", "numerous", "some", "a lot of",
    "a number of", "many people", "some people", "researchers",
    "studies show", "experts say", "it is believed", "generally",
}

RANDOM_SEED = 13

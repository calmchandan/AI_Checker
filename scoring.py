"""
scoring.py
Combines individual metric results into transparent 0-100 sub-scores and
the overall weighted Academic Writing Quality Score, per the spec's
component weighting.
"""

from config import SCORE_WEIGHTS, SCORE_BANDS, THRESHOLDS


def _band_score(value, low, high, flag_low=None, flag_high=None, higher_is_worse_beyond_high=True):
    """
    Generic scorer: 100 within [low, high]; degrades linearly toward 0 as
    the value moves toward (or past) the flag threshold on either side.
    """
    if low <= value <= high:
        return 100.0
    if value < low:
        floor = flag_low if flag_low is not None else 0
        if value <= floor:
            return 0.0
        return 100 * (value - floor) / (low - floor)
    else:  # value > high
        ceiling = flag_high if flag_high is not None else high * 2
        if value >= ceiling:
            return 0.0
        return 100 * (ceiling - value) / (ceiling - high)


def compute_subscores(sentence, vocab, repetition, specificity, readability,
                       style, paragraphs) -> dict:
    t = THRESHOLDS

    sentence_variation = _band_score(
        sentence["cv"], t["sentence_length_cv"]["low"], t["sentence_length_cv"]["high"],
        flag_low=t["sentence_length_cv"]["flag_low"], flag_high=1.2,
    )
    # Penalize extreme mean length separately, then average
    mean_len_score = _band_score(
        sentence["mean_length"], t["mean_sentence_length"]["low"], t["mean_sentence_length"]["high"],
        flag_low=4, flag_high=t["mean_sentence_length"]["flag_high"],
    )
    sentence_variation = round((sentence_variation + mean_len_score) / 2, 1)

    vocab_metric = vocab["mtld"] if vocab["recommended_metric"] == "MTLD/HD-D" else vocab["ttr"] * 100
    if vocab["recommended_metric"] == "MTLD/HD-D":
        # MTLD typically ranges ~40-100+ for varied text; scale heuristically
        vocabulary_diversity = round(min(100, max(0, (vocab_metric - 30) / (90 - 30) * 100)), 1)
    else:
        vocabulary_diversity = round(_band_score(
            vocab["ttr"], t["ttr"]["low"], t["ttr"]["high"], flag_low=t["ttr"]["flag_low"], flag_high=0.85
        ), 1)

    tri = repetition["repeated_trigram_pct"]
    four = repetition["repeated_fourgram_pct"]
    tri_score = max(0, 100 - (tri / t["repeated_trigrams_pct"]["flag"]) * 100) if tri > t["repeated_trigrams_pct"]["target"] else 100
    four_score = max(0, 100 - (four / t["repeated_fourgrams_pct"]["flag"]) * 100) if four > t["repeated_fourgrams_pct"]["target"] else 100
    repetition_score = round((tri_score + four_score) / 2, 1)

    specificity_score = round(specificity["specificity_score"], 1)

    fre = readability["flesch_reading_ease"]
    readability_score = round(_band_score(fre, 30, 60, flag_low=0, flag_high=90), 1)

    syntactic_variation = round(sentence["opener_variation_pct"] * 0.6 + sentence["complex_sentence_pct"] * 0.4, 1)
    syntactic_variation = min(100.0, syntactic_variation)

    lengths = paragraphs["lengths"]
    if lengths:
        within = sum(1 for l in lengths if t["paragraph_length"]["low"] <= l <= t["paragraph_length"]["high"])
        paragraph_structure = round(100 * within / len(lengths), 1)
        if paragraphs["unsupported_paragraph_count"]:
            paragraph_structure = round(paragraph_structure * 0.85, 1)
    else:
        paragraph_structure = 0.0

    filler = style["filler_density_pct"]
    filler_control = round(max(0, 100 - (filler / t["filler_density_pct"]["flag"]) * 100) if filler > t["filler_density_pct"]["target"] else 100, 1)

    return {
        "sentence_variation": sentence_variation,
        "vocabulary_diversity": vocabulary_diversity,
        "repetition": repetition_score,
        "specificity": specificity_score,
        "readability": readability_score,
        "syntactic_variation": syntactic_variation,
        "paragraph_structure": paragraph_structure,
        "filler_control": filler_control,
    }


def compute_overall_score(subscores: dict) -> dict:
    overall = sum(subscores[k] * w for k, w in SCORE_WEIGHTS.items())
    overall = round(overall, 1)
    label = next((lbl for lo, hi, lbl in SCORE_BANDS if lo <= overall < hi + 1), "Unscored")
    return {"overall_score": overall, "interpretation": label}

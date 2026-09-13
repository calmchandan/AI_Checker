"""
readability.py
Established readability measures via textstat: Flesch Reading Ease,
Flesch-Kincaid Grade, Gunning Fog, and SMOG (appropriate for academic text).
"""

import textstat


def analyze_readability(text: str) -> dict:
    if not text.strip():
        return {
            "flesch_reading_ease": 0, "flesch_kincaid_grade": 0,
            "gunning_fog": 0, "smog_index": 0, "interpretation": "No text",
        }

    fre = textstat.flesch_reading_ease(text)
    fkg = textstat.flesch_kincaid_grade(text)
    fog = textstat.gunning_fog(text)
    smog = textstat.smog_index(text)

    # Academic writing generally sits in "difficult"/"fairly difficult"
    # Flesch bands (30-50); flag only extremes.
    if fre >= 60:
        interp = "Reads easier than typical academic prose — check for oversimplification."
    elif fre >= 30:
        interp = "Consistent with typical academic/technical writing difficulty."
    else:
        interp = "Very dense — consider shortening some sentences for clarity."

    return {
        "flesch_reading_ease": round(fre, 1),
        "flesch_kincaid_grade": round(fkg, 1),
        "gunning_fog": round(fog, 1),
        "smog_index": round(smog, 1),
        "interpretation": interp,
    }

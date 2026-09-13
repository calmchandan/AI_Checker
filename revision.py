"""
revision.py
Generates transparent, rule-based revision suggestions tied directly to
flagged metrics. Also provides an optional "mechanical clean pass" that
strips detected filler phrases only — it never rewrites sentences,
invents content, or paraphrases, so facts, citations, and terminology are
guaranteed to survive untouched. Full rewriting is a job for the author
(or a human/LLM editor working sentence-by-sentence), not a rule engine.
"""

import re
from config import FILLER_PHRASES


def generate_suggestions(report: dict) -> list[dict]:
    suggestions = []
    s = report["sentence_analysis"]
    v = report["vocabulary"]
    r = report["repetition"]
    sp = report["specificity"]
    rd = report["readability"]
    st = report["style"]
    pg = report["paragraphs"]

    if s["cv"] < 0.20:
        suggestions.append({
            "area": "Sentence variation",
            "issue": f"Low sentence-length variation (CV={s['cv']}).",
            "suggestion": "Mix short and long sentences deliberately — break up runs of "
                           "similarly-sized sentences with one short, direct statement.",
        })
    if s["mean_length"] > 35:
        suggestions.append({
            "area": "Sentence length",
            "issue": f"Mean sentence length is {s['mean_length']} words.",
            "suggestion": "Split the longest sentences (see flagged list) at coordinating "
                           "conjunctions or subordinate clause boundaries.",
        })

    if v["recommended_metric"] == "TTR" and v["ttr"] < 0.30:
        suggestions.append({
            "area": "Vocabulary diversity",
            "issue": f"TTR is {v['ttr']}, below the 0.30 floor.",
            "suggestion": "Replace repeated general terms with more precise synonyms or "
                           "domain-specific vocabulary where meaning allows.",
        })
    elif v["recommended_metric"] == "MTLD/HD-D" and v["mtld"] < 50:
        suggestions.append({
            "area": "Vocabulary diversity",
            "issue": f"MTLD is {v['mtld']}, indicating limited lexical range for a document this long.",
            "suggestion": "Vary word choice for frequently repeated concepts; check the "
                           "top-words list for over-relied-on terms.",
        })

    if r["repeated_trigram_pct"] > 5:
        suggestions.append({
            "area": "Repetition",
            "issue": f"{r['repeated_trigram_pct']}% of 3-grams are repeated (target <2%).",
            "suggestion": "Reword the repeated phrases listed in the report; keep one instance "
                           "and rephrase the rest.",
        })

    if sp["specificity_score"] < 50:
        suggestions.append({
            "area": "Specificity",
            "issue": "Low density of named entities, numbers, or domain terminology.",
            "suggestion": "Add concrete examples, named sources, dates, or figures to back up "
                           "general claims. Watch for vague quantifiers like 'many' or 'several' "
                           "without a number or citation nearby.",
        })

    if st["passive_voice_pct"] > 45:
        suggestions.append({
            "area": "Passive voice",
            "issue": f"{st['passive_voice_pct']}% of sentences are passive (target 10-30%).",
            "suggestion": "Convert flagged passive sentences to active voice where the actor "
                           "is known and relevant.",
        })

    if st["transition_density_pct"] > 10:
        suggestions.append({
            "area": "Transitions",
            "issue": f"Transition-word density is {st['transition_density_pct']}% (target 2-6%).",
            "suggestion": "Remove mechanical connectors (e.g. 'furthermore', 'moreover') where "
                           "the logical link is already clear from context.",
        })

    if st["filler_density_pct"] > 3:
        suggestions.append({
            "area": "Filler",
            "issue": f"Filler-phrase density is {st['filler_density_pct']}% (target <1%).",
            "suggestion": "Cut generic filler phrases (see list) — they add length without content.",
        })

    if pg["unsupported_paragraph_count"] > 0:
        suggestions.append({
            "area": "Paragraph evidence",
            "issue": f"{pg['unsupported_paragraph_count']} paragraph(s) over 60 words have no "
                     "detected citation or numeric evidence.",
            "suggestion": "Add a citation, data point, or concrete example to substantiate the "
                          "paragraph's central claim.",
        })

    if rd["flesch_reading_ease"] >= 60:
        suggestions.append({
            "area": "Readability",
            "issue": "Text reads easier than typical academic prose.",
            "suggestion": "Check whether simplification has cost precision — academic register "
                           "often needs more qualified, technical phrasing.",
        })

    return suggestions


def mechanical_clean_pass(text: str) -> tuple[str, list[str]]:
    """
    Removes only exact filler-phrase matches (case-insensitive), leaving
    everything else — facts, numbers, citations, terminology — untouched.
    Returns (cleaned_text, list_of_removed_phrases).
    """
    removed = []
    cleaned = text
    for phrase in sorted(FILLER_PHRASES, key=len, reverse=True):
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        matches = pattern.findall(cleaned)
        if matches:
            removed.extend(matches)
            cleaned = pattern.sub("", cleaned)
    # tidy up double spaces / stray punctuation left by removals
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([,.;:])", r"\1", cleaned)
    cleaned = re.sub(r"^\s*[,.;:]\s*", "", cleaned, flags=re.MULTILINE)
    return cleaned.strip(), removed

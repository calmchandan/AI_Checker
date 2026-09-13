"""
paragraph_analysis.py
Paragraph-level structure: length distribution and a lightweight evidence-
support check (does each paragraph contain a claim backed by a number,
entity, or citation-like marker?).
"""

import re
from text_utils import split_paragraphs, word_count

_CITATION_RE = re.compile(r"\(([A-Z][a-zA-Z]+(?:\s(?:et al\.|&|and)\s[A-Z][a-zA-Z]+)?,?\s*\d{4}[a-z]?)\)|\[\d+\]")
_NUMBER_RE = re.compile(r"\b\d+(?:[.,]\d+)?%?\b")


def analyze_paragraphs(text: str) -> dict:
    paras = split_paragraphs(text)
    if not paras:
        return {
            "paragraph_count": 0, "lengths": [], "mean_length": 0,
            "flagged_paragraphs": [], "unsupported_paragraph_count": 0,
        }

    lengths = [word_count(p) for p in paras]
    flagged = []
    unsupported = 0

    for p, length in zip(paras, lengths):
        has_citation = bool(_CITATION_RE.search(p))
        has_number = bool(_NUMBER_RE.search(p))
        has_evidence = has_citation or has_number

        reasons = []
        if length > 250:
            reasons.append(f"Very long paragraph ({length} words) — consider splitting")
        elif length < 30:
            reasons.append(f"Very short paragraph ({length} words) — may be underdeveloped")
        if not has_evidence and length > 60:
            reasons.append("No citation or numeric evidence detected for a paragraph of this length")
            unsupported += 1

        if reasons:
            flagged.append({"preview": p[:120] + ("..." if len(p) > 120 else ""),
                             "length": length, "reasons": reasons})

    return {
        "paragraph_count": len(paras),
        "lengths": lengths,
        "mean_length": round(sum(lengths) / len(lengths), 1),
        "flagged_paragraphs": flagged[:15],
        "unsupported_paragraph_count": unsupported,
    }

"""
analyzer.py
Orchestrates all sub-modules into a single report dict, ready for the
dashboard or for JSON/CSV/TXT export.

Scope note (per project spec): this tool evaluates writing-quality
characteristics only. It does not estimate or claim to detect whether text
was written by AI, and it is not designed to help evade Turnitin, GPT
detectors, or other academic-integrity systems.
"""

import datetime
from text_utils import word_count, split_paragraphs
from sentence_analysis import analyze_sentences
from vocabulary import analyze_vocabulary
from repetition import analyze_repetition
from readability import analyze_readability
from specificity import analyze_specificity
from style_rules import analyze_style
from paragraph_analysis import analyze_paragraphs
from scoring import compute_subscores, compute_overall_score
from revision import generate_suggestions
from ai_pattern_indicators import analyze_ai_patterns


def run_analysis(text: str, filename: str = "") -> dict:
    text = text.strip()
    sentence = analyze_sentences(text)
    vocab = analyze_vocabulary(text)
    repetition = analyze_repetition(text)
    readability = analyze_readability(text)
    specificity = analyze_specificity(text)
    style = analyze_style(text)
    paragraphs = analyze_paragraphs(text)

    subscores = compute_subscores(sentence, vocab, repetition, specificity,
                                   readability, style, paragraphs)
    overall = compute_overall_score(subscores)
    ai_patterns = analyze_ai_patterns(
        text,
        sentence_lengths=sentence["length_distribution"],
        paragraph_lengths=paragraphs["lengths"],
    )

    report = {
        "meta": {
            "filename": filename,
            "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "word_count": word_count(text),
            "sentence_count": sentence["sentence_count"],
            "paragraph_count": paragraphs["paragraph_count"],
            "scope_note": (
                "This report includes writing-quality metrics plus a heuristic "
                "'AI-writing-pattern' section. Neither section determines or proves "
                "whether text was written by AI — see the caveat inside the "
                "ai_pattern_indicators section before using or sharing that score."
            ),
        },
        "sentence_analysis": sentence,
        "vocabulary": vocab,
        "repetition": repetition,
        "readability": readability,
        "specificity": specificity,
        "style": style,
        "paragraphs": paragraphs,
        "subscores": subscores,
        "overall": overall,
        "ai_pattern_indicators": ai_patterns,
    }
    report["suggestions"] = generate_suggestions(report)
    return report


if __name__ == "__main__":
    import sys
    import json
    if len(sys.argv) < 2:
        print("Usage: python analyzer.py <path_to_text_file>")
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        content = f.read()
    result = run_analysis(content, filename=sys.argv[1])
    print(json.dumps(result, indent=2, default=str))

"""
file_io.py
Loading text from uploaded files (TXT / DOCX / PDF) and exporting reports
to TXT / CSV / JSON, per the spec's "Recommended Output" section.
"""

import io
import json
import csv


def load_text_from_upload(uploaded_file) -> str:
    """
    uploaded_file: a Streamlit UploadedFile (has .name and .read()/.getvalue()).
    """
    name = uploaded_file.name.lower()
    data = uploaded_file.getvalue()

    if name.endswith(".txt") or name.endswith(".md"):
        return data.decode("utf-8", errors="replace")

    if name.endswith(".docx"):
        from docx import Document
        doc = Document(io.BytesIO(data))
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())

    if name.endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages)

    raise ValueError(f"Unsupported file type: {uploaded_file.name}. "
                      f"Supported: .txt, .md, .docx, .pdf")


def export_json(report: dict) -> bytes:
    return json.dumps(report, indent=2, default=str).encode("utf-8")


def export_txt(report: dict) -> bytes:
    lines = []
    m = report["meta"]
    lines.append(f"Academic Writing Analysis Report")
    lines.append(f"File: {m.get('filename', 'N/A')}")
    lines.append(f"Generated: {m['generated_at']}")
    lines.append(f"Words: {m['word_count']} | Sentences: {m['sentence_count']} | Paragraphs: {m['paragraph_count']}")
    lines.append("")
    lines.append(f"OVERALL SCORE: {report['overall']['overall_score']} / 100 "
                 f"({report['overall']['interpretation']})")
    lines.append("")
    lines.append("Sub-scores:")
    for k, v in report["subscores"].items():
        lines.append(f"  - {k.replace('_', ' ').title()}: {v}")
    lines.append("")
    lines.append("Key metrics:")
    lines.append(f"  - Mean sentence length: {report['sentence_analysis']['mean_length']} words")
    lines.append(f"  - Sentence-length CV: {report['sentence_analysis']['cv']}")
    lines.append(f"  - TTR: {report['vocabulary']['ttr']} | MTLD: {report['vocabulary']['mtld']}")
    lines.append(f"  - Repeated 3-grams: {report['repetition']['repeated_trigram_pct']}%")
    lines.append(f"  - Repeated 4-grams: {report['repetition']['repeated_fourgram_pct']}%")
    lines.append(f"  - Passive voice: {report['style']['passive_voice_pct']}%")
    lines.append(f"  - Transition density: {report['style']['transition_density_pct']}%")
    lines.append(f"  - Filler density: {report['style']['filler_density_pct']}%")
    lines.append(f"  - Flesch Reading Ease: {report['readability']['flesch_reading_ease']}")
    lines.append("")
    ai = report["ai_pattern_indicators"]
    lines.append(f"AI-WRITING-PATTERN INDICATORS (heuristic — see caveat below, NOT a detector)")
    lines.append(f"  Composite pattern score: {ai['composite_pattern_score']} / 100  "
                 f"(confidence: {ai['confidence_note']})")
    for k, v in ai["components"].items():
        lines.append(f"  - {k.replace('_', ' ').title()}: {v}")
    lines.append(f"  CAVEAT: {ai['caveat']}")
    lines.append("")
    lines.append("Suggestions:")
    for s in report["suggestions"]:
        lines.append(f"  [{s['area']}] {s['issue']}")
        lines.append(f"    -> {s['suggestion']}")
    lines.append("")
    lines.append(f"Scope note: {m['scope_note']}")
    return "\n".join(lines).encode("utf-8")


def export_csv(report: dict) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["metric", "value"])
    writer.writerow(["overall_score", report["overall"]["overall_score"]])
    writer.writerow(["interpretation", report["overall"]["interpretation"]])
    for k, v in report["subscores"].items():
        writer.writerow([f"subscore_{k}", v])
    flat_metrics = {
        "word_count": report["meta"]["word_count"],
        "sentence_count": report["meta"]["sentence_count"],
        "paragraph_count": report["meta"]["paragraph_count"],
        "mean_sentence_length": report["sentence_analysis"]["mean_length"],
        "sentence_length_cv": report["sentence_analysis"]["cv"],
        "ttr": report["vocabulary"]["ttr"],
        "mtld": report["vocabulary"]["mtld"],
        "repeated_trigram_pct": report["repetition"]["repeated_trigram_pct"],
        "repeated_fourgram_pct": report["repetition"]["repeated_fourgram_pct"],
        "passive_voice_pct": report["style"]["passive_voice_pct"],
        "transition_density_pct": report["style"]["transition_density_pct"],
        "filler_density_pct": report["style"]["filler_density_pct"],
        "flesch_reading_ease": report["readability"]["flesch_reading_ease"],
        "specificity_score": report["specificity"]["specificity_score"],
        "ai_pattern_composite_score": report["ai_pattern_indicators"]["composite_pattern_score"],
        "ai_pattern_burstiness": report["ai_pattern_indicators"]["raw_metrics"]["burstiness"],
        "ai_pattern_word_predictability_zipf": report["ai_pattern_indicators"]["raw_metrics"]["word_predictability_zipf"],
        "ai_pattern_generic_phrase_density_pct": report["ai_pattern_indicators"]["raw_metrics"]["generic_phrase_density_pct"],
    }
    for k, v in flat_metrics.items():
        writer.writerow([k, v])
    return buf.getvalue().encode("utf-8")

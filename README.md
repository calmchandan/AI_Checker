# Academic Writing Analyzer & Natural Writing Optimizer

A local Python/Streamlit dashboard that evaluates academic writing quality:
sentence structure, vocabulary diversity, repetition, readability,
specificity, passive voice, paragraph structure, and filler density — with
a transparent 0–100 score and revision suggestions.

**Scope:** This tool does not determine, estimate, or imply whether text was
AI-written, and it is not designed to help evade Turnitin, GPT detectors, or
other academic-integrity systems. It only measures writing-quality
characteristics that any writer — human or otherwise — can act on.

## Setup

```bash
cd academic_writer
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

No spaCy model download step — this version has no spaCy/C-extension
dependency at all (see "Why no spaCy" below), so install is just the one
`pip install` command, and it deploys reliably on hosted platforms like
Streamlit Community Cloud regardless of what Python version they run.

## Run the dashboard

```bash
streamlit run app.py
```

This opens a browser tab (usually `http://localhost:8501`) where you can
upload a `.txt`, `.md`, `.docx`, or `.pdf` file, or paste text directly.

## Run from the command line (no UI)

```bash
python analyzer.py path/to/essay.txt > report.json
```

## Project structure

```
academic_writer/
├── app.py                # Streamlit dashboard
├── analyzer.py            # Orchestrates all modules -> single report dict
├── config.py               # All thresholds, weights, word lists
├── text_utils.py            # Shared tokenization / spaCy loader
├── sentence_analysis.py      # Sentence length, complexity, structure
├── vocabulary.py               # TTR, MTLD, HD-D
├── repetition.py                 # Repeated n-grams / words
├── readability.py                  # Flesch, Flesch-Kincaid, Fog, SMOG
├── specificity.py                    # Entities, numbers, domain terms, vague quantifiers
├── style_rules.py                      # Transitions, filler phrases, passive voice
├── paragraph_analysis.py                 # Paragraph length + evidence-support check
├── scoring.py                              # Weighted 0-100 overall score
├── revision.py                               # Suggestions + mechanical filler-removal pass
├── file_io.py                                  # Upload parsing (docx/pdf/txt) + export (json/txt/csv)
└── requirements.txt
```

## Why no spaCy

Earlier versions used spaCy for sentence parsing, passive-voice detection,
and entity recognition. spaCy's dependency `blis` has no prebuilt wheel on
several current Python versions and fails to build from source when it
falls back to compiling — which is exactly what broke deployment on
Streamlit Community Cloud once their base image moved to a newer Python.
Since hosted platforms can bump their Python version without notice, this
version replaces spaCy entirely with regex/word-list heuristics for the
same three features (see `sentence_analysis.py`, `style_rules.py`,
`specificity.py` docstrings for the exact trade-offs — they're slightly
less precise than a true parse, but dependency-free and won't break again
on a platform Python bump).

## Key metrics & thresholds

| Metric | Target | Flag |
|---|---|---|
| Mean sentence length | 12–24 words | >35 words |
| Sentence-length CV | 0.35–0.70 | <0.20 |
| Repeated 3-grams | <2% | >5% |
| Repeated 4-grams | <1% | >3% |
| Transition density | 2–6% | >10% |
| TTR (short docs) | 0.40–0.65 | <0.30 |
| Passive voice | 10–30% | >45% |
| Paragraph length | 60–150 words | >250 words |
| Filler density | <1% | >3% |

For documents over ~400 words, the dashboard automatically switches the
vocabulary-diversity headline metric from raw TTR to MTLD/HD-D, since TTR
degrades as document length grows.

## AI-writing-pattern indicators (read before using)

The **AI Pattern Indicators** tab reports a heuristic 0–100 score built from
four surface statistics that, *on average, across large samples*, correlate
with typical LLM output: sentence-length uniformity (burstiness), word-choice
predictability (static frequency, not a real language-model perplexity),
generic/hedge-phrase density, and paragraph-length uniformity.

**This is not an AI detector and cannot prove authorship.** The same
patterns show up routinely in:
- non-native English writing (often more uniform/formulaic)
- technical, legal, or scientific writing (naturally low burstiness, high hedging)
- heavily-edited human prose (editing itself reduces idiosyncrasy)
- anything under ~300 words (too little signal to be meaningful — the
  dashboard labels these as "Low confidence")

Every commercial AI-detector (Turnitin's AI score, GPTZero, etc.) has
published, non-trivial false-positive rates for exactly these reasons. Use
this tab, if at all, as one prompt for a human conversation — never as
standalone evidence in an academic-integrity accusation.

## Notes on the "revision" feature

`revision.py` generates suggestions tied to specific flagged metrics, and a
separate **mechanical clean pass** that strips only exact filler-phrase
matches (e.g. "it is important to note that"). It deliberately does **not**
auto-rewrite sentences or paraphrase content — that would risk altering
facts, citations, or intended meaning. Treat the suggestions tab as a
checklist for your own edit pass, not an auto-fix button.

## Extending it

- Swap in `language_tool_python` for grammar checks (optional dependency
  named in the original spec).
- Add a domain-specific term list in `config.py` if you want specificity
  scoring tuned to a particular field (e.g. finance, banking, law).
- The scoring weights and thresholds are all in one place (`config.py`) —
  adjust them to match your institution's style guide.

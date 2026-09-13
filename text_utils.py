"""
text_utils.py
Shared helpers: sentence/paragraph splitting and tokenization.

No spaCy dependency (intentionally). spaCy's `blis` dependency has no
prebuilt wheel on several current Python versions and fails to build from
source on hosted platforms like Streamlit Cloud, which pin whatever Python
version their base image ships. Everything here is pure-Python regex/rule
based so the app deploys reliably regardless of the host's Python version.
"""

import re
import regex

_WORD_RE = regex.compile(r"[A-Za-z']+")

# Common abbreviations that should NOT be treated as sentence boundaries.
_ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "vs", "etc",
    "eg", "ie", "us", "uk", "inc", "ltd", "co", "fig", "no", "vol",
    "approx", "govt", "dept", "univ", "assn", "rs",
}

_SENTENCE_BOUNDARY = re.compile(r'(?<=[.!?])["\')\]]?\s+(?=[A-Z"\'(])')


def split_sentences(text: str) -> list[str]:
    """
    Rule-based sentence splitter: splits on ./!/? followed by whitespace and
    a capital letter (or quote/paren), then merges back splits that were
    actually just an abbreviation followed by a capitalized word.
    """
    text = text.strip()
    if not text:
        return []

    raw_chunks = _SENTENCE_BOUNDARY.split(text)
    sentences = []
    buffer = ""

    for chunk in raw_chunks:
        buffer = f"{buffer} {chunk}".strip() if buffer else chunk
        trailing_word = re.findall(r"([A-Za-z]+)\.\s*$", buffer)
        if trailing_word and trailing_word[-1].lower() in _ABBREVIATIONS:
            continue  # don't finalize yet -- likely a false split
        # also avoid splitting on a single capital-letter initial, e.g. "J. Smith"
        if re.search(r"\b[A-Z]\.\s*$", buffer):
            continue
        sentences.append(buffer.strip())
        buffer = ""

    if buffer:
        sentences.append(buffer.strip())

    return [s for s in sentences if s]


def split_paragraphs(text: str) -> list[str]:
    """Split on blank lines; fall back to single-newline if no blank lines exist."""
    text = text.replace("\r\n", "\n").strip()
    if not text:
        return []
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(paras) <= 1 and "\n" in text:
        paras = [p.strip() for p in text.split("\n") if p.strip()]
    return paras


def words(text: str) -> list[str]:
    return _WORD_RE.findall(text)


def word_count(text: str) -> int:
    return len(words(text))


def ngrams(tokens: list[str], n: int) -> list[tuple]:
    return [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def normalize_tokens(tokens: list[str]) -> list[str]:
    return [t.lower() for t in tokens]

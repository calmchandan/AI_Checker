"""
text_utils.py
Shared helpers: sentence/paragraph splitting, tokenization, and the single
spaCy pipeline instance used across modules (loaded once, lazily).
"""

import re
import regex
from functools import lru_cache

_WORD_RE = regex.compile(r"[A-Za-z']+")


@lru_cache(maxsize=1)
def get_nlp():
    """Load the spaCy pipeline once and reuse it everywhere."""
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError as e:
        raise RuntimeError(
            "spaCy model 'en_core_web_sm' is not installed. Run:\n"
            "  python -m spacy download en_core_web_sm"
        ) from e
    return nlp


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

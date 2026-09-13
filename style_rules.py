"""
style_rules.py
Transition-word density, filler-phrase density, and passive-voice
percentage — via regex/word-list heuristics (no spaCy dependency; see
text_utils.py for why).

Passive voice detection: a be-verb (is/are/was/were/be/been/being/am)
followed within a few words by a past-participle-shaped word (ends in
"-ed", or is a known irregular past participle). This is the same class of
heuristic used by common rule-based grammar linters. It will miss some
passives and occasionally flag an adjectival "-ed" as passive (e.g. "was
excited") — a known trade-off of avoiding a full parse.
"""

import re
from text_utils import split_sentences, word_count
from config import TRANSITION_WORDS, FILLER_PHRASES

_BE_FORMS = {"is", "are", "was", "were", "be", "been", "being", "am"}
_IRREGULAR_PAST_PARTICIPLES = {
    "done", "made", "given", "taken", "seen", "known", "shown", "written",
    "spoken", "broken", "chosen", "driven", "eaten", "fallen", "forgotten",
    "gotten", "hidden", "ridden", "risen", "stolen", "thrown", "worn",
    "born", "built", "bought", "brought", "caught", "dealt", "felt",
    "found", "fought", "held", "kept", "left", "lent", "lost", "meant",
    "met", "paid", "said", "sent", "sold", "sought", "taught", "told",
    "understood", "won", "led", "read", "sat", "spent", "stood", "struck",
    "swept", "thought", "hit", "hurt", "cut", "cost", "put", "set", "shut",
    "spread", "let", "bet", "burst", "kept",
}


def _count_phrase_hits(text_lower: str, phrases: set[str]) -> tuple[int, dict]:
    hits = {}
    for phrase in phrases:
        c = text_lower.count(phrase)
        if c:
            hits[phrase] = c
    return sum(hits.values()), hits


def _is_passive(sentence: str) -> bool:
    tokens_lower = [w.lower() for w in re.findall(r"[A-Za-z']+", sentence)]
    for i, tok in enumerate(tokens_lower):
        if tok in _BE_FORMS:
            for j in range(i + 1, min(i + 4, len(tokens_lower))):
                candidate = tokens_lower[j]
                if candidate in _IRREGULAR_PAST_PARTICIPLES or (
                    candidate.endswith("ed") and len(candidate) > 3
                ):
                    return True
    return False


def analyze_style(text: str) -> dict:
    total_words = max(1, word_count(text))
    text_lower = text.lower()

    trans_count, trans_hits = _count_phrase_hits(text_lower, TRANSITION_WORDS)
    filler_count, filler_hits = _count_phrase_hits(text_lower, FILLER_PHRASES)

    transition_density = 100 * trans_count / total_words
    filler_density = 100 * filler_count / total_words

    sents = split_sentences(text)
    passive_sents = 0
    passive_examples = []
    for s in sents:
        if _is_passive(s):
            passive_sents += 1
            if len(passive_examples) < 8:
                passive_examples.append(s.strip())

    passive_pct = 100 * passive_sents / max(1, len(sents))

    return {
        "transition_density_pct": round(transition_density, 2),
        "transition_word_hits": sorted(trans_hits.items(), key=lambda x: -x[1]),
        "filler_density_pct": round(filler_density, 2),
        "filler_phrase_hits": sorted(filler_hits.items(), key=lambda x: -x[1]),
        "passive_voice_pct": round(passive_pct, 1),
        "passive_sentence_examples": passive_examples,
        "total_sentences": len(sents),
    }

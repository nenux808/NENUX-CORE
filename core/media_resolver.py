"""Deterministic media-result ranking for browser playback."""

import re
from difflib import SequenceMatcher
from urllib.parse import urlparse


STOPWORDS = {
    "play", "watch", "listen", "to", "by", "on", "youtube", "official",
    "music", "video", "the", "a", "an", "can", "you", "please",
}


def _collapse_spelled_tokens(text: str) -> str:
    """Turn sequences such as S-H-A-N into SHAN before matching."""
    def repl(match):
        return match.group(0).replace("-", "").replace(" ", "")

    return re.sub(
        r"\b(?:[a-zA-Z][ -]){2,}[a-zA-Z]\b",
        repl,
        text,
    )


def _normalize(text: str) -> str:
    text = _collapse_spelled_tokens(str(text))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _tokens(text: str) -> list[str]:
    return [
        token
        for token in _normalize(text).split()
        if token and token not in STOPWORDS
    ]


def _token_similarity(a: str, b: str) -> float:
    if a == b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def _is_youtube_watch_url(url: str) -> bool:
    try:
        parsed = urlparse(str(url))
    except Exception:
        return False

    host = parsed.netloc.lower()
    return (
        parsed.scheme in {"http", "https"}
        and host in {"youtube.com", "www.youtube.com", "m.youtube.com"}
        and parsed.path == "/watch"
        and "v=" in parsed.query
    )


def score_media_result(request: str, result: dict) -> float:
    """Score a search result against the user's requested media."""
    url = str(result.get("url", ""))
    if not _is_youtube_watch_url(url):
        return -1.0

    query_tokens = _tokens(request)
    title = str(result.get("title", ""))
    title_tokens = _tokens(title)

    if not query_tokens or not title_tokens:
        return 0.0

    token_scores = []
    for query_token in query_tokens:
        best = max(
            (_token_similarity(query_token, title_token) for title_token in title_tokens),
            default=0.0,
        )
        token_scores.append(best)

    coverage = sum(token_scores) / len(token_scores)
    strong_matches = sum(score >= 0.72 for score in token_scores) / len(token_scores)

    normalized_title = _normalize(title)
    bonus = 0.0
    if "official" in normalized_title:
        bonus += 0.04
    if "music video" in normalized_title:
        bonus += 0.03

    return round((0.7 * coverage) + (0.3 * strong_matches) + bonus, 4)


def select_best_youtube_result(request: str, search_result: dict) -> dict | None:
    """Return the highest-scoring YouTube watch result."""
    results = search_result.get("results", []) if isinstance(search_result, dict) else []

    ranked = []
    for result in results:
        if not isinstance(result, dict):
            continue
        score = score_media_result(request, result)
        if score >= 0:
            ranked.append((score, result))

    if not ranked:
        return None

    ranked.sort(key=lambda item: item[0], reverse=True)
    score, result = ranked[0]

    selected = dict(result)
    selected["match_score"] = score
    return selected

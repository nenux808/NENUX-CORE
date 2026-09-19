"""Read-only live web search for NENUX Core."""

from ddgs import DDGS


def web_search(query: str, max_results: int = 5) -> dict:
    """Search the public web and return compact source-backed results."""
    query = query.strip()
    if not query:
        return {"success": False, "error": "Search query cannot be empty."}

    max_results = max(1, min(int(max_results), 8))

    results = DDGS(timeout=10).text(
        query,
        max_results=max_results,
        backend="auto",
    )

    sources = []
    for item in results or []:
        sources.append(
            {
                "title": item.get("title", ""),
                "url": item.get("href", item.get("url", "")),
                "snippet": item.get("body", item.get("snippet", "")),
            }
        )

    return {
        "success": True,
        "query": query,
        "results": sources,
    }

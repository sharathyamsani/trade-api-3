"""
Data collection layer.
Tries Serper API first; falls back to DuckDuckGo HTML scraping.
"""
import asyncio
import logging
import urllib.parse

import httpx

from config import settings

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

SEARCH_QUERIES = [
    "{sector} sector India trade opportunities 2024 2025",
    "{sector} India export import market growth",
    "{sector} India government policy FDI investment",
    "India {sector} industry challenges risks outlook",
]


async def fetch_serper(query: str, client: httpx.AsyncClient) -> list[dict]:
    """Use Serper.dev API (paid, reliable)."""
    try:
        resp = await client.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": settings.SERPER_API_KEY, "Content-Type": "application/json"},
            json={"q": query, "num": 5, "gl": "in", "hl": "en"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        results = []
        for item in data.get("organic", []):
            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "link": item.get("link", ""),
            })
        return results
    except Exception as exc:
        logger.warning("Serper fetch failed: %s", exc)
        return []


async def fetch_duckduckgo(query: str, client: httpx.AsyncClient) -> list[dict]:
    """Fallback: DuckDuckGo HTML scraping."""
    try:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        resp = await client.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
        resp.raise_for_status()
        html = resp.text

        results = []
        # Simple tag-based extraction (avoids heavy deps like BeautifulSoup)
        import re
        # Extract result snippets
        snippets = re.findall(
            r'class="result__snippet"[^>]*>(.*?)</a>',
            html, re.DOTALL
        )
        titles = re.findall(
            r'class="result__a"[^>]*>(.*?)</a>',
            html, re.DOTALL
        )
        links = re.findall(
            r'class="result__url"[^>]*>(.*?)</a>',
            html, re.DOTALL
        )

        def strip_tags(text: str) -> str:
            return re.sub(r"<[^>]+>", "", text).strip()

        for i in range(min(5, len(snippets))):
            results.append({
                "title": strip_tags(titles[i]) if i < len(titles) else "",
                "snippet": strip_tags(snippets[i]),
                "link": strip_tags(links[i]) if i < len(links) else "",
            })
        return results
    except Exception as exc:
        logger.warning("DuckDuckGo fetch failed: %s", exc)
        return []


async def collect_market_data(sector: str) -> tuple[list[dict], list[str]]:
    """
    Run multiple search queries and aggregate results.
    Returns (results_list, sources_list).
    """
    queries = [q.format(sector=sector) for q in SEARCH_QUERIES]
    all_results: list[dict] = []
    sources: list[str] = []

    use_serper = bool(settings.SERPER_API_KEY)

    async with httpx.AsyncClient() as client:
        tasks = [
            fetch_serper(q, client) if use_serper else fetch_duckduckgo(q, client)
            for q in queries
        ]
        batches = await asyncio.gather(*tasks, return_exceptions=True)

    for batch in batches:
        if isinstance(batch, list):
            for item in batch:
                all_results.append(item)
                if item.get("link"):
                    sources.append(item["link"])

    # Deduplicate by title
    seen: set[str] = set()
    unique: list[dict] = []
    for r in all_results:
        key = r.get("title", "")[:60]
        if key not in seen:
            seen.add(key)
            unique.append(r)

    logger.info("Collected %d unique results for sector=%s", len(unique), sector)
    return unique[:20], list(set(sources))[:10]


def format_results_for_prompt(results: list[dict]) -> str:
    """Convert search results into a readable block for the LLM prompt."""
    lines: list[str] = []
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r.get('title', 'No title')}")
        if r.get("snippet"):
            lines.append(f"    {r['snippet']}")
        if r.get("link"):
            lines.append(f"    Source: {r['link']}")
        lines.append("")
    return "\n".join(lines)

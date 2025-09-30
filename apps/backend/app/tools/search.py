from __future__ import annotations
import asyncio
from typing import Any, Dict, List, Optional
import httpx
from urllib.parse import urlparse

from ..config import settings

DEFAULT_TIMEOUT = httpx.Timeout(10.0, connect=10.0)

def _norm_source_from_url(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        host = host.split(":")[0]
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return "unknown"

async def _tavily_search(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    if not settings.TAVILY_API_KEY:
        raise RuntimeError("Tavily API key not configured")
    payload = {
        "api_key": settings.TAVILY_API_KEY,
        "query": query,
        "max_results": max_results,
        "search_depth": "basic",
        # You can add domain filters later if desired
    }
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        r = await client.post("https://api.tavily.com/search", json=payload)
        r.raise_for_status()
        data = r.json()
    items = []
    for row in data.get("results", []):
        items.append({
            "title": row.get("title") or "",
            "url": row.get("url") or "",
            "snippet": row.get("content") or row.get("snippet") or "",
            "source": _norm_source_from_url(row.get("url") or ""),
        })
    return items

async def _serpapi_search(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    if not settings.SERPAPI_API_KEY:
        raise RuntimeError("SerpApi API key not configured")
    params = {
        "engine": "google",
        "q": query,
        "num": max_results,
        "api_key": settings.SERPAPI_API_KEY,
    }
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        r = await client.get("https://serpapi.com/search.json", params=params)
        r.raise_for_status()
        data = r.json()
    items = []
    for row in data.get("organic_results", []):
        items.append({
            "title": row.get("title") or "",
            "url": row.get("link") or "",
            "snippet": row.get("snippet") or "",
            "source": _norm_source_from_url(row.get("link") or ""),
        })
    return items

async def search_web(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Provider-agnostic search. Uses Tavily if configured, else SerpApi.
    Returns: [{title, url, snippet, source}]
    """
    if settings.TAVILY_API_KEY:
        return await _tavily_search(query, max_results=max_results)
    if settings.SERPAPI_API_KEY:
        return await _serpapi_search(query, max_results=max_results)
    raise RuntimeError("No search provider configured. Set TAVILY_API_KEY or SERPAPI_API_KEY.")

def build_video_query(topic: str, extra_terms: Optional[List[str]] = None, site_filters: Optional[List[str]] = None) -> str:
    """
    Build a video-intent query like:
      "<topic> (tutorial OR course OR lecture OR playlist) (site:... OR site:...)"
    """
    terms = extra_terms or ["tutorial", "course", "lecture", "playlist"]
    q = f'{topic} ("' + '" OR "'.join(terms) + '")'
    if site_filters:
        sites = " OR ".join([f"site:{s}" for s in site_filters])
        q += f" ({sites})"
    return q

async def search_videos(topic: str, max_results: int = 10, site_filters: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    q = build_video_query(topic, site_filters=site_filters)
    return await search_web(q, max_results=max_results)

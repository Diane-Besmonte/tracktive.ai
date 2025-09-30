from __future__ import annotations
import asyncio
from typing import Iterable, List, Tuple
from urllib.parse import urlparse, urlencode

import httpx

# Treat these as definitely dead
_DEAD_STATUS = {404, 410, 451}
# Some sites block HEAD or anon; we still allow these (likely gated but alive)
_TOLERATE_STATUS = {401, 402, 403, 405}

_CLIENT_LIMITS = httpx.Limits(max_keepalive_connections=8, max_connections=20)
_TIMEOUT = httpx.Timeout(5.0, connect=5.0)  # keep it snappy

def _is_youtube(netloc: str) -> bool:
    n = netloc.lower()
    return "youtube.com" in n or "youtu.be" in n

def _is_vimeo(netloc: str) -> bool:
    return "vimeo.com" in netloc.lower()

async def _head_or_get(client: httpx.AsyncClient, url: str) -> httpx.Response:
    try:
        resp = await client.head(url, follow_redirects=True)
        if resp.status_code in (405, 501):  # method not allowed, try GET
            resp = await client.get(url, headers={"Range": "bytes=0-1024"}, follow_redirects=True)
        return resp
    except Exception:
        # network error; pretend it's dead
        return httpx.Response(status_code=599, request=httpx.Request("GET", url))

async def _check_oembed(client: httpx.AsyncClient, url: str) -> Tuple[bool, int]:
    """Fast availability check via oEmbed for YouTube/Vimeo (no API key)."""
    try:
        if _is_youtube(urlparse(url).netloc):
            q = urlencode({"url": url, "format": "json"})
            r = await client.get(f"https://www.youtube.com/oembed?{q}", timeout=_TIMEOUT)
            return (r.status_code == 200, r.status_code)
        if _is_vimeo(urlparse(url).netloc):
            q = urlencode({"url": url})
            r = await client.get(f"https://vimeo.com/api/oembed.json?{q}", timeout=_TIMEOUT)
            return (r.status_code == 200, r.status_code)
    except Exception:
        return (False, 599)
    return (None, 0)  # not applicable

async def check_url_alive(url: str, is_video: bool = False) -> Tuple[bool, int]:
    """
    Returns (ok, status_code).
    ok=True when the resource looks reachable (2xx/3xx), or tolerable 401/403/405 (gated),
    and not in the dead list (404/410/451/5xx).
    """
    parsed = urlparse(url)
    async with httpx.AsyncClient(limits=_CLIENT_LIMITS, timeout=_TIMEOUT, follow_redirects=True) as client:
        # Prefer oEmbed for known video hosts
        if is_video:
            ok, code = await _check_oembed(client, url)
            if ok is True:
                return True, 200
            if ok is False:
                # oEmbed says it's gone
                return False, code or 404
        # Fallback: HEAD/GET
        resp = await _head_or_get(client, url)
        code = resp.status_code
        if code in _DEAD_STATUS:
            return False, code
        if 200 <= code < 400:
            return True, code
        if code in _TOLERATE_STATUS:
            return True, code
        # treat other 4xx/5xx as dead
        return False, code

# --------- Adapters for your Pydantic items ---------
from ..schemas import ResourceItem, VideoItem

async def filter_valid_resources(items: Iterable[ResourceItem]) -> List[ResourceItem]:
    sem = asyncio.Semaphore(16)
    async def _one(it: ResourceItem):
        async with sem:
            ok, _ = await check_url_alive(it.url, is_video=False)
            return it if ok else None
    results = await asyncio.gather(*[_one(it) for it in items])
    return [r for r in results if r]

async def filter_valid_videos(items: Iterable[VideoItem]) -> List[VideoItem]:
    sem = asyncio.Semaphore(16)
    async def _one(it: VideoItem):
        async with sem:
            ok, _ = await check_url_alive(it.url, is_video=True)
            return it if ok else None
    results = await asyncio.gather(*[_one(it) for it in items])
    return [r for r in results if r]

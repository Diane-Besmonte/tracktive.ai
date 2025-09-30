from __future__ import annotations
import json
import re
from typing import Any, Dict, Optional
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from ..config import settings
from .search import DEFAULT_TIMEOUT

UA = "Mozilla/5.0 (compatible; MultiAgentMVP/0.1; +https://example.local)"

def _compact_host(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower().split(":")[0]
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return "unknown"

def _iso8601_to_compact(s: str) -> Optional[str]:
    """
    Convert ISO 8601 durations like PT1H05M30S → "1h05m" or "12m" or "45s".
    """
    if not s or not s.startswith("P"):
        return None
    # simple regex parse
    m = re.match(r"P(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)", s)
    if not m:
        return None
    h, mins, sec = m.groups()
    parts = []
    if h: parts.append(f"{int(h)}h")
    if mins: parts.append(f"{int(mins):02d}m" if h else f"{int(mins)}m")
    if sec and not mins and not h: parts.append(f"{int(sec)}s")
    return "".join(parts) or None

async def fetch_video_metadata(url: str) -> Dict[str, Any]:
    """
    Fetch a page and extract best-effort video metadata:
      { title, source, duration? }
    """
    headers = {"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"}
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, headers=headers, follow_redirects=True) as client:
        r = await client.get(url)
        r.raise_for_status()
        html = r.text

    soup = BeautifulSoup(html, "html.parser")

    # Title preference: og:title > <title>
    title = None
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = og_title["content"].strip()
    if not title and soup.title and soup.title.string:
        title = soup.title.string.strip()

    # Source: og:site_name > hostname
    source = None
    og_site = soup.find("meta", property="og:site_name")
    if og_site and og_site.get("content"):
        source = og_site["content"].strip()
    if not source:
        source = _compact_host(url)

    # Duration: try JSON-LD VideoObject, then og:video:duration or itemprop
    duration = None
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "{}")
            # could be a list or single object
            candidates = data if isinstance(data, list) else [data]
            for obj in candidates:
                t = obj.get("@type") or obj.get("@type".lower())
                if (isinstance(t, str) and t.lower() == "videoobject") or (isinstance(t, list) and "VideoObject" in t):
                    iso = obj.get("duration")
                    if iso:
                        duration = _iso8601_to_compact(iso)
                        break
            if duration:
                break
        except Exception:
            continue

    if not duration:
        meta_dur = soup.find("meta", property="og:video:duration") or soup.find("meta", itemprop="duration")
        if meta_dur and meta_dur.get("content"):
            # may be seconds integer or ISO8601
            val = meta_dur["content"].strip()
            if val.isdigit():
                seconds = int(val)
                if seconds >= 3600:
                    duration = f"{seconds//3600}h{(seconds%3600)//60:02d}m"
                elif seconds >= 60:
                    duration = f"{seconds//60}m"
                else:
                    duration = f"{seconds}s"
            else:
                duration = _iso8601_to_compact(val)

    return {
        "title": title or "",
        "source": source or _compact_host(url),
        "duration": duration,  # may be None
    }

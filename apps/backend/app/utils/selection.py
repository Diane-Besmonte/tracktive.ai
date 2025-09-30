from __future__ import annotations
from typing import Callable, Dict, Iterable, List, Tuple
from urllib.parse import urlparse

def normalize_title(t: str) -> str:
    return " ".join((t or "").strip().lower().split())

def normalize_url(u: str) -> str:
    # strip fragments, normalize trailing slash lightly
    p = urlparse(u)
    path = p.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    return f"{p.scheme}://{p.netloc.lower()}{path}"

def dedupe_by_title_url(items: Iterable[Dict], title_key="title", url_key="url") -> List[Dict]:
    seen_t: set[str] = set()
    seen_u: set[str] = set()
    out: List[Dict] = []
    for it in items:
        t = normalize_title(it.get(title_key, ""))
        u = normalize_url(it.get(url_key, ""))
        if t in seen_t or u in seen_u:
            continue
        seen_t.add(t)
        seen_u.add(u)
        out.append(it)
    return out

def cap_per_domain(items: Iterable[Dict], max_per_domain: int = 3, url_key="url") -> List[Dict]:
    counts: dict[str, int] = {}
    out: List[Dict] = []
    for it in items:
        host = urlparse(it.get(url_key, "")).netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        if counts.get(host, 0) >= max_per_domain:
            continue
        counts[host] = counts.get(host, 0) + 1
        out.append(it)
    return out

from __future__ import annotations
from typing import Iterable, List, Set

from ..schemas import ResourceItem, VideoItem
from ..tools.search import search_web, search_videos
from ..utils.selection import dedupe_by_title_url, cap_per_domain
from ..utils.linkcheck import filter_valid_resources, filter_valid_videos

MIN_RESOURCES = 2     # ensure at least this many stay after validation
MIN_VIDEOS = 1        # ensure at least this many stay after validation
MAX_PER_DOMAIN = 3    # keep variety

async def backfill_resources(
    brief: str,
    goals: List[str],
    existing: Iterable[ResourceItem],
    need_at_least: int = MIN_RESOURCES,
) -> List[ResourceItem]:
    items = list(existing)
    if len(items) >= need_at_least:
        return items

    existing_urls: Set[str] = {r.url for r in items}
    # Try brief + top goals
    queries = [brief] + [f"{g} tutorial" for g in goals[:3]]

    candidates = []
    for q in queries:
        try:
            batch = await search_web(q, max_results=6)
            for h in batch:
                url = h.get("url") or ""
                title = (h.get("title") or "").strip()
                if not url or url in existing_urls or not title:
                    continue
                candidates.append({"title": title[:120], "url": url, "why": "Useful reference for your goal."})
        except Exception:
            continue
        if len(candidates) > 12:
            break

    candidates = dedupe_by_title_url(candidates)
    candidates = cap_per_domain(candidates, max_per_domain=MAX_PER_DOMAIN)

    # Coerce to model + validate live links
    cand_items: List[ResourceItem] = []
    for c in candidates:
        try:
            cand_items.append(ResourceItem(**c))
        except Exception:
            continue
    validated = await filter_valid_resources(cand_items)

    for it in validated:
        if len(items) >= need_at_least:
            break
        if it.url in existing_urls:
            continue
        items.append(it)
        existing_urls.add(it.url)

    return items

async def backfill_videos(
    brief: str,
    goals: List[str],
    existing: Iterable[VideoItem],
    need_at_least: int = MIN_VIDEOS,
) -> List[VideoItem]:
    items = list(existing)
    if len(items) >= need_at_least:
        return items

    existing_urls: Set[str] = {v.url for v in items}
    queries = [brief] + [f"{g} short video" for g in goals[:3]]

    candidates = []
    for q in queries:
        try:
            batch = await search_videos(q, max_results=8)
            for v in batch:
                url = v.get("url") or ""
                title = (v.get("title") or "").strip()
                if not url or url in existing_urls or not title:
                    continue
                candidates.append({
                    "title": title[:120],
                    "url": url,
                    "source": (v.get("source") or "")[:60],
                    "duration": v.get("duration"),
                    "why": "Concise demo for today’s topic."
                })
        except Exception:
            continue
        if len(candidates) > 16:
            break

    candidates = dedupe_by_title_url(candidates)
    candidates = cap_per_domain(candidates, max_per_domain=MAX_PER_DOMAIN)

    cand_items: List[VideoItem] = []
    for c in candidates:
        try:
            cand_items.append(VideoItem(**c))
        except Exception:
            c.pop("duration", None)  # tolerate missing/odd duration
            try:
                cand_items.append(VideoItem(**c))
            except Exception:
                continue

    validated = await filter_valid_videos(cand_items)

    for it in validated:
        if len(items) >= need_at_least:
            break
        if it.url in existing_urls:
            continue
        items.append(it)
        existing_urls.add(it.url)

    return items

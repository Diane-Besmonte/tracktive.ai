# from __future__ import annotations
# from typing import List, Dict
# from math import ceil
# from .schemas import (
#     GenerateScheduleIn, ResourceItem, VideoItem, ExerciseItem,
#     DayPlan, ScheduleOutput, RoadmapOutput
# )

# def _chunk(items: List, n: int) -> List[List]:
#     """Split items into n roughly equal chunks (preserve order)."""
#     if n <= 0:
#         return [items]
#     size = max(1, ceil(len(items) / n))
#     out = []
#     for i in range(0, len(items), size):
#         out.append(items[i:i+size])
#     # pad to n with empty lists if needed
#     while len(out) < n:
#         out.append([])
#     return out[:n]

# def compose_schedule(inp: GenerateScheduleIn, base: RoadmapOutput) -> ScheduleOutput:
#     """Create day_1..day_N with small bundles of resources/videos/exercises."""
#     days = inp.duration_days
#     # chunk each list into days
#     r_chunks = _chunk(list(base.resources), days)
#     v_chunks = _chunk(list(base.videos), days)
#     e_chunks = _chunk(list(base.exercises), days)

#     # derive topics by cycling goals, fallback to brief
#     topics = []
#     if inp.goals:
#         for i in range(days):
#             topics.append(inp.goals[i % len(inp.goals)])
#     else:
#         topics = [inp.brief] * days

#     data: Dict[str, DayPlan] = {}
#     for i in range(days):
#         topic = topics[i]
#         resources = r_chunks[i][:3]
#         videos = v_chunks[i][:3]
#         exercises = e_chunks[i][:3]

#         # simple description template (keep under 600 chars)
#         desc = (
#             f"Focus: {topic}. Spend ~{inp.daily_minutes} minutes at {inp.preferred_time} "
#             f"({inp.timezone}). Start with 1–2 links, then 1 video, then finish an exercise. "
#             f"Keep notes; aim for small wins today."
#         )
#         data[f"day_{i+1}"] = DayPlan(
#             topic=topic,
#             description=desc[:600],
#             resources=resources,
#             videos=videos,
#             exercises=exercises,
#         )
#     return ScheduleOutput(overview=base.overview, data=data)


# apps/backend/app/scheduler.py
from __future__ import annotations
import re
from typing import List, Dict, Tuple

from .schemas import (
    GenerateScheduleIn, DayPlan, ScheduleOutput, RoadmapOutput,
    ResourceItem, VideoItem, ExerciseItem
)

# per-day caps (should align with routes' min/max)
RES_CAP = 2
VID_CAP = 1
EX_CAP = 1

_STOP = {"the","and","for","with","your","from","into","over","then","that","this","you","our","in","of","to","a","an","on","at","by","as","up"}

def _tokens(s: str) -> set[str]:
    parts = re.findall(r"[a-zA-Z0-9]+", (s or "").lower())
    return {p for p in parts if len(p) >= 3 and p not in _STOP}

def _score(theme: str, title: str, extra: str = "") -> int:
    t = _tokens(theme)
    c = _tokens(title) | _tokens(extra)
    return len(t & c)

def _pick_best_items(theme: str, pool: List, k: int, kind: str) -> Tuple[List, List]:
    """
    Greedy pick top-k by overlap score against theme.
    Returns (picked, remaining_pool).
    """
    if k <= 0 or not pool:
        return [], pool

    scored = []
    for idx, it in enumerate(pool):
        if kind == "resource":
            s = _score(theme, it.title, it.why)
        elif kind == "video":
            extra = f"{getattr(it, 'source', '')} {it.why}"
            s = _score(theme, it.title, extra)
        else:
            # exercise
            steps_text = " ".join(getattr(it, "steps", []))
            s = _score(theme, it.title, steps_text)
        scored.append((s, idx))

    scored.sort(key=lambda x: (x[0], -x[1]), reverse=True)
    picked_idxs = [idx for (s, idx) in scored[:k] if s > 0]

    # if not enough positive matches, pad from the earliest remaining
    if len(picked_idxs) < k:
        remaining_idxs = [i for i in range(len(pool)) if i not in picked_idxs]
        pad_needed = k - len(picked_idxs)
        picked_idxs += remaining_idxs[:pad_needed]

    picked = [pool[i] for i in picked_idxs if i < len(pool)]
    remaining = [pool[i] for i in range(len(pool)) if i not in picked_idxs]
    return picked, remaining

def compose_schedule(
    inp: GenerateScheduleIn,
    base: RoadmapOutput,
    day_topics: List[str] | None = None,
) -> ScheduleOutput:
    """
    Build day_1..day_N schedule with better thematic alignment:
      1) Use provided day_topics if available; else derive from goals/brief.
      2) For each day, pick items from global pools that best match the day's theme.
    """
    days = inp.duration_days

    # Decide day titles
    topics: List[str] = []
    if day_topics and len(day_topics) >= days:
        topics = day_topics[:days]
    elif inp.goals:
        topics = [inp.goals[i % len(inp.goals)] for i in range(days)]
    else:
        topics = [inp.brief] * days

    # mutable pools (consumed as we assign)
    res_pool = list(base.resources)
    vid_pool = list(base.videos)
    ex_pool  = list(base.exercises)

    data: Dict[str, DayPlan] = {}

    for i in range(days):
        theme = topics[i]

        # pick best items for this theme
        r_take, res_pool = _pick_best_items(theme, res_pool, RES_CAP, "resource")
        v_take, vid_pool = _pick_best_items(theme, vid_pool, VID_CAP, "video")
        e_take, ex_pool  = _pick_best_items(theme, ex_pool,  EX_CAP, "exercise")

        desc = (
            f"Focus: {theme}. Spend ~{inp.daily_minutes} minutes at {inp.preferred_time} "
            f"({inp.timezone}). Start with short reads, then one video, then finish an exercise. "
            f"Keep notes; aim for small wins today."
        )
        data[f"day_{i+1}"] = DayPlan(
            topic=theme[:120],
            description=desc[:600],
            resources=r_take[:3],
            videos=v_take[:3],
            exercises=e_take[:3],
        )

    return ScheduleOutput(overview=base.overview, data=data)

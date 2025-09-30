# from __future__ import annotations
# from pydantic import BaseModel, Field, conint, constr
# from typing import List, Optional, Dict

# # Constrained URL string (Agents SDK dislikes JSON Schema "uri" format)
# UrlStr = constr(strip_whitespace=True, min_length=8, max_length=2048, pattern=r"^https?://")

# # ---------- Inputs ----------

# class GenerateScheduleIn(BaseModel):
#     brief: constr(strip_whitespace=True, min_length=10, max_length=500)
#     goals: List[constr(strip_whitespace=True, min_length=2)] = Field(default_factory=list)
#     daily_minutes: conint(ge=10, le=180) = 30
#     duration_days: conint(ge=1, le=365) = 5
#     preferred_time: constr(pattern=r"^\d{2}:\d{2}$") = "18:00"  # 24h "HH:MM"
#     timezone: str = "Asia/Manila"

# # ---------- Atomic items (reuse for days) ----------

# class ResourceItem(BaseModel):
#     title: constr(strip_whitespace=True, min_length=3, max_length=120)
#     url: UrlStr
#     why: constr(strip_whitespace=True, min_length=5, max_length=240)

# class VideoItem(BaseModel):
#     title: constr(strip_whitespace=True, min_length=3, max_length=120)
#     url: UrlStr
#     source: constr(strip_whitespace=True, min_length=2, max_length=60)
#     why: constr(strip_whitespace=True, min_length=5, max_length=240)
#     duration: Optional[constr(strip_whitespace=True, max_length=40)] = None

# class ExerciseItem(BaseModel):
#     title: constr(strip_whitespace=True, min_length=3, max_length=120)
#     steps: List[constr(strip_whitespace=True, min_length=2, max_length=160)]
#     estimate_minutes: conint(ge=5, le=180)

# # ---------- Old preview (still used internally) ----------

# class RoadmapOutput(BaseModel):
#     overview: constr(strip_whitespace=True, min_length=10, max_length=600)
#     resources: List[ResourceItem] = Field(default_factory=list, max_items=12)
#     videos: List[VideoItem] = Field(default_factory=list, max_items=12)
#     exercises: List[ExerciseItem] = Field(default_factory=list, max_items=12)

# # ---------- Day-by-day plan ----------

# class DayPlan(BaseModel):
#     topic: constr(strip_whitespace=True, min_length=3, max_length=120)
#     description: constr(strip_whitespace=True, min_length=10, max_length=600)
#     resources: List[ResourceItem] = Field(default_factory=list, max_items=3)
#     videos: List[VideoItem] = Field(default_factory=list, max_items=3)
#     exercises: List[ExerciseItem] = Field(default_factory=list, max_items=3)

# class ScheduleOutput(BaseModel):
#     overview: constr(strip_whitespace=True, min_length=10, max_length=600)
#     # data.day_1, day_2, ...
#     data: Dict[constr(pattern=r"^day_\d+$"), DayPlan] = Field(default_factory=dict)


from __future__ import annotations
from pydantic import BaseModel, Field, conint, constr
from typing import List, Optional, Dict

# Constrained URL string (Agents SDK dislikes JSON Schema "uri" format)
UrlStr = constr(strip_whitespace=True, min_length=8, max_length=2048, pattern=r"^https?://")

# ---------- Inputs ----------

class GenerateScheduleIn(BaseModel):
    brief: constr(strip_whitespace=True, min_length=10, max_length=500)
    goals: List[constr(strip_whitespace=True, min_length=2)] = Field(default_factory=list)
    daily_minutes: conint(ge=10, le=180) = 30
    duration_days: conint(ge=1, le=365) = 5
    preferred_time: constr(pattern=r"^\d{2}:\d{2}$") = "18:00"  # 24h "HH:MM"
    timezone: str = "Asia/Manila"

# ---------- Atomic items (reuse for days) ----------

class ResourceItem(BaseModel):
    title: constr(strip_whitespace=True, min_length=3, max_length=120)
    url: UrlStr
    why: constr(strip_whitespace=True, min_length=5, max_length=240)

class VideoItem(BaseModel):
    title: constr(strip_whitespace=True, min_length=3, max_length=120)
    url: UrlStr
    source: constr(strip_whitespace=True, min_length=2, max_length=60)
    why: constr(strip_whitespace=True, min_length=5, max_length=240)
    duration: Optional[constr(strip_whitespace=True, max_length=40)] = None

class ExerciseItem(BaseModel):
    title: constr(strip_whitespace=True, min_length=3, max_length=120)
    steps: List[constr(strip_whitespace=True, min_length=2, max_length=160)]
    estimate_minutes: conint(ge=5, le=180)

# ---------- Preview list (manager output) ----------

class RoadmapOutput(BaseModel):
    overview: constr(strip_whitespace=True, min_length=10, max_length=600)
    # keep higher caps so we can stock per-day options
    resources: List[ResourceItem] = Field(default_factory=list, max_items=24)
    videos: List[VideoItem] = Field(default_factory=list, max_items=24)
    exercises: List[ExerciseItem] = Field(default_factory=list, max_items=24)

# ---------- Day-by-day plan ----------

class DayPlan(BaseModel):
    topic: constr(strip_whitespace=True, min_length=3, max_length=120)
    description: constr(strip_whitespace=True, min_length=10, max_length=600)
    resources: List[ResourceItem] = Field(default_factory=list, max_items=3)
    videos: List[VideoItem] = Field(default_factory=list, max_items=3)
    exercises: List[ExerciseItem] = Field(default_factory=list, max_items=3)

class ScheduleOutput(BaseModel):
    overview: constr(strip_whitespace=True, min_length=10, max_length=600)
    # data.day_1, day_2, ...
    data: Dict[constr(pattern=r"^day_\d+$"), DayPlan] = Field(default_factory=dict)

# ---------- Internal helper outputs for agents ----------

class DayThemesOut(BaseModel):
    topics: List[constr(strip_whitespace=True, min_length=3, max_length=120)] = Field(default_factory=list)

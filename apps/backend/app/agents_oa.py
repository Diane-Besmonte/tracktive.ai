# # apps/backend/app/agents_oa.py
# from __future__ import annotations
# import asyncio
# import json
# from typing import List

# from pydantic import BaseModel, Field, constr
# from agents import (
#     Agent,
#     Runner,
#     function_tool,
#     input_guardrail,
#     output_guardrail,
#     GuardrailFunctionOutput,
#     RunContextWrapper,
#     TResponseInputItem,
# )
# from langsmith.wrappers import OpenAIAgentsTracingProcessor
# from agents import set_trace_processors  # LangSmith tracer hook for Agents SDK

# from .schemas import GenerateScheduleIn, RoadmapOutput

# # ---- LangSmith tracing for the Agents SDK ----
# try:
#     set_trace_processors([OpenAIAgentsTracingProcessor()])
#     print("[LangSmith] OpenAI Agents tracing enabled for OpenAI Agents SDK")
# except Exception as e:
#     print(f"[LangSmith] Agents tracing NOT enabled: {e}")

# # ---------------- function tools ----------------
# @function_tool
# async def web_search(query: str, max_results: int = 6) -> str:
#     """Search the web and return JSON array of {title,url} items (short)."""
#     try:
#         from .tools.search import search_web
#         hits = await search_web(query, max_results=max_results)
#         out = [{"title": (h.get("title") or "")[:200], "url": h.get("url") or ""} for h in hits]
#         return json.dumps(out, ensure_ascii=False)
#     except Exception:
#         return json.dumps([], ensure_ascii=False)

# @function_tool
# async def video_search(topic: str, max_results: int = 8) -> str:
#     """Find videos across sites. Return JSON array of {title,url,source?,duration?}."""
#     try:
#         from .tools.search import search_videos
#         vids = await search_videos(topic, max_results=max_results)
#         out = [{
#             "title": (v.get("title") or "")[:200],
#             "url": v.get("url") or "",
#             "source": v.get("source") or "",
#             "duration": v.get("duration"),
#         } for v in vids]
#         return json.dumps(out, ensure_ascii=False)
#     except Exception:
#         return json.dumps([], ensure_ascii=False)

# @function_tool
# def pace_rules(daily_minutes: int, duration_days: int) -> str:
#     """Return compact pacing guidance for the agent to follow."""
#     guide = {
#         "per_day": {"reads": 1, "videos": 1, "exercise_minutes": min(20, max(10, daily_minutes - 10))},
#         "total_days": duration_days,
#         "avoid": ["long playlists", "heavy toolchains"],
#     }
#     return json.dumps(guide, ensure_ascii=False)

# # ---------------- Guardrail models ----------------
# class BriefCheckOutput(BaseModel):
#     allowed: bool
#     reason: constr(strip_whitespace=True, min_length=2, max_length=300) = "ok"

# class PlanCheckOutput(BaseModel):
#     ok: bool
#     reason: constr(strip_whitespace=True, min_length=2, max_length=300) = "ok"

# # Guardrail Agent used by the input guardrail (cheap check)
# brief_guardrail_agent = Agent(
#     name="Brief guardrail",
#     instructions=(
#         "You check if a brief is safe, in-scope for a learning planner, and feasible for the stated pace. "
#         "Flag as NOT allowed if it requests illegal/unsafe content, explicit content, "
#         "or is totally unrelated to learning; or if pace is unrealistic (e.g., advanced topic in 5 min/day)."
#     ),
#     output_type=BriefCheckOutput,
# )

# # ---------------- Input guardrail ----------------
# @input_guardrail
# async def brief_guardrail(
#     ctx: RunContextWrapper[None],
#     agent: Agent,
#     input: str | List[TResponseInputItem],
# ) -> GuardrailFunctionOutput:
#     """
#     Runs BEFORE the Manager agent. If tripwire is True, the SDK raises
#     InputGuardrailTripwireTriggered and halts the run.
#     """
#     # Run the brief checker using the same context for trace continuity
#     result = await Runner.run(brief_guardrail_agent, input, context=ctx.context, max_turns=1)
#     output: BriefCheckOutput = result.final_output  # type: ignore
#     return GuardrailFunctionOutput(
#         output_info=output,
#         tripwire_triggered=not output.allowed,
#     )

# # ---------------- Output guardrail ----------------
# @output_guardrail
# async def roadmap_guardrail(
#     ctx: RunContextWrapper[None],
#     agent: Agent,
#     output: RoadmapOutput,
# ) -> GuardrailFunctionOutput:
#     """
#     Runs AFTER the Manager agent returns its RoadmapOutput, right before the result is finalized.
#     Use this to enforce extra business rules beyond Pydantic validation.
#     """
#     ok = True
#     reasons: List[str] = []

#     # Soft checks on counts (Pydantic already caps these, this is a safety double-check)
#     if len(output.resources) == 0 and len(output.videos) == 0:
#         ok = False
#         reasons.append("No study materials found (resources/videos empty).")

#     # Keep rationales short-ish
#     for r in output.resources:
#         if len(r.why) > 200:
#             ok = False
#             reasons.append("Resource rationale too long.")
#             break
#     for v in output.videos:
#         if len(v.why) > 200:
#             ok = False
#             reasons.append("Video rationale too long.")
#             break

#     # Ensure at least one exercise
#     if len(output.exercises) == 0:
#         ok = False
#         reasons.append("No exercises returned.")

#     return GuardrailFunctionOutput(
#         output_info=PlanCheckOutput(ok=ok, reason="; ".join(reasons) if reasons else "ok"),
#         tripwire_triggered=not ok,
#     )

# # ---------------- Manager Agent ----------------
# manager = Agent(
#     name="Manager",
#     instructions=(
#         "You produce a beginner-friendly learning preview: an 'overview' plus short lists "
#         "of 'resources', 'videos', and 'exercises'. Use tools sparingly (web_search, video_search), "
#         "respect pace_rules, keep 'why' rationales <=180 chars, and avoid long courses/playlists.\n\n"
#         "OUTPUT MUST MATCH the RoadmapOutput schema exactly."
#     ),
#     tools=[web_search, video_search, pace_rules],
#     output_type=RoadmapOutput,
#     input_guardrails=[brief_guardrail],
#     output_guardrails=[roadmap_guardrail],
# )

# # ---------------- Entry point used by routes ----------------
# async def run_manager(inp: GenerateScheduleIn) -> RoadmapOutput:
#     msg = (
#         "Brief: {brief}\n"
#         "Goals: {goals}\n"
#         "Daily minutes: {mins}\n"
#         "Timezone: {tz}\n"
#         "Constraints: Prefer 1 short read + 1 short video + 1 practical exercise per day; "
#         "beginner pacing; avoid frameworks/backends unless requested."
#     ).format(
#         brief=inp.brief,
#         goals=", ".join(inp.goals),
#         mins=inp.daily_minutes,
#         tz=inp.timezone,
#     )

#     # Runner.run supports max_turns; use asyncio timeout for a wall clock cap.
#     try:
#         coro = Runner.run(manager, msg, max_turns=10)
#         result = await asyncio.wait_for(coro, timeout=90)
#     except asyncio.TimeoutError:
#         raise RuntimeError("Agent run timed out after 90s")
#     return result.final_output  # type: ignore


# apps/backend/app/agents_oa.py
from __future__ import annotations

import asyncio
import json
from typing import List

from pydantic import BaseModel, constr
from agents import (
    Agent,
    Runner,
    function_tool,
    input_guardrail,
    output_guardrail,
    GuardrailFunctionOutput,
    RunContextWrapper,
    TResponseInputItem,
)
from agents import set_trace_processors  # LangSmith tracer hook for Agents SDK
from langsmith.wrappers import OpenAIAgentsTracingProcessor

from .schemas import GenerateScheduleIn, RoadmapOutput, ExerciseItem, DayThemesOut

# ---- LangSmith tracing for the OpenAI Agents SDK ----
try:
    set_trace_processors([OpenAIAgentsTracingProcessor()])
    print("[LangSmith] OpenAI Agents tracing enabled for OpenAI Agents SDK")
except Exception as e:
    print(f"[LangSmith] Agents tracing NOT enabled: {e}")


# ---------------- function tools ----------------
@function_tool
async def web_search(query: str, max_results: int = 8) -> str:
    """
    Search the web and return JSON array of {title,url} items (short).
    Keep payload tiny; the agent will write 'why'.
    """
    try:
        from .tools.search import search_web
        hits = await search_web(query, max_results=max_results)
        out = [{"title": (h.get("title") or "")[:200], "url": h.get("url") or ""} for h in hits]
        return json.dumps(out, ensure_ascii=False)
    except Exception:
        return json.dumps([], ensure_ascii=False)


@function_tool
async def video_search(topic: str, max_results: int = 10) -> str:
    """
    Find videos across sites. Return JSON array of {title,url,source?,duration?}.
    """
    try:
        from .tools.search import search_videos
        vids = await search_videos(topic, max_results=max_results)
        out = [
            {
                "title": (v.get("title") or "")[:200],
                "url": v.get("url") or "",
                "source": v.get("source") or "",
                "duration": v.get("duration"),
            }
            for v in vids
        ]
        return json.dumps(out, ensure_ascii=False)
    except Exception:
        return json.dumps([], ensure_ascii=False)


@function_tool
def pace_rules(daily_minutes: int, duration_days: int) -> str:
    """
    Return compact pacing guidance for the agent to follow.
    2 reads + 1 video + 1 exercise per day.
    """
    guide = {
        "per_day": {"reads": 2, "videos": 1, "exercise_minutes": max(10, min(30, daily_minutes - 18))},
        "total_days": duration_days,
        "avoid": ["long playlists", "heavy toolchains"],
    }
    return json.dumps(guide, ensure_ascii=False)


# ---------------- Guardrail models ----------------
class BriefCheckOutput(BaseModel):
    allowed: bool
    reason: constr(strip_whitespace=True, min_length=2, max_length=300) = "ok"


class PlanCheckOutput(BaseModel):
    ok: bool
    reason: constr(strip_whitespace=True, min_length=2, max_length=300) = "ok"


# Guardrail Agent used by the input guardrail (cheap check)
brief_guardrail_agent = Agent(
    name="Brief guardrail",
    instructions=(
        "You check if a brief is safe, in-scope for a learning planner, and feasible for the stated pace. "
        "Flag as NOT allowed if it requests illegal/unsafe content, explicit content, "
        "or is totally unrelated to learning; or if pace is unrealistic (e.g., advanced topic in 5 min/day)."
    ),
    output_type=BriefCheckOutput,
)


# ---------------- Input guardrail ----------------
@input_guardrail
async def brief_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    input: str | List[TResponseInputItem],
) -> GuardrailFunctionOutput:
    result = await Runner.run(brief_guardrail_agent, input, context=ctx.context, max_turns=1)
    output: BriefCheckOutput = result.final_output  # type: ignore
    return GuardrailFunctionOutput(output_info=output, tripwire_triggered=not output.allowed)


# ---------------- Output guardrail ----------------
@output_guardrail
async def roadmap_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    output: RoadmapOutput,
) -> GuardrailFunctionOutput:
    ok = True
    reasons: List[str] = []

    if len(output.resources) == 0 and len(output.videos) == 0:
        ok = False
        reasons.append("No study materials found (resources/videos empty).")

    for r in output.resources:
        if len(r.why) > 200:
            ok = False
            reasons.append("Resource rationale too long.")
            break
    for v in output.videos:
        if len(v.why) > 200:
            ok = False
            reasons.append("Video rationale too long.")
            break

    if len(output.exercises) == 0:
        ok = False
        reasons.append("No exercises returned.")

    return GuardrailFunctionOutput(
        output_info=PlanCheckOutput(ok=ok, reason="; ".join(reasons) if reasons else "ok"),
        tripwire_triggered=not ok,
    )


# ---- Exercise Coach (to fill a single exercise for a given topic/day) ----
exercise_coach = Agent(
    name="Exercise Coach",
    instructions=(
        "Given a day topic and time budget, propose ONE practical exercise a learner can do today. "
        "It must be realistic and measurable, sized <= the time budget. "
        "Output MUST match ExerciseItem: title, steps[3-6], estimate_minutes."
    ),
    output_type=ExerciseItem,
)

async def make_exercise_for_topic(topic: str, estimate_minutes: int) -> ExerciseItem:
    prompt = (
        f"Topic: {topic}\n"
        f"Time budget: {estimate_minutes} minutes (estimate_minutes MUST be <= {estimate_minutes}).\n"
        "Constraints: 3–6 short steps, concrete and measurable; no advanced tools; "
        "include file names or concrete artifacts when relevant."
    )
    res = await Runner.run(exercise_coach, prompt, max_turns=3)
    ex: ExerciseItem = res.final_output  # type: ignore
    if ex.estimate_minutes > estimate_minutes:  # extra safety clamp
        ex.estimate_minutes = estimate_minutes
    return ex


# ---- Day Themer (NEW): create dynamic day titles from brief/goals ----
themer = Agent(
    name="Day Themer",
    instructions=(
        "Design a coherent sequence of day titles for a learning plan. "
        "Use the learner's brief and goals as INPUT SIGNALS only—do NOT simply echo them. "
        "Titles should flow from fundamentals to slightly more advanced, each <= 80 chars. "
        "Return JSON with key 'topics': an ordered list of day titles. "
        "Focus on clarity and real study flow."
    ),
    output_type=DayThemesOut,
)

async def run_day_themer(inp: GenerateScheduleIn) -> List[str]:
    n = max(1, min(inp.duration_days, 14))
    msg = (
        "Brief: {brief}\n"
        "Goals (inspiration only): {goals}\n"
        "Duration: {days} days\n"
        "Daily minutes: {mins}\n"
        "Requirement: produce exactly {days} day titles that form a sensible study sequence.\n"
        "Do NOT just copy the goals. Titles must be specific and instructional (e.g., 'CSS Flexbox Layout Basics')."
    ).format(
        brief=inp.brief,
        goals=", ".join(inp.goals) if inp.goals else "none",
        days=n,
        mins=inp.daily_minutes,
    )
    res = await Runner.run(themer, msg, max_turns=4)
    out: DayThemesOut = res.final_output  # type: ignore
    topics = [t.strip() for t in (out.topics or []) if t and t.strip()]
    return topics[:n]


# ---------------- Manager Agent ----------------
manager = Agent(
    name="Manager",
    instructions=(
        "You produce a learner-friendly preview: an 'overview' plus lists of 'resources', 'videos', and 'exercises'. "
        "Use tools (web_search, video_search) to curate HIGH-SIGNAL items aligned to goals. "
        "Respect pace_rules, keep 'why' rationales <=180 chars, avoid long courses/playlists.\n\n"
        "OUTPUT MUST MATCH the RoadmapOutput schema exactly."
    ),
    tools=[web_search, video_search, pace_rules],
    output_type=RoadmapOutput,
    input_guardrails=[brief_guardrail],
    output_guardrails=[roadmap_guardrail],
)

# ---------------- Entry point used by routes ----------------
async def run_manager(inp: GenerateScheduleIn) -> RoadmapOutput:
    """
    Ask the manager for enough items to cover all days:
      - 2 resources/day
      - 1 video/day
      - 1 exercise/day
    """
    days = min(max(1, inp.duration_days), 12)
    need_r = min(24, days * 2)
    need_v = min(24, days * 1)
    need_e = min(24, days * 1)

    msg = (
        "Brief: {brief}\n"
        "Goals: {goals}\n"
        "Daily minutes: {mins}\n"
        "Timezone: {tz}\n"
        "Targets: return AT LEAST {need_r} resources (2/day), {need_v} videos (1/day), and {need_e} exercises (1/day). "
        "Prefer short reads (3–5 min) and ≤10-min videos. Each item MUST include a crisp 'why' focusing on value.\n"
        "Constraints: favor beginner-friendly pacing unless goals indicate otherwise; avoid long playlists."
    ).format(
        brief=inp.brief,
        goals=", ".join(inp.goals),
        mins=inp.daily_minutes,
        tz=inp.timezone,
        need_r=need_r,
        need_v=need_v,
        need_e=need_e,
    )

    try:
        coro = Runner.run(manager, msg, max_turns=10)
        result = await asyncio.wait_for(coro, timeout=90)
    except asyncio.TimeoutError:
        raise RuntimeError("Agent run timed out after 90s")

    return result.final_output  # type: ignore

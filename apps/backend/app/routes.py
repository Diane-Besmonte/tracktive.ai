# from __future__ import annotations
# from fastapi import APIRouter, HTTPException, Request

# from agents import InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered

# from .schemas import GenerateScheduleIn, ScheduleOutput, RoadmapOutput
# from .scheduler import compose_schedule
# from .rate_limit import singleflight, AlreadyRunning
# from .observability import root_trace

# from .agents_oa import run_manager as run_manager_preview

# router = APIRouter()

# @router.post("/generate-roadmap", response_model=ScheduleOutput)
# async def generate_roadmap(req: Request, body: GenerateScheduleIn):
#     # per-IP single-flight to avoid spam clicks
#     client_ip = getattr(req.client, "host", "unknown")
#     key = f"gen:{client_ip}"

#     try:
#         with root_trace("generate-roadmap", inputs=body.model_dump()):
#             async with singleflight.guard(key):
#                 # 1) run agent with SDK guardrails
#                 try:
#                     preview: RoadmapOutput = await run_manager_preview(body)
#                 except InputGuardrailTripwireTriggered as e:
#                     # bad/unsafe brief → 400
#                     raise HTTPException(status_code=400, detail=f"Input guardrail: {e}") from e
#                 except OutputGuardrailTripwireTriggered as e:
#                     # bad final output → 502 to indicate upstream agent failure
#                     raise HTTPException(status_code=502, detail=f"Output guardrail: {e}") from e

#                 # 2) compose day_1..N
#                 schedule = compose_schedule(body, preview)
#                 return schedule

#     except AlreadyRunning:
#         raise HTTPException(
#             status_code=429,
#             detail="A generation is already in progress for your client. Please wait for it to finish.",
#             headers={"Retry-After": "5"},
#         )
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to generate roadmap: {e}")

# ==================================================================

# from __future__ import annotations
# from fastapi import APIRouter, HTTPException, Request

# from agents import InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered

# from .schemas import GenerateScheduleIn, ScheduleOutput, RoadmapOutput
# from .scheduler import compose_schedule
# from .rate_limit import singleflight, AlreadyRunning
# from .observability import root_trace

# from .agents_oa import run_manager as run_manager_preview
# from .utils.linkcheck import filter_valid_resources, filter_valid_videos
# from .utils.backfill import backfill_resources, backfill_videos  # NEW

# router = APIRouter()

# @router.post("/generate-roadmap", response_model=ScheduleOutput)
# async def generate_roadmap(req: Request, body: GenerateScheduleIn):
#     client_ip = getattr(req.client, "host", "unknown")
#     key = f"gen:{client_ip}"

#     try:
#         with root_trace("generate-roadmap", inputs=body.model_dump()):
#             async with singleflight.guard(key):
#                 # 1) run agent (SDK guardrails raise typed errors)
#                 try:
#                     preview: RoadmapOutput = await run_manager_preview(body)
#                 except InputGuardrailTripwireTriggered as e:
#                     raise HTTPException(status_code=400, detail=f"Input guardrail: {e}") from e
#                 except OutputGuardrailTripwireTriggered as e:
#                     raise HTTPException(status_code=502, detail=f"Output guardrail: {e}") from e

#                 # 2) validate live links first
#                 try:
#                     good_res = await filter_valid_resources(preview.resources)
#                     good_vids = await filter_valid_videos(preview.videos)
#                 except Exception:
#                     # if validator fails, keep originals
#                     good_res, good_vids = preview.resources, preview.videos

#                 # 3) backfill to meet minimums if items got dropped
#                 try:
#                     good_res = await backfill_resources(body.brief, body.goals, good_res, need_at_least=2)
#                     good_vids = await backfill_videos(body.brief, body.goals, good_vids, need_at_least=1)
#                 except Exception:
#                     # if backfill fails, proceed with whatever we have
#                     pass

#                 preview = RoadmapOutput(
#                     overview=preview.overview,
#                     resources=good_res[:8],
#                     videos=good_vids[:8],
#                     exercises=preview.exercises[:6],  # keep whatever the agent returned
#                 )

#                 # 4) compose day_1..N
#                 schedule = compose_schedule(body, preview)
#                 return schedule

#     except AlreadyRunning:
#         raise HTTPException(
#             status_code=429,
#             detail="A generation is already in progress for your client. Please wait for it to finish.",
#             headers={"Retry-After": "5"},
#         )
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to generate roadmap: {e}")


# apps/backend/app/routes.py
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Request

from agents import InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered

from .schemas import GenerateScheduleIn, ScheduleOutput, RoadmapOutput, ExerciseItem
from .scheduler import compose_schedule
from .rate_limit import singleflight, AlreadyRunning
from .observability import root_trace

from .agents_oa import run_manager as run_manager_preview
from .agents_oa import make_exercise_for_topic, run_day_themer  # NEW
from .utils.linkcheck import filter_valid_resources, filter_valid_videos
from .utils.backfill import backfill_resources, backfill_videos

router = APIRouter()

# Per-day targets
RES_MIN, RES_MAX = 2, 2
VID_MIN, VID_MAX = 1, 1
EX_MIN, EX_MAX = 1, 1

async def _ensure_day_minimums(schedule: ScheduleOutput, brief: str, goals: list[str], daily_minutes: int) -> ScheduleOutput:
    """
    Ensure each day has at least:
      - 2 resources
      - 1 video
      - 1 exercise
    Validate/backfill links and generate exercises as needed.
    """
    for key, day in schedule.data.items():
        topic = day.topic

        # ---- RESOURCES ----
        if len(day.resources) < RES_MIN:
            try:
                need = RES_MIN
                filled = await backfill_resources(f"{topic} {brief}", [topic] + goals, day.resources, need_at_least=need)
                good = await filter_valid_resources(filled[:RES_MAX])
                day.resources = (good or day.resources)[:RES_MAX]
            except Exception:
                day.resources = day.resources[:RES_MAX]

        # ---- VIDEOS ----
        if len(day.videos) < VID_MIN:
            try:
                need = VID_MIN
                filled = await backfill_videos(f"{topic} {brief}", [topic] + goals, day.videos, need_at_least=need)
                good = await filter_valid_videos(filled[:VID_MAX])
                day.videos = (good or day.videos)[:VID_MAX]
            except Exception:
                day.videos = day.videos[:VID_MAX]

        # ---- EXERCISES ----
        if len(day.exercises) < EX_MIN:
            try:
                ex = await make_exercise_for_topic(topic, daily_minutes)
                if ex.estimate_minutes > daily_minutes:
                    ex.estimate_minutes = daily_minutes
                day.exercises = [ex]
            except Exception:
                day.exercises = [
                    ExerciseItem(
                        title=f"Practice: {topic}",
                        steps=["Study the resource", "Apply to one example", "Write two takeaways"],
                        estimate_minutes=min(daily_minutes, 30),
                    )
                ]

        # final trim to caps (UI simplicity)
        day.resources = (day.resources or [])[:RES_MAX]
        day.videos = (day.videos or [])[:VID_MAX]
        day.exercises = (day.exercises or [])[:EX_MAX]

    return schedule

@router.post("/generate-roadmap", response_model=ScheduleOutput)
async def generate_roadmap(req: Request, body: GenerateScheduleIn):
    client_ip = getattr(req.client, "host", "unknown")
    key = f"gen:{client_ip}"

    try:
        with root_trace("generate-roadmap", inputs=body.model_dump()):
            async with singleflight.guard(key):
                # 1) run agent (SDK guardrails raise typed errors)
                try:
                    preview: RoadmapOutput = await run_manager_preview(body)
                except InputGuardrailTripwireTriggered as e:
                    raise HTTPException(status_code=400, detail=f"Input guardrail: {e}") from e
                except OutputGuardrailTripwireTriggered as e:
                    raise HTTPException(status_code=502, detail=f"Output guardrail: {e}") from e

                # 2) validate links at preview level
                try:
                    good_res = await filter_valid_resources(preview.resources)
                    good_vids = await filter_valid_videos(preview.videos)
                except Exception:
                    good_res, good_vids = preview.resources, preview.videos

                # 3) backfill preview to reach at least "days * per-day" totals
                try:
                    days = min(max(1, body.duration_days), 12)
                    need_r_total = min(24, days * RES_MIN)
                    need_v_total = min(24, days * VID_MIN)
                    good_res = await backfill_resources(body.brief, body.goals, good_res, need_at_least=need_r_total)
                    good_vids = await backfill_videos(body.brief, body.goals, good_vids, need_at_least=need_v_total)
                except Exception:
                    pass

                preview = RoadmapOutput(
                    overview=preview.overview,
                    resources=good_res[:24],
                    videos=good_vids[:24],
                    exercises=preview.exercises[:24],
                )

                # 4) NEW: generate dynamic day titles (not just echo goals)
                try:
                    themed_topics = await run_day_themer(body)
                except Exception:
                    themed_topics = []

                # 5) compose day_1..N using themed topics + alignment scoring
                schedule = compose_schedule(body, preview, day_topics=themed_topics)

                # 6) guarantee per-day minimums (validated + generated as needed)
                schedule = await _ensure_day_minimums(schedule, body.brief, body.goals, body.daily_minutes)

                return schedule

    except AlreadyRunning:
        raise HTTPException(
            status_code=429,
            detail="A generation is already in progress for your client. Please wait for it to finish.",
            headers={"Retry-After": "5"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate roadmap: {e}")

import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import Navbar from "../../components/layout/Navbar";
import Page from "../../components/layout/Page";
import Card from "../../components/ui/Card";
import ProgressBar from "../../components/ui/ProgressBar";
import api from "../../lib/api";
import { apiErrorMessage } from "../../lib/err";
import { toTitleCase } from "../../lib/text";

type AnyObj = Record<string, any>;

function safeParseJSON(x: any): any {
  if (typeof x !== "string") return x;
  try { return JSON.parse(x); } catch { return x; }
}

function daysFromDataMap(data: any): AnyObj[] {
  if (!data || typeof data !== "object") return [];
  return Object.entries(data)
    .filter(([k, v]) => /^day[_\s-]?\d+$/i.test(String(k)) && v && typeof v === "object")
    .map(([k, v]) => ({ day: Number(String(k).match(/\d+/)?.[0] || 0), ...(v as AnyObj) }))
    .filter((x) => x.day > 0)
    .sort((a, b) => a.day - b.day);
}

function looksLikeDayArray(arr: any): arr is AnyObj[] {
  return Array.isArray(arr) && arr.length > 0 && arr.every((el) => el && typeof el === "object");
}

function normalizeSession(session: AnyObj) {
  const rawPlan = session?.plan ?? session?.plan_json ?? session?.data ?? session?.roadmap ?? session;
  const plan = safeParseJSON(rawPlan);

  const overview =
    plan?.overview ??
    plan?.roadmap?.overview ??
    session?.overview ??
    session?.plan?.overview ??
    "";

  let days: AnyObj[] =
    daysFromDataMap(plan?.data) ||
    daysFromDataMap(session?.data);

  if (!days.length) {
    const candidates = [
      plan?.roadmap?.days,
      plan?.days,
      session?.plan?.roadmap?.days,
      session?.plan?.days,
      session?.roadmap?.days,
      session?.days,
    ];
    for (const c of candidates) {
      if (looksLikeDayArray(c)) { days = c; break; }
    }
  }

  return { overview, days, plan };
}

export default function SessionDetail() {
  const { id } = useParams<{ id: string }>();

  const [session, setSession] = useState<AnyObj | null>(null);
  const [progress, setProgress] = useState<Record<number, boolean>>({});
  const [summary, setSummary] = useState<{
    total_days?: number;
    completed?: number;
    not_completed?: number;
    progress_in_percent?: string | number;
  }>({});
  const [pendingDay, setPendingDay] = useState<number | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function loadProgress() {
    try {
      const pm = await api.get(`/sessions/${id}/progress`, { params: { _ts: Date.now() } });
      const map = pm.data?.breakdown || pm.data || {};
      const m: Record<number, boolean> = {};
      Object.entries(map).forEach(([k, v]: any) => {
        const n = Number(String(k).match(/\d+/)?.[0] || 0);
        if (n) m[n] = !!v?.completed;
      });
      setProgress(m);
      setSummary({
        total_days: pm.data?.total_days,
        completed: pm.data?.completed,
        not_completed: pm.data?.not_completed,
        progress_in_percent: pm.data?.progress_in_percent,
      });
    } catch {
      /* optional endpoint; ignore if missing */
    }
  }

  async function loadAll() {
    setErr(null);
    try {
      const res = await api.get(`/sessions/${id}`);
      setSession(res.data);
      await loadProgress();
    } catch (e: any) {
      setErr(apiErrorMessage(e));
    }
  }

  useEffect(() => { loadAll(); /* eslint-disable-next-line */ }, [id]);

  async function toggle(day: number, done: boolean) {
    setPendingDay(day);
    setProgress((prev) => ({ ...prev, [day]: !done })); // optimistic
    try {
      await api.post(`/sessions/${id}/day/${day}/${done ? "undo" : "complete"}`, {});
      await loadProgress();
    } catch (e) {
      setProgress((prev) => ({ ...prev, [day]: done })); // revert
      alert(apiErrorMessage(e));
    } finally {
      setPendingDay(null);
    }
  }

  // ---- hooks that must always run
  const normalized = useMemo(
    () => (session ? normalizeSession(session) : { overview: "", days: [], plan: null }),
    [session]
  );
  const displayTitle = useMemo(
    () => (session?.title ? String(session.title).trim() : "Session"),
    [session]
  );
  const dayList = normalized.days;

  const progressPct = useMemo(() => {
    const raw = summary?.progress_in_percent;
    if (typeof raw === "string") {
      const n = parseInt(raw.replace(/[^\d]/g, ""), 10);
      return Number.isFinite(n) ? Math.max(0, Math.min(100, n)) : 0;
    }
    if (typeof raw === "number") {
      return Math.max(0, Math.min(100, raw));
    }
    return 0;
  }, [summary]);

  // ---- rendering
  if (err) {
    return (
      <>
        <Navbar />
        <Page maxWidth="max-w-3xl">
          <Card soft><div className="text-red-600">{err}</div></Card>
        </Page>
      </>
    );
  }

  if (!session) {
    return (
      <>
        <Navbar />
        <Page maxWidth="max-w-3xl">
          <Card soft>
            <div className="space-y-3">
              <div className="h-6 w-40 bg-surface rounded animate-pulse" />
              <div className="h-3 w-24 bg-surface rounded animate-pulse" />
              <div className="h-20 w-full bg-surface rounded animate-pulse" />
            </div>
          </Card>
        </Page>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <Page maxWidth="max-w-3xl">
        {/* Header */}
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-xl sm:text-2xl font-semibold">{displayTitle}</h1>
            {summary?.progress_in_percent != null && (
              <div className="mt-1 text-sm opacity-80">
                {progressPct}%{" "}
                <span className="opacity-70">
                  ({summary.completed ?? 0}/{summary.total_days ?? 0})
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Progress */}
        {summary?.progress_in_percent != null && (
          <Card soft className="mt-4">
            <div className="flex items-center justify-between gap-2">
              <div className="text-sm font-medium">Progress</div>
              <div className="text-xs opacity-70">
                {progressPct}% ({summary.completed ?? 0}/{summary.total_days ?? 0})
              </div>
            </div>
            <div className="mt-2">
              <ProgressBar value={progressPct} />
            </div>
          </Card>
        )}

        {/* Overview */}
        {!!normalized.overview && (
          <Card soft className="mt-4">
            <h2 className="text-base sm:text-lg font-semibold">Overview</h2>
            <p className="mt-1 text-sm sm:text-base opacity-80">{String(normalized.overview)}</p>
          </Card>
        )}

        {/* Days — styled to match Home preview section */}
        <div className="mt-4 space-y-3 sm:space-y-4">
          {dayList.length === 0 ? (
            <Card soft>No days found.</Card>
          ) : (
            <ul className="space-y-3 sm:space-y-4">
              {dayList.map((d: AnyObj, idx: number) => {
                const dayNum = Number(d?.day || idx + 1);
                const done = !!progress[dayNum];
                const isPending = pendingDay === dayNum;
                const rawTitle = d.topic || d.theme || d.title || "—";
                const titleText = toTitleCase(String(rawTitle));

                return (
                  <li key={dayNum} className="rounded-3xl border border-border bg-bg p-4 sm:p-6 shadow-card">
                    {/* Header row like on Home preview (title + small meta + action on desktop) */}
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                      <h3 className="text-base sm:text-lg font-semibold">
                        Day {dayNum}: {titleText}
                      </h3>

                      {/* Status + Action (action moves to top-right on desktop; sits below on mobile) */}
                      <div className="flex items-center gap-2">
                        <div className="text-xs sm:text-sm opacity-70">{done ? "Completed" : "Pending"}</div>
                        <button
                          onClick={() => toggle(dayNum, done)}
                          disabled={isPending}
                          className={`h-10 px-4 text-sm rounded-2xl inline-flex items-center justify-center transition-colors ${
                            done ? "border border-border" : "bg-primary text-white"
                          } ${isPending ? "opacity-80" : ""}`}
                          aria-pressed={done}
                        >
                          {isPending ? "…" : done ? "Undo" : "Complete"}
                        </button>
                      </div>
                    </div>

                    {/* Inner surface card (matches Home preview inner box) */}
                    <div className="mt-4 rounded-2xl border border-border bg-surface p-4">
                      {d.description && (
                        <p className="text-sm sm:text-base opacity-80">{String(d.description)}</p>
                      )}

                      {/* Resources + Video grid (like Home: two columns on sm+) */}
                      {(Array.isArray(d.resources) && d.resources.length > 0) ||
                      (Array.isArray(d.videos) && d.videos.length > 0) ? (
                        <div className="mt-3 grid gap-2 sm:grid-cols-2">
                          {/* Resources */}
                          {Array.isArray(d.resources) && d.resources.length > 0 && (
                            <div>
                              <div className="text-sm font-medium">Resources</div>
                              {d.resources.map((r: any, i: number) => (
                                <a
                                  key={i}
                                  href={r.url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="mt-1 block underline text-sm break-all"
                                  title={r.why || undefined}
                                >
                                  {r.title || r.url}
                                </a>
                              ))}
                            </div>
                          )}
                          {/* Videos */}
                          {Array.isArray(d.videos) && d.videos.length > 0 && (
                            <div>
                              <div className="text-sm font-medium">{d.videos.length > 1 ? "Videos" : "Video"}</div>
                              {d.videos.map((v: any, i: number) => (
                                <a
                                  key={i}
                                  href={v.url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="mt-1 block underline text-sm break-all"
                                  title={v.why || undefined}
                                >
                                  {v.title || v.url}{v.duration ? ` (${v.duration})` : ""}
                                </a>
                              ))}
                            </div>
                          )}
                        </div>
                      ) : null}

                      {/* Exercises */}
                      {Array.isArray(d.exercises) && d.exercises.length > 0 && (
                        <div className="mt-3">
                          <div className="text-sm font-medium">Exercise{d.exercises.length > 1 ? "s" : ""}</div>
                          {d.exercises.map((x: any, i: number) => (
                            <div key={i} className="mt-1">
                              <div className="text-sm font-medium">{x.title || "Exercise"}</div>
                              {Array.isArray(x.steps) && x.steps.length > 0 ? (
                                <ul className="mt-1 ml-5 list-disc text-sm">
                                  {x.steps.map((s: any, j: number) => <li key={j}>{String(s)}</li>)}
                                </ul>
                              ) : null}
                              {x.estimate_minutes && (
                                <div className="text-xs opacity-70 mt-1">Duration: ~{x.estimate_minutes} min</div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </Page>
    </>
  );
}

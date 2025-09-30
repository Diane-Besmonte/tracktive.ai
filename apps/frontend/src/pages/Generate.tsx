import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/layout/Navbar";
import Page from "../components/layout/Page";
import Card from "../components/ui/Card";
import api from "../lib/api";
import { apiErrorMessage } from "../lib/err";
import LoadingOverlay from "../components/ui/LoadingOverlay";

type AnyObj = Record<string, any>;

// --- Timezone options (curated common IANA zones) ---
const TIMEZONE_GROUPS: { group: string; zones: string[] }[] = [
  {
    group: "Americas",
    zones: [
      "Pacific/Honolulu",
      "America/Anchorage",
      "America/Los_Angeles",
      "America/Denver",
      "America/Chicago",
      "America/New_York",
      "America/Toronto",
      "America/Mexico_City",
      "America/Bogota",
      "America/Lima",
      "America/Santiago",
      "America/Argentina/Buenos_Aires",
      "America/Sao_Paulo",
    ],
  },
  {
    group: "Europe",
    zones: [
      "Europe/London",
      "Europe/Dublin",
      "Europe/Lisbon",
      "Europe/Madrid",
      "Europe/Paris",
      "Europe/Brussels",
      "Europe/Amsterdam",
      "Europe/Berlin",
      "Europe/Rome",
      "Europe/Zurich",
      "Europe/Vienna",
      "Europe/Warsaw",
      "Europe/Athens",
      "Europe/Istanbul",
      "Europe/Moscow",
    ],
  },
  {
    group: "Africa & Middle East",
    zones: [
      "Africa/Cairo",
      "Africa/Johannesburg",
      "Africa/Nairobi",
      "Asia/Jerusalem",
      "Asia/Beirut",
      "Asia/Baghdad",
      "Asia/Riyadh",
      "Asia/Tehran",
      "Asia/Dubai",
    ],
  },
  {
    group: "Asia",
    zones: [
      "Asia/Karachi",
      "Asia/Kolkata",
      "Asia/Dhaka",
      "Asia/Bangkok",
      "Asia/Jakarta",
      "Asia/Kuala_Lumpur",
      "Asia/Singapore",
      "Asia/Manila",
      "Asia/Taipei",
      "Asia/Hong_Kong",
      "Asia/Shanghai",
      "Asia/Seoul",
      "Asia/Tokyo",
    ],
  },
  {
    group: "Oceania",
    zones: [
      "Australia/Perth",
      "Australia/Adelaide",
      "Australia/Melbourne",
      "Australia/Sydney",
      "Pacific/Auckland",
    ],
  },
];

// Flatten for quick membership checks
const ALL_TZS = TIMEZONE_GROUPS.flatMap((g) => g.zones);

// Try to detect browser timezone
const DETECTED_TZ =
  (Intl && Intl.DateTimeFormat && Intl.DateTimeFormat().resolvedOptions().timeZone) ||
  "Asia/Manila";

function daysFromDataMap(data: any) {
  if (!data || typeof data !== "object") return [];
  return Object.entries(data)
    .filter(([k, v]) => /^day[_\s-]?\d+$/i.test(String(k)) && v && typeof v === "object")
    .map(([k, v]) => ({ day: Number(String(k).match(/\d+/)?.[0] || 0), ...(v as AnyObj) }))
    .filter((x) => x.day > 0)
    .sort((a, b) => a.day - b.day);
}

export default function Generate() {
  const navigate = useNavigate();

  const [brief, setBrief] = useState("");
  const [goalsRaw, setGoalsRaw] = useState("");
  const [dailyMinutes, setDailyMinutes] = useState<number>(30);
  const [durationDays, setDurationDays] = useState<number>(7);
  const [preferredTime, setPreferredTime] = useState("19:00");
  const [timezone, setTimezone] = useState<string>(DETECTED_TZ || "Asia/Manila");

  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState<AnyObj | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const goals = useMemo(
    () =>
      goalsRaw
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
    [goalsRaw]
  );

  async function generate(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setErr(null);
    try {
      const body = {
        brief,
        goals,
        daily_minutes: Number(dailyMinutes),
        duration_days: Number(durationDays),
        preferred_time: preferredTime,
        timezone,
      };
      const res = await api.post("/generate-roadmap", body);
      setPreview(res.data);
    } catch (e) {
      setErr(apiErrorMessage(e));
    } finally {
      setLoading(false);
    }
  }

  async function savePlan() {
    if (!preview) return;
    try {
      const title = deriveTitle(preview, durationDays, preferredTime);
      const payload = {
        title,
        brief,
        goals,
        daily_minutes: dailyMinutes,
        duration_days: durationDays,
        preferred_time: preferredTime,
        timezone,
        plan: preview, // send whole preview json
      };
      const res = await api.post("/sessions", payload);
      const id = res.data?.id ?? res.data?.session_id;
      navigate(`/sessions/${id}`);
    } catch (e) {
      alert(apiErrorMessage(e));
    }
  }

  const days = useMemo(() => daysFromDataMap(preview?.data), [preview]);

  const detectedNotInList = useMemo(
    () => timezone && !ALL_TZS.includes(DETECTED_TZ),
    [timezone]
  );

  return (
    <>
      <Navbar />
      <Page maxWidth="max-w-5xl">
        <Card>
          <h1 className="text-xl sm:text-2xl font-semibold">Generate roadmap</h1>
          <p className="mt-1 text-sm sm:text-base opacity-80">
            Brief + goals → organized daily plan with resources, videos, and exercises.
          </p>

          <form onSubmit={generate} className="mt-5 grid gap-3 sm:gap-4 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <label className="text-sm font-medium">Brief</label>
              <textarea
                className="mt-1 w-full rounded-xl border border-border bg-bg p-3"
                rows={3}
                placeholder="e.g., Learn RAG with OpenAI Agents for a portfolio-ready demo."
                value={brief}
                onChange={(e) => setBrief(e.target.value)}
                required
              />
            </div>

            <div className="sm:col-span-2">
              <label className="text-sm font-medium">Goals (comma-separated)</label>
              <input
                className="mt-1 w-full rounded-xl border border-border bg-bg p-3"
                placeholder="python basics, files & scripts, automation"
                value={goalsRaw}
                onChange={(e) => setGoalsRaw(e.target.value)}
              />
            </div>

            <div>
              <label className="text-sm font-medium">Daily minutes</label>
              <input
                type="number"
                className="mt-1 w-full rounded-xl border border-border bg-bg p-3"
                value={dailyMinutes}
                onChange={(e) => setDailyMinutes(Number(e.target.value))}
                min={5}
                step={5}
                required
              />
            </div>

            <div>
              <label className="text-sm font-medium">Duration (days)</label>
              <input
                type="number"
                className="mt-1 w-full rounded-xl border border-border bg-bg p-3"
                value={durationDays}
                onChange={(e) => setDurationDays(Number(e.target.value))}
                min={1}
                required
              />
            </div>

            <div>
              <label className="text-sm font-medium">Preferred time (HH:MM)</label>
              <input
                type="time"
                className="mt-1 w-full rounded-xl border border-border bg-bg p-3"
                value={preferredTime}
                onChange={(e) => setPreferredTime(e.target.value)}
                required
              />
            </div>

            {/* Timezone dropdown */}
            <div className="sm:col-span-1">
              <label htmlFor="timezone" className="text-sm font-medium">Timezone</label>
              <div className="mt-1 relative">
                <select
                  id="timezone"
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                  required
                  className="w-full h-11 rounded-xl border border-border bg-bg pl-3 pr-10 text-sm sm:text-base
                            appearance-none focus:outline-none focus:ring-2 focus:ring-primary/40"
                  aria-label="Timezone"
                >
                  {/* If the detected zone isn’t in the curated list, show it on top */}
                  {detectedNotInList && (
                    <optgroup label="Detected">
                      <option value={DETECTED_TZ}>{DETECTED_TZ}</option>
                    </optgroup>
                  )}

                  {TIMEZONE_GROUPS.map((g) => (
                    <optgroup key={g.group} label={g.group}>
                      {g.zones.map((z) => (
                        <option key={z} value={z}>
                          {z}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </select>

                {/* Chevron */}
                <svg
                  className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 opacity-70"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  aria-hidden="true"
                >
                  <path
                    fillRule="evenodd"
                    d="M5.23 7.21a.75.75 0 011.06.02L10 10.17l3.71-2.94a.75.75 0 111.04 1.08l-4.24 3.36a.75.75 0 01-.94 0L5.21 8.31a.75.75 0 01.02-1.1z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>

              <div className="mt-1 text-xs opacity-70">
                Auto-detected: <span className="font-medium">{DETECTED_TZ}</span>
              </div>
            </div>

            <div className="sm:col-span-2 flex flex-col sm:flex-row gap-2">
              <button
                type="submit"
                disabled={loading}
                className="h-11 rounded-2xl bg-primary text-white px-4 inline-flex items-center justify-center"
              >
                {loading ? "Generating…" : "Generate"}
              </button>
              {preview && (
                <>
                  <button
                    type="button"
                    onClick={generate}
                    disabled={loading}
                    className="h-11 rounded-2xl text-primary border border-primary px-4 inline-flex items-center justify-center"
                  >
                    Regenerate
                  </button>
                  <button
                    type="button"
                    onClick={savePlan}
                    className="h-11 rounded-2xl border border-border bg-[#2d539a] text-white px-4 inline-flex items-center justify-center"
                  >
                    Save plan
                  </button>
                </>
              )}
            </div>

            {err && (
              <div className="sm:col-span-2 text-sm text-red-600">{err}</div>
            )}
          </form>
        </Card>

        {preview && (
          <Card soft className="mt-4">
            <h2 className="text-lg sm:text-xl font-semibold">Preview</h2>
            {!!preview?.overview && (
              <p className="mt-1 text-sm sm:text-base opacity-80">{String(preview.overview)}</p>
            )}

            <div className="mt-4 space-y-3 sm:space-y-4">
              {days.length === 0 ? (
                <div className="text-sm opacity-80">No day-by-day items found in the preview.</div>
              ) : (
                <ul className="space-y-3 sm:space-y-4">
                  {days.map((d: AnyObj, i: number) => (
                    <li key={i} className="rounded-2xl border border-border bg-bg p-3 sm:p-4">
                      <div className="text-base sm:text-lg font-semibold">
                        Day {d.day}: {d.topic || d.theme || d.title || "—"}
                      </div>
                      {d.description && (
                        <p className="mt-1 text-sm sm:text-base opacity-80">{String(d.description)}</p>
                      )}
                      {Array.isArray(d.resources) && d.resources.length > 0 && (
                        <div className="mt-2">
                          <div className="text-sm font-medium">Resources</div>
                          <div className="mt-1 grid gap-1">
                            {d.resources.map((r: any, idx: number) => (
                              <a
                                key={idx}
                                href={r.url}
                                target="_blank"
                                rel="noreferrer"
                                className="underline text-sm break-all"
                              >
                                {r.title || r.url}
                              </a>
                            ))}
                          </div>
                        </div>
                      )}
                      {Array.isArray(d.videos) && d.videos.length > 0 && (
                        <div className="mt-2">
                          <div className="text-sm font-medium">Videos</div>
                          <div className="mt-1 grid gap-1">
                            {d.videos.map((v: any, idx: number) => (
                              <a
                                key={idx}
                                href={v.url}
                                target="_blank"
                                rel="noreferrer"
                                className="underline text-sm break-all"
                              >
                                {v.title || v.url}{v.duration ? ` — ${v.duration}` : ""}
                              </a>
                            ))}
                          </div>
                        </div>
                      )}
                      {Array.isArray(d.exercises) && d.exercises.length > 0 && (
                        <div className="mt-2">
                          <div className="text-sm font-medium">Exercises</div>
                          <ul className="mt-1 list-disc ml-5 text-sm">
                            {d.exercises.map((x: any, idx: number) => (
                              <li key={idx}>{x.title || String(x)}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </Card>
        )}
        <LoadingOverlay
          show={loading}
          message="Generating your learning path…"
          submessage="We’re picking high-quality reads, videos, and exercises for each day."
        />
      </Page>
    </>
  );
}

function deriveTitle(preview: AnyObj, days: number, time: string) {
  const base = (preview?.title || preview?.roadmap?.title || "").trim();
  if (base) return `${base} (${days} days @ ${time})`;
  const firstGoal =
    Array.isArray(preview?.goals) && preview.goals.length ? preview.goals[0] : "";
  if (firstGoal) return `${firstGoal} (${days} days @ ${time})`;
  return `${days} days @ ${time}`;
}

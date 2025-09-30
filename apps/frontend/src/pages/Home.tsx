import { useNavigate, Link } from "react-router-dom";
import Navbar from "../components/layout/Navbar";
import { isLoggedIn } from "../lib/auth";

export default function Home() {
  const navigate = useNavigate();

  function start() {
    if (isLoggedIn()) navigate("/dashboard");
    else navigate("/login");
  }

  return (
    <>
      <Navbar />

      {/* Decorative background blobs (subtle, performance-friendly) */}
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute -top-24 -left-20 h-72 w-72 rounded-full blur-3xl opacity-30 bg-gradient-to-tr from-primary to-[#77b7c5]" />
        <div className="absolute -bottom-24 -right-20 h-72 w-72 rounded-full blur-3xl opacity-25 bg-gradient-to-tr from-[#a3c2e0] to-primary" />
      </div>

      <main className="px-4">
        {/* HERO — mobile-first */}
        <section className="mx-auto max-w-6xl py-10 sm:py-16">
          <div className="relative overflow-hidden rounded-3xl border border-border bg-gradient-to-b from-surface to-bg p-6 sm:p-10 shadow-card">
            {/* Radial glow */}
            <div className="pointer-events-none absolute -top-32 left-1/2 h-72 w-72 -translate-x-1/2 rounded-full bg-primary/20 blur-3xl" />
            <div className="relative">
              <p className="text-xs sm:text-sm uppercase tracking-wide text-muted">AI Learning Planner</p>
              <h1 className="mt-2 text-3xl leading-tight font-bold sm:text-5xl">
                <span className="bg-gradient-to-r from-primary to-[#77b7c5] bg-clip-text text-transparent">
                  Day-by-day roadmaps
                </span>{" "}
                for skills you actually use
              </h1>
              <p className="mt-3 max-w-2xl text-sm sm:text-base opacity-80">
                Tell us your goal and time budget. Get a crisp plan with daily reads, a short video,
                and one hands-on exercise — all mobile-friendly. Track progress and stay consistent.
              </p>

              <div className="mt-5 sm:mt-7 flex flex-col gap-3 sm:flex-row">
                <button
                  onClick={start}
                  className="h-12 rounded-2xl bg-primary text-white px-5 inline-flex items-center justify-center"
                >
                  Start Learning
                </button>
                <a
                  href="#features"
                  className="h-12 rounded-2xl border border-border px-5 inline-flex items-center justify-center"
                >
                  Explore features
                </a>
              </div>

              {/* Quick trust row (placeholder badges) */}
              <div className="mt-8 grid grid-cols-2 gap-2 sm:grid-cols-4">
                {["Fast", "Focused", "Mobile-first", "Private"].map((t) => (
                  <div
                    key={t}
                    className="rounded-xl border border-border bg-bg/70 px-3 py-2 text-center text-xs sm:text-sm"
                  >
                    {t}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* HOW IT WORKS — 3 steps timeline cards */}
        <section className="mx-auto max-w-6xl pb-12 sm:pb-16">
          <div className="grid gap-3 sm:gap-4 sm:grid-cols-3">
            <StepCard
              n="01"
              title="Describe your goal"
              desc="Briefly say what you want to learn and your daily time. We keep it simple."
            />
            <StepCard
              n="02"
              title="Get a daily plan"
              desc="Each day: 1–2 links, a short video, and a practical drill. Minimal fluff."
            />
            <StepCard
              n="03"
              title="Track & iterate"
              desc="Complete/undo, see progress, regenerate when you want a different angle."
            />
          </div>
        </section>

        {/* FEATURES — modern cards with tiny icons */}
        <section id="features" className="mx-auto max-w-6xl pb-12 sm:pb-16">
          <div className="flex items-end justify-between gap-3">
            <h2 className="text-xl sm:text-2xl font-semibold">What you get</h2>
            <Link
              to={isLoggedIn() ? "/generate" : "/login"}
              className="hidden sm:inline-flex h-10 rounded-xl border border-border px-4 items-center"
            >
              Try it now
            </Link>
          </div>

          <div className="mt-4 grid gap-3 sm:gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <FeatureCard
              icon={<IconSparkles />}
              title="AI-generated roadmap"
              desc="Tight overview + day cards with curated resources, videos, and exercises."
            />
            <FeatureCard
              icon={<IconClock />}
              title="Time-boxed"
              desc="Plans respect your daily minutes and preferred time in your timezone."
            />
            <FeatureCard
              icon={<IconCheck />}
              title="Progress tracking"
              desc="One-tap complete/undo with a live progress bar and per-day status."
            />
            <FeatureCard
              icon={<IconShield />}
              title="Guardrails"
              desc="Link checks and validation prevent broken or low-quality resources."
            />
            <FeatureCard
              icon={<IconPhone />}
              title="Mobile-first"
              desc="Large tap targets, clear typography, and a layout tuned for phones."
            />
            <FeatureCard
              icon={<IconRepeat />}
              title="Regenerate"
              desc="Not loving it yet? Regenerate a variant — your saved session stays safe."
            />
          </div>
        </section>

        {/* PREVIEW — example day card (glassy) */}
        <section className="mx-auto max-w-6xl pb-12 sm:pb-16">
          <div className="rounded-3xl border border-border bg-bg p-4 sm:p-6 shadow-card">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <h3 className="text-base sm:text-lg font-semibold">Preview a day</h3>
              <div className="text-xs sm:text-sm opacity-70">Looks familiar from your session page</div>
            </div>
            <div className="mt-4 rounded-2xl border border-border bg-surface p-4">
              <div className="text-base sm:text-lg font-semibold">Day 3: Files & Scripts</div>
              <p className="mt-1 text-sm sm:text-base opacity-80">
                Start with 1–2 links, watch a short example, then finish a quick exercise. Keep notes.
              </p>
              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                <div>
                  <div className="text-sm font-medium">Resources</div>
                  <a className="mt-1 block underline text-sm" href="#" onClick={(e) => e.preventDefault()}>
                    Automate the Boring Stuff — Chapter 1
                  </a>
                </div>
                <div>
                  <div className="text-sm font-medium">Video</div>
                  <a className="mt-1 block underline text-sm" href="#" onClick={(e) => e.preventDefault()}>
                    Python File Handling (6:25)
                  </a>
                </div>
              </div>
              <div className="mt-3">
                <div className="text-sm font-medium">Exercise</div>
                <ul className="mt-1 ml-5 list-disc text-sm">
                  <li>Write a script to rename .txt files, appending “_2024”.</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* CTA BAND */}
        <section className="mx-auto max-w-6xl pb-16">
          <div className="relative overflow-hidden rounded-3xl border border-border bg-gradient-to-r from-[#a3c2e0]/30 to-primary/30 p-6 sm:p-8">
            <div className="relative z-10">
              <h3 className="text-lg sm:text-xl font-semibold">Ready to learn faster?</h3>
              <p className="mt-1 text-sm sm:text-base opacity-80">
                Generate your first roadmap in under a minute.
              </p>
              <div className="mt-4 flex flex-col gap-2 sm:flex-row">
                <button
                  onClick={start}
                  className="h-12 rounded-2xl bg-primary text-white px-5 inline-flex items-center justify-center"
                >
                  Start Learning
                </button>
                <Link
                  to={isLoggedIn() ? "/dashboard" : "/register"}
                  className="h-12 rounded-2xl border border-border px-5 inline-flex items-center justify-center"
                >
                  {isLoggedIn() ? "Go to Dashboard" : "Create an account"}
                </Link>
              </div>
            </div>
            <div className="pointer-events-none absolute -right-10 -bottom-10 h-48 w-48 rounded-full bg-primary/30 blur-2xl" />
          </div>
        </section>
      </main>

      {/* FOOTER */}
      <footer className="border-t border-border py-6 text-center text-xs opacity-70">
        © {new Date().getFullYear()} Tracktive AI — built with FastAPI + React
      </footer>
    </>
  );
}

/* ---------- tiny presentational subcomponents ---------- */

function StepCard({ n, title, desc }: { n: string; title: string; desc: string }) {
  return (
    <article className="rounded-2xl border border-border bg-bg p-4 shadow-card">
      <div className="inline-flex h-8 w-8 items-center justify-center rounded-xl bg-primary/10 text-primary text-xs font-semibold">
        {n}
      </div>
      <h3 className="mt-2 font-semibold">{title}</h3>
      <p className="mt-1 text-sm opacity-80">{desc}</p>
    </article>
  );
}

function FeatureCard({
  icon,
  title,
  desc,
}: {
  icon: React.ReactNode;
  title: string;
  desc: string;
}) {
  return (
    <article className="rounded-2xl border border-border bg-bg p-4 shadow-card">
      <div className="flex items-start gap-3">
        <div className="mt-0.5">{icon}</div>
        <div>
          <div className="font-semibold">{title}</div>
          <p className="mt-1 text-sm opacity-80">{desc}</p>
        </div>
      </div>
    </article>
  );
}

/* Minimal inline icons (no extra deps) */
function IconSparkles() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true" className="opacity-90">
      <path d="M12 3l1.5 3.5L17 8l-3.5 1.5L12 13l-1.5-3.5L7 8l3.5-1.5L12 3zM5 14l1 2 2 1-2 1-1 2-1-2-2-1 2-1 1-2zm12 1l1.2 2.8L21 19l-2.8 1.2L17 23l-1.2-2.8L13 19l2.8-1.2L17 15z" fill="currentColor"/>
    </svg>
  );
}
function IconClock() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true" className="opacity-90">
      <path d="M12 1a11 11 0 100 22 11 11 0 000-22zm1 6h-2v6l5 3 1-1.7-4-2.3V7z" fill="currentColor"/>
    </svg>
  );
}
function IconCheck() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true" className="opacity-90">
      <path d="M20.3 5.7l-11 11-5-5L6.7 10l2.6 2.6 8.4-8.3 2.6 1.4z" fill="currentColor"/>
    </svg>
  );
}
function IconShield() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true" className="opacity-90">
      <path d="M12 2l8 4v6c0 5-3.5 9.7-8 10-4.5-.3-8-5-8-10V6l8-4z" fill="currentColor"/>
    </svg>
  );
}
function IconPhone() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true" className="opacity-90">
      <path d="M17 1H7a2 2 0 00-2 2v18a2 2 0 002 2h10a2 2 0 002-2V3a2 2 0 00-2-2zm0 18H7V5h10v14z" fill="currentColor"/>
    </svg>
  );
}
function IconRepeat() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true" className="opacity-90">
      <path d="M17 1l4 4-4 4V6H8a4 4 0 00-4 4H2a6 6 0 016-6h9V1zM7 23l-4-4 4-4v3h9a4 4 0 004-4h2a6 6 0 01-6 6H7v3z" fill="currentColor"/>
    </svg>
  );
}

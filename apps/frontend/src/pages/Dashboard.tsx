import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Navbar from "../components/layout/Navbar";
import Page from "../components/layout/Page";
import Card from "../components/ui/Card";
import api from "../lib/api";
import SessionCard from "../components/SessionCard";

type AnyObj = Record<string, any>;

export default function Dashboard() {
  const [items, setItems] = useState<AnyObj[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setErr(null);
    try {
      const res = await api.get("/sessions", { params: { limit: 20 } });
      const list = Array.isArray(res.data) ? res.data : (res.data?.items ?? []);
      setItems(list);
    } catch (e: any) {
      setErr(e?.response?.data?.detail || e.message || "Failed to load sessions");
      setItems([]);
    }
  }

  useEffect(() => { load(); }, []);

  function handleDelete(id: number) {
    setItems((prev) => (prev ? prev.filter((x) => (x.id ?? x.session_id) !== id) : prev));
  }
  function handleRenamed(id: number, title: string) {
    setItems((prev) =>
      prev ? prev.map((x) => ((x.id ?? x.session_id) === id ? { ...x, title } : x)) : prev
    );
  }

  return (
    <>
      <Navbar />
      <Page maxWidth="max-w-6xl">
        <Card>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-xl sm:text-2xl font-semibold">Your Sessions</h1>
              <p className="mt-1 text-sm sm:text-base opacity-80">
                Manage saved roadmaps. Rename, delete, or open any session.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Link to="/generate" className="h-11 rounded-2xl border border-border px-4 inline-flex items-center">
                New plan
              </Link>
            </div>
          </div>
        </Card>

        <div className="mt-4">
          {err && <div className="text-red-600 text-sm">{err}</div>}

          {items === null ? (
            <ul className="space-y-3 sm:space-y-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <li key={i} className="rounded-2xl border border-border bg-bg p-3 sm:p-4 shadow-card animate-pulse">
                  <div className="h-5 w-40 bg-surface rounded mb-2" />
                  <div className="h-3 w-24 bg-surface rounded mb-4" />
                  <div className="h-2 w-full bg-surface rounded" />
                </li>
              ))}
            </ul>
          ) : items.length === 0 ? (
            <Card soft className="text-sm opacity-80">
              No sessions yet. Click <span className="font-medium">New plan</span> to create one.
            </Card>
          ) : (
            <ul className="mt-4 space-y-3 sm:space-y-4">
              {items.map((s) => (
                <SessionCard
                  key={s.id ?? s.session_id}
                  session={s}
                  onDelete={handleDelete}
                  onRenamed={handleRenamed}
                />
              ))}
            </ul>
          )}
        </div>
      </Page>
    </>
  );
}

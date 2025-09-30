import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../lib/api";
import ProgressBar from "./ui/ProgressBar";
import Dialog from "./ui/Dialog";

type AnyObj = Record<string, any>;

export default function SessionCard({
  session,
  onDelete,
  onRenamed,
}: {
  session: AnyObj;
  onDelete: (id: number) => void;
  onRenamed: (id: number, title: string) => void;
}) {
  const navigate = useNavigate();
  const id = session?.id ?? session?.session_id;
  const [pct, setPct] = useState<number | null>(null);

  // Actions state
  const [removing, setRemoving] = useState(false);
  const [renaming, setRenaming] = useState(false);
  const [newTitle, setNewTitle] = useState(session?.title ?? "");
  const [saving, setSaving] = useState(false);

  // Confirm dialog state
  const [confirmOpen, setConfirmOpen] = useState(false);

  useEffect(() => {
    setNewTitle(session?.title ?? "");
  }, [session?.title]);

  // Try use precomputed progress; else fetch
  useEffect(() => {
    const raw = session?.progress_in_percent;
    if (typeof raw === "string" && raw.endsWith("%")) {
      setPct(parseInt(raw));
    } else if (typeof raw === "number") {
      setPct(raw);
    } else if (id != null) {
      (async () => {
        try {
          const pm = await api.get(`/sessions/${id}/progress`, { params: { _ts: Date.now() } });
          const p = pm.data?.progress_in_percent;
          if (typeof p === "string" && p.endsWith("%")) setPct(parseInt(p));
        } catch {}
      })();
    }
  }, [id, session]);

  async function actuallyDelete() {
    if (!id) return;
    setRemoving(true);
    try {
      await api.delete(`/sessions/${id}`);
      onDelete(id);
      setConfirmOpen(false);
    } catch (e: any) {
      alert(e?.response?.data?.detail || e.message || "Failed to delete");
    } finally {
      setRemoving(false);
    }
  }

  async function handleSaveRename(e: React.MouseEvent) {
    e.stopPropagation();
    if (!id) return;
    const title = newTitle.trim();
    if (!title) { setRenaming(false); return; }
    setSaving(true);
    try {
      await api.patch(`/sessions/${id}/title`, { title });
      onRenamed(id, title); // update parent list
      setRenaming(false);
    } catch (e: any) {
      alert(e?.response?.data?.detail || e.message || "Failed to rename");
    } finally {
      setSaving(false);
    }
  }

  function openCard() {
    if (!renaming) navigate(`/sessions/${id}`);
  }

  function keyOpen(e: React.KeyboardEvent) {
    if (renaming) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      navigate(`/sessions/${id}`);
    }
  }

  const title = session?.title || "Untitled session";
  const metaParts: string[] = [];
  if (session?.duration_days) metaParts.push(`${session.duration_days} days`);
  if (session?.preferred_time) metaParts.push(`${session.preferred_time}`);
  const meta = metaParts.join(" · ");

  return (
    <>
      <li
        tabIndex={0}
        onClick={openCard}
        onKeyDown={keyOpen}
        aria-label={`Open session ${title}`}
        className={`group cursor-pointer bg-bg border border-border rounded-2xl p-3 sm:p-4 shadow-card outline-none transition-colors
          hover:bg-primary hover:text-white focus-visible:ring-2 focus-visible:ring-primary/40`}
      >
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          {/* Left: title/meta/progress */}
          <div className="min-w-0">
            {renaming ? (
              <div className="flex flex-col sm:flex-row sm:items-center gap-2" onClick={(e) => e.stopPropagation()}>
                <input
                  autoFocus
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") { e.preventDefault(); (async () => handleSaveRename(e as any))(); }
                    if (e.key === "Escape") setRenaming(false);
                  }}
                  className="flex-1 min-w-0 rounded-xl border border-border px-3 py-2 bg-bg text-content group-hover:text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/40"
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleSaveRename}
                    disabled={saving}
                    className="h-10 px-3 rounded-xl border border-border bg-transparent group-hover:border-white group-hover:text-white"
                  >
                    {saving ? "Saving…" : "Save"}
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); setRenaming(false); }}
                    disabled={saving}
                    className="h-10 px-3 rounded-xl border border-border bg-transparent group-hover:border-white group-hover:text-white"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <>
                <h3 className="text-base sm:text-lg font-semibold truncate group-hover:text-white">{title}</h3>
                {meta && (
                  <div className="mt-1 text-xs sm:text-sm text-muted group-hover:text-white/80">{meta}</div>
                )}
              </>
            )}

            <div className="mt-2">
              <div className="opacity-90 group-hover:text-white/90">
                <ProgressBar value={pct ?? 0} />
              </div>
              <div className="mt-1 text-xs sm:text-sm text-muted group-hover:text-white/80">
                {pct ?? 0}%
              </div>
            </div>
          </div>

          {/* Right: actions (don't navigate) */}
          <div className="flex gap-2 sm:gap-3 w-full sm:w-auto" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={() => setRenaming(true)}
              className="flex-1 sm:flex-none h-11 px-4 rounded-2xl inline-flex items-center justify-center border border-border bg-transparent group-hover:border-white group-hover:text-white"
            >
              Rename
            </button>
            <button
              onClick={() => setConfirmOpen(true)}
              disabled={removing}
              className="flex-1 sm:flex-none h-11 px-4 rounded-2xl inline-flex items-center justify-center border border-border bg-transparent group-hover:border-white group-hover:text-white"
            >
              Delete
            </button>
          </div>
        </div>
      </li>

      {/* Confirm delete dialog */}
      <Dialog
        open={confirmOpen}
        title="Delete session?"
        description={`This will permanently remove “${title}”.`}
        confirmText={removing ? "Deleting…" : "Delete"}
        cancelText="Cancel"
        onConfirm={actuallyDelete}
        onCancel={() => (!removing ? setConfirmOpen(false) : null)}
        busy={removing}
      />
    </>
  );
}

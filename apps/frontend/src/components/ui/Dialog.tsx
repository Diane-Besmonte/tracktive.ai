import { createPortal } from "react-dom";
import { useEffect } from "react";

type Props = {
  open: boolean;
  title?: string;
  description?: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel: () => void;
  busy?: boolean;
};

export default function Dialog({
  open,
  title = "Are you sure?",
  description,
  confirmText = "Confirm",
  cancelText = "Cancel",
  onConfirm,
  onCancel,
  busy = false,
}: Props) {
  // Close on ESC
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCancel();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onCancel]);

  if (!open) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      aria-modal="true"
      role="dialog"
      aria-labelledby="dialog-title"
      onClick={onCancel} // backdrop click
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />

      {/* Panel */}
      <div
        className="relative w-full max-w-sm rounded-2xl bg-bg border border-border shadow-2xl p-4 sm:p-5 animate-in fade-in zoom-in-95"
        onClick={(e) => e.stopPropagation()} // prevent backdrop close
      >
        <h2 id="dialog-title" className="text-lg font-semibold">
          {title}
        </h2>
        {description && <p className="mt-1 text-sm opacity-80">{description}</p>}

        <div className="mt-4 flex items-center gap-2 justify-end">
          <button
            onClick={onCancel}
            disabled={busy}
            className="h-10 px-3 rounded-xl border border-border"
          >
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            disabled={busy}
            className="h-10 px-3 rounded-2xl bg-primary text-white"
          >
            {busy ? "Working…" : confirmText}
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}

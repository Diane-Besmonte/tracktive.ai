export default function ProgressBar({
  value,
  label = "Progress",
}: {
  value: number;
  label?: string;
}) {
  const pct = Math.min(100, Math.max(0, Math.round(Number(value) || 0)));

  return (
    <div
      className="relative h-3 w-full rounded-xl bg-surface border border-border overflow-hidden"
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={pct}
    >
      <div
        className="absolute inset-y-0 left-0 bg-primary transition-[width] duration-300"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

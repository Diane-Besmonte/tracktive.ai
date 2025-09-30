export default function LoadingOverlay({
  show,
  message = "Generating your learning path…",
  submessage = "Hang tight while we assemble resources, videos, and exercises.",
}: {
  show: boolean;
  message?: string;
  submessage?: string;
}) {
  if (!show) return null;

  return (
    <div
      className="fixed inset-0 z-[100] bg-black/20 backdrop-blur-sm p-6 flex items-center justify-center"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <div className="w-full max-w-sm rounded-2xl border border-border bg-bg shadow-card p-6 text-center">
        {/* Spinner */}
        <div
          className="mx-auto h-10 w-10 rounded-full border-2 border-primary border-t-transparent motion-safe:animate-spin"
          aria-hidden="true"
        />
        {/* Copy */}
        <h3 className="mt-4 text-base sm:text-lg font-semibold">{message}</h3>
        <p className="mt-1 text-sm opacity-80">{submessage}</p>

        {/* Subtle pulse dots */}
        <div className="mt-4 flex items-center justify-center gap-1 text-xs opacity-70">
          <span className="inline-block h-1.5 w-1.5 rounded-full bg-primary animate-bounce [animation-delay:-0.2s]" />
          <span className="inline-block h-1.5 w-1.5 rounded-full bg-primary animate-bounce [animation-delay:-0.1s]" />
          <span className="inline-block h-1.5 w-1.5 rounded-full bg-primary animate-bounce" />
        </div>
      </div>
    </div>
  );
}

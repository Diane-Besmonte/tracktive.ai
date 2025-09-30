export function apiErrorMessage(e: any): string {
  const status = e?.response?.status;

  const detail = e?.response?.data?.detail ?? e?.message ?? e?.toString?.();
  if (typeof detail === "string") {
    if (status === 401 && /invalid|credential/i.test(detail)) return "Invalid username or password";
    return detail;
  }

  if (Array.isArray(detail)) {
    const msgs = detail
      .map((d: any) => d?.msg || d?.type || JSON.stringify(d))
      .filter(Boolean);
    if (msgs.length) return msgs.join("\n");
  }

  const fallback = e?.response?.data?.error || e?.response?.data?.message;
  if (typeof fallback === "string") return fallback;

  return status ? `Request failed with status ${status}` : "Network error";
}

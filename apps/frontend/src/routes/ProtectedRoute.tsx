import { useEffect, useState, type ReactNode } from "react";
import { Navigate } from "react-router-dom";
import api from "../lib/api";
import { getToken } from "../lib/storage";

export default function ProtectedRoute({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<"checking" | "ok" | "fail">("checking");

  useEffect(() => {
    if (!getToken()) { setStatus("fail"); return; }
    let mounted = true;
    api.get("/auth/me")
      .then(() => mounted && setStatus("ok"))
      .catch(() => mounted && setStatus("fail"));
    return () => { mounted = false; };
  }, []);

  if (status === "checking") return <div className="p-6 text-center">Loading…</div>;
  if (status === "fail") return <Navigate to="/login" replace />;
  return <>{children}</>;
}

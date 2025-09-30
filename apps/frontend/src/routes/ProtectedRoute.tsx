import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import api from "../lib/api";
import { getToken } from "../lib/storage";

export default function ProtectedRoute({ children }: { children: JSX.Element }) {
  const [status, setStatus] = useState<"checking" | "ok" | "fail">("checking");

  useEffect(() => {
    if (!getToken()) { setStatus("fail"); return; }
    api.get("/auth/me").then(() => setStatus("ok")).catch(() => setStatus("fail"));
  }, []);

  if (status === "checking") return <div className="p-6 text-center">Loading…</div>;
  if (status === "fail") return <Navigate to="/login" replace />;
  return children;
}

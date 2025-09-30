import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Navbar from "../../components/layout/Navbar";
import Page from "../../components/layout/Page";
import Card from "../../components/ui/Card";
import api from "../../lib/api";
import { apiErrorMessage } from "../../lib/err";

export default function Login() {
  const navigate = useNavigate();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      const res = await api.post(
        "/auth/login",
        { username_or_email: identifier, password },
        { headers: { "Content-Type": "application/json; charset=utf-8" } }
      );

      const token = res.data?.access_token || res.data?.token;
      if (!token) throw new Error("No access token returned");

      localStorage.setItem("access_token", token);
      localStorage.setItem("token", token);

      api.defaults.headers.common.Authorization = `Bearer ${token}`;

      navigate("/dashboard", { replace: true });
    } catch (e) {
      setErr(apiErrorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Navbar />
      <Page maxWidth="max-w-md">
        <Card>
          <h1 className="text-xl sm:text-2xl font-semibold">Welcome back</h1>
          <p className="mt-1 text-sm opacity-80">Log in to continue your learning plan.</p>

          <form onSubmit={submit} className="mt-5 space-y-4">
            <div>
              <label className="text-sm font-medium">Username or Email</label>
              <input
                className="mt-1 w-full rounded-xl border border-border bg-bg p-3"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium">Password</label>
              <input
                type="password"
                className="mt-1 w-full rounded-xl border border-border bg-bg p-3"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            {err && <div className="text-sm text-red-600">{err}</div>}

            <button
              type="submit"
              disabled={busy}
              className="w-full h-11 rounded-2xl bg-primary text-white"
            >
              {busy ? "Signing in…" : "Sign in"}
            </button>

            <div className="text-sm opacity-80">
              No account? <Link to="/register" className="underline">Sign up</Link>
            </div>
          </form>
        </Card>
      </Page>
    </>
  );
}

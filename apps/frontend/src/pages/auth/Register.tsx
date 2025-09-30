import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Navbar from "../../components/layout/Navbar";
import Page from "../../components/layout/Page";
import Card from "../../components/ui/Card";
import api from "../../lib/api";
import { apiErrorMessage } from "../../lib/err";

export default function Register() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      await api.post(
        "/auth/register",
        { name, username, email, password },
        { headers: { "Content-Type": "application/json; charset=utf-8" } }
      );

      const res = await api.post(
        "/auth/login",
        { username_or_email: username || email, password },
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
      setBusy(false);
    }
  }

  return (
    <>
      <Navbar />
      <Page maxWidth="max-w-md">
        <Card>
          <h1 className="text-xl sm:text-2xl font-semibold">Create your account</h1>
          <p className="mt-1 text-sm opacity-80">It takes less than a minute.</p>

          <form onSubmit={submit} className="mt-5 space-y-4">
            <div>
              <label className="text-sm font-medium">Name</label>
              <input
                className="mt-1 w-full rounded-xl border border-border bg-bg p-3"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium">Username</label>
              <input
                className="mt-1 w-full rounded-xl border border-border bg-bg p-3"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium">Email</label>
              <input
                type="email"
                className="mt-1 w-full rounded-xl border border-border bg-bg p-3"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
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
              {busy ? "Creating…" : "Create account"}
            </button>

            <div className="text-sm opacity-80">
              Already have an account? <Link to="/login" className="underline">Log in</Link>
            </div>
          </form>
        </Card>
      </Page>
    </>
  );
}

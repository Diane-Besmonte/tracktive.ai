import api from "./api";
import { setToken, clearToken } from "./storage";

export async function registerUser(input: {
  name: string; username: string; email: string; password: string;
}) {
  await api.post("/auth/register", input);
}

export async function loginUser(input: {
  usernameOrEmail: string; password: string;
}) {
  const res = await api.post("/auth/login", {
    username_or_email: input.usernameOrEmail,
    password: input.password,
  });
  const token = res.data?.access_token || res.data?.token;
  if (!token) throw new Error("No access_token in response");
  setToken(token);
  return token;
}

export async function me() {
  return api.get("/auth/me");
}

export async function logoutUser() {
  try { await api.post("/auth/logout"); } catch {}
  clearToken();
}

export function isLoggedIn(): boolean {
  const t = localStorage.getItem("access_token") || localStorage.getItem("token");
  return !!t;
}

import { useEffect, useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { isLoggedIn } from "../../lib/auth";
import api from "../../lib/api";

export default function Navbar() {
  const authed = isLoggedIn();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const [open, setOpen] = useState(false);

  useEffect(() => { setOpen(false); }, [pathname]);

  async function logout() {
    try { await api.post("/auth/logout"); } catch {}
    localStorage.removeItem("access_token");
    localStorage.removeItem("token");
    navigate("/login");
  }

  const desktopNav = authed
    ? [
        { to: "/dashboard", label: "Dashboard" },
        { to: "/generate", label: "Generate" },
        { to: "/login", label: "Logout", onClick: logout, isButton: true },
      ]
    : [
        { to: "/#features", label: "Features" },
        { to: "/login", label: "Log in" },
        { to: "/register", label: "Sign up" },
      ];

  const menuNavLeft = authed
    ? [
        { to: "/", label: "Home" },
        { to: "/dashboard", label: "Dashboard" },
        { to: "/generate", label: "Generate" },
      ]
    : [
        { to: "/", label: "Home" },
        { to: "/#features", label: "Features" },
      ];

  const menuAccount = authed
    ? [{ label: "Logout", onClick: logout, isButton: true }]
    : [
        { to: "/login", label: "Log in" },
        { to: "/register", label: "Sign up" },
      ];

  const linkBase = "px-3 py-2 rounded-md text-sm transition-colors";
  const desktopLink = ({ isActive }: { isActive: boolean }) =>
    [linkBase, isActive ? "text-primary" : "opacity-80 hover:opacity-100"].join(" ");
  const menuItem = "block rounded-xl px-3 py-2 text-sm hover:bg-surface";

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-bg/70 backdrop-blur supports-[backdrop-filter]:bg-bg/60">
      <nav className="mx-auto max-w-5xl px-3 sm:px-4">
        <div className="flex h-14 items-center gap-3">
          <Link to="/" className="font-semibold tracking-tight text-base lg:text-lg">
            Tracktive <span className="opacity-70 text-primary">AI</span>
          </Link>

          <ul className="ml-auto hidden lg:flex items-center gap-1">
            {desktopNav.map((item) =>
              item.isButton ? (
                <li key={item.label} className="relative">
                  <button
                    onClick={item.onClick}
                    className={[linkBase, "opacity-80 hover:opacity-100"].join(" ")}
                  >
                    {item.label}
                  </button>
                </li>
              ) : (
                <li key={item.to} className="relative">
                  <NavLink to={item.to!} className={desktopLink as any}>
                    {item.label}
                  </NavLink>
                  <NavActiveUnderline match={pathname === item.to} />
                </li>
              )
            )}
          </ul>

          <button
            className="ml-auto inline-flex h-9 w-9 items-center justify-center rounded-xl border border-border lg:hidden"
            aria-label="Open menu"
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
            </svg>
          </button>
        </div>
      </nav>

      {open && (
        <>
          <button
            className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm lg:hidden"
            aria-label="Close menu"
            onClick={() => setOpen(false)}
          />
          <div className="fixed inset-x-0 top-14 z-50 px-3 lg:hidden">
            <div className="mx-auto max-w-5xl rounded-2xl border border-border bg-bg shadow-2xl">
              <div className="grid gap-2 p-3 sm:grid-cols-2">
                <div>
                  <div className="px-2 pb-1 text-xs uppercase opacity-60">Navigation</div>
                  <ul>
                    {menuNavLeft.map((l) => (
                      <li key={l.label}>
                        {l.to?.startsWith("/#") ? (
                          <a href={l.to} onClick={() => setOpen(false)} className={menuItem}>
                            {l.label}
                          </a>
                        ) : (
                          <Link to={l.to!} onClick={() => setOpen(false)} className={menuItem}>
                            {l.label}
                          </Link>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <div className="px-2 pb-1 text-xs uppercase opacity-60">Account</div>
                  <div className="p-2 flex flex-col gap-2">
                    {menuAccount.map((a) =>
                      a.isButton ? (
                        <button
                          key={a.label}
                          onClick={async () => { await a.onClick?.(); setOpen(false); }}
                          className="h-11 rounded-2xl bg-primary text-white inline-flex items-center justify-center"
                        >
                          {a.label}
                        </button>
                      ) : (
                        <Link
                          key={a.to}
                          to={a.to!}
                          onClick={() => setOpen(false)}
                          className="h-11 rounded-2xl border border-border inline-flex items-center justify-center"
                        >
                          {a.label}
                        </Link>
                      )
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </header>
  );
}

function NavActiveUnderline({ match }: { match: boolean }) {
  return (
    <span
      aria-hidden
      className={[
        "pointer-events-none absolute -bottom-1 left-2 right-2 h-0.5 rounded-full bg-primary transition-transform duration-200",
        match ? "scale-x-100" : "scale-x-0",
      ].join(" ")}
      style={{ transformOrigin: "left center" }}
    />
  );
}

"use client";

import { useState } from "react";
import { useSession } from "@/context/SessionContext";

export function SignInScreen() {
  const { login } = useSession();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await login(email.trim(), password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in");
      setSaving(false);
    }
  }

  return (
    <div className="app-shell align-items-center justify-content-center p-4">
      <form className="surface-card p-4" style={{ width: "min(420px, 100%)" }} onSubmit={onSubmit}>
        <div className="d-flex align-items-center gap-2 mb-3">
          <span className="brand-mark">P</span>
          <strong>Parasite SEO</strong>
        </div>
        <h1 className="h4 mb-1">Sign in</h1>
        <p className="text-muted small mb-3">Use your workspace email and password.</p>
        {error ? <div className="alert alert-danger py-2">{error}</div> : null}
        <div className="mb-3">
          <label className="form-label" htmlFor="signin-email">
            Email
          </label>
          <input
            id="signin-email"
            className="form-control"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </div>
        <div className="mb-3">
          <label className="form-label" htmlFor="signin-password">
            Password
          </label>
          <input
            id="signin-password"
            className="form-control"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </div>
        <button className="btn btn-accent w-100" type="submit" disabled={saving}>
          {saving ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}

"use client";

import { useState } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap-icons/font/bootstrap-icons.css";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopNav } from "@/components/layout/TopNav";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="app-shell">
      <Sidebar mobileOpen={mobileOpen} onNavigate={() => setMobileOpen(false)} />
      {mobileOpen ? (
        <button
          className="overlay-backdrop d-lg-none"
          aria-label="Close navigation"
          type="button"
          onClick={() => setMobileOpen(false)}
        />
      ) : null}
      <div className="app-main">
        <TopNav onMenu={() => setMobileOpen(true)} />
        <div className="page-wrap">{children}</div>
      </div>
    </div>
  );
}

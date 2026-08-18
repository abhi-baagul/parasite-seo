"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { NAV_ITEMS } from "@/lib/navigation";

const groups = [
  { label: "Overview", items: NAV_ITEMS.slice(0, 2) },
  { label: "Production", items: NAV_ITEMS.slice(2, 12) },
  { label: "Performance", items: NAV_ITEMS.slice(12, 16) },
  { label: "System", items: NAV_ITEMS.slice(16) },
];

export function Sidebar({
  mobileOpen,
  onNavigate,
}: {
  mobileOpen?: boolean;
  onNavigate?: () => void;
}) {
  const pathname = usePathname();

  return (
    <aside className={`sidebar ${mobileOpen ? "mobile-open" : ""}`} aria-label="Primary">
      <Link href="/" className="sidebar-brand" onClick={onNavigate}>
        <span className="brand-mark">P</span>
        <span className="brand-copy">
          <strong>Parasite SEO</strong>
          <span>AI Automation</span>
        </span>
      </Link>
      <nav className="sidebar-nav">
        {groups.map((group) => (
          <div key={group.label}>
            <div className="nav-section-label">{group.label}</div>
            {group.items.map((item) => {
              const active =
                item.href === "/"
                  ? pathname === "/"
                  : item.href === "/parasite-seo"
                    ? pathname === "/parasite-seo" ||
                      (pathname.startsWith("/parasite-seo/") &&
                        !pathname.startsWith("/parasite-seo/campaigns") &&
                        !pathname.startsWith("/parasite-seo/network"))
                    : pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`sidebar-link ${active ? "active" : ""}`}
                  onClick={onNavigate}
                >
                  <i className={`bi ${item.icon}`} aria-hidden="true" />
                  {item.label}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>
    </aside>
  );
}

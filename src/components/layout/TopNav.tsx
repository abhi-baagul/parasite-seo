"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useRef, useState } from "react";
import { useProject } from "@/context/ProjectContext";
import { useSession } from "@/context/SessionContext";
import { formatDateTime } from "@/lib/format";
import { useClickOutside } from "@/components/layout/useClickOutside";

function initials(name: string) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

export function TopNav({ onMenu }: { onMenu: () => void }) {
  const router = useRouter();
  const { projects, selectedId, setSelectedId } = useProject();
  const { user, notifications, unreadCount, markRead, markAllRead, logout } = useSession();
  const [query, setQuery] = useState("");
  const [openSearch, setOpenSearch] = useState(false);
  const [openNotes, setOpenNotes] = useState(false);
  const [openProfile, setOpenProfile] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);
  const notesRef = useRef<HTMLDivElement>(null);
  const profileRef = useRef<HTMLDivElement>(null);

  useClickOutside(searchRef, () => setOpenSearch(false));
  useClickOutside(notesRef, () => setOpenNotes(false));
  useClickOutside(profileRef, () => setOpenProfile(false));

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (q.length < 2) return [];
    return projects
      .filter((item) => item.name.toLowerCase().includes(q) || (item.niche ?? "").toLowerCase().includes(q))
      .map((item) => ({ href: `/projects/${item.id}`, label: item.name, kind: "Project" }))
      .slice(0, 8);
  }, [query, projects]);

  return (
    <header className="topbar">
      <button className="icon-btn d-lg-none" type="button" aria-label="Open navigation" onClick={onMenu}>
        <i className="bi bi-list" />
      </button>

      <label className="visually-hidden" htmlFor="project-select">
        Project
      </label>
      <select
        id="project-select"
        className="form-select"
        style={{ maxWidth: 240 }}
        value={selectedId}
        onChange={(event) => setSelectedId(event.target.value)}
      >
        <option value="all">All projects</option>
        {projects.map((project) => (
          <option key={project.id} value={project.id}>
            {project.name}
          </option>
        ))}
      </select>
      {selectedId !== "all" ? (
        <Link href={`/projects/${selectedId}`} className="btn btn-sm btn-ghost">
          Open project
        </Link>
      ) : null}

      <div className="search-field" style={{ flex: "1 1 220px" }} ref={searchRef}>
        <i className="bi bi-search" />
        <input
          className="form-control"
          placeholder="Search content, URLs, campaigns"
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setOpenSearch(true);
          }}
          onFocus={() => setOpenSearch(true)}
          aria-label="Global search"
        />
        {openSearch && results.length > 0 ? (
          <div className="search-results">
            {results.map((result) => (
              <Link
                key={result.href + result.label}
                href={result.href}
                className="d-block px-3 py-2 border-bottom"
                onClick={() => setOpenSearch(false)}
              >
                <div className="small text-muted">{result.kind}</div>
                <div>{result.label}</div>
              </Link>
            ))}
          </div>
        ) : null}
      </div>

      <div className="ms-auto d-flex align-items-center gap-2">
        <div className="position-relative" ref={notesRef}>
          <button
            className="icon-btn"
            type="button"
            aria-label="Notifications"
            onClick={() => {
              setOpenNotes((open) => !open);
              setOpenProfile(false);
            }}
          >
            <i className="bi bi-bell" />
            {unreadCount > 0 ? (
              <span className="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">
                {unreadCount}
              </span>
            ) : null}
          </button>
          {openNotes ? (
            <div className="menu-panel p-2" role="menu" style={{ minWidth: 320, maxHeight: 420, overflow: "auto" }}>
              <div className="px-2 py-1 d-flex justify-content-between align-items-center">
                <span className="small text-muted">Notifications</span>
                {unreadCount > 0 ? (
                  <button type="button" className="btn btn-sm btn-ghost" onClick={() => void markAllRead()}>
                    Mark all read
                  </button>
                ) : null}
              </div>
              {notifications.length === 0 ? (
                <div className="px-2 py-3 text-muted small">No notifications yet.</div>
              ) : (
                notifications.map((note) => (
                  <button
                    key={note.id}
                    type="button"
                    className="d-block w-100 text-start px-2 py-2 border-bottom border-0 bg-transparent"
                    style={{ opacity: note.read ? 0.65 : 1 }}
                    onClick={() => {
                      void markRead(note.id);
                      setOpenNotes(false);
                      if (note.href) router.push(note.href);
                    }}
                  >
                    <div className="fw-semibold">{note.title}</div>
                    <div className="small text-muted">{note.body}</div>
                    {note.at ? <div className="small text-muted mt-1">{formatDateTime(note.at)}</div> : null}
                  </button>
                ))
              )}
              <Link href="/settings?tab=notifications" className="d-block px-2 py-2" onClick={() => setOpenNotes(false)}>
                Notification settings
              </Link>
            </div>
          ) : null}
        </div>

        <div className="position-relative" ref={profileRef}>
          <button
            className="icon-btn"
            type="button"
            style={{ width: "auto", padding: "0 10px", gap: 8 }}
            onClick={() => {
              setOpenProfile((open) => !open);
              setOpenNotes(false);
            }}
            aria-label="Account menu"
          >
            <span
              className="rounded-circle d-inline-flex align-items-center justify-content-center"
              style={{ width: 26, height: 26, background: "#c45c16", color: "#fff", fontSize: 12 }}
            >
              {initials(user?.name || "U")}
            </span>
            <span className="d-none d-sm-inline">{user?.name ?? "Account"}</span>
            <i className="bi bi-chevron-down small" />
          </button>
          {openProfile ? (
            <div className="menu-panel p-2" style={{ minWidth: 220 }}>
              <div className="px-2 py-2 border-bottom">
                <div className="fw-semibold">{user?.name}</div>
                <div className="small text-muted">{user?.email}</div>
              </div>
              <Link href="/settings" className="d-block px-2 py-2" onClick={() => setOpenProfile(false)}>
                Edit profile
              </Link>
              <Link href="/settings?tab=security" className="d-block px-2 py-2" onClick={() => setOpenProfile(false)}>
                Security
              </Link>
              <button
                type="button"
                className="d-block w-100 text-start px-2 py-2 border-0 bg-transparent"
                onClick={() => {
                  setOpenProfile(false);
                  void logout();
                }}
              >
                Log out
              </button>
            </div>
          ) : null}
        </div>
      </div>
    </header>
  );
}

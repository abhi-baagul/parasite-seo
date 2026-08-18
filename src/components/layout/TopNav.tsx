"use client";

import Link from "next/link";
import { useMemo, useRef, useState } from "react";
import { notifications, userProfile } from "@/data/mock";
import { useProject } from "@/context/ProjectContext";
import { formatDateTime } from "@/lib/format";
import { useClickOutside } from "@/components/layout/useClickOutside";

export function TopNav({ onMenu }: { onMenu: () => void }) {
  const { projects, selectedId, setSelectedId } = useProject();
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

  const unread = notifications.filter((item) => !item.read).length;

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
            {unread > 0 ? (
              <span className="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">
                {unread}
              </span>
            ) : null}
          </button>
          {openNotes ? (
            <div className="menu-panel p-2" role="menu">
              <div className="px-2 py-1 small text-muted">Notifications</div>
              {notifications.map((note) => (
                <div key={note.id} className="px-2 py-2 border-bottom">
                  <div className="fw-semibold">{note.title}</div>
                  <div className="small text-muted">{note.body}</div>
                  <div className="small text-muted mt-1">{formatDateTime(note.at)}</div>
                </div>
              ))}
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
              AR
            </span>
            <span className="d-none d-sm-inline">{userProfile.name}</span>
            <i className="bi bi-chevron-down small" />
          </button>
          {openProfile ? (
            <div className="menu-panel p-2" style={{ minWidth: 220 }}>
              <div className="px-2 py-2 border-bottom">
                <div className="fw-semibold">{userProfile.name}</div>
                <div className="small text-muted">{userProfile.email}</div>
              </div>
              <Link href="/settings" className="d-block px-2 py-2" onClick={() => setOpenProfile(false)}>
                Settings
              </Link>
              <div className="px-2 py-2 text-muted small">Sign out is not enabled in this prototype.</div>
            </div>
          ) : null}
        </div>
      </div>
    </header>
  );
}

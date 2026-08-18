"use client";

import { useMemo, useState } from "react";
import { PageScaffold } from "@/components/layout/PageScaffold";
import { ErrorState, LoadingState } from "@/components/ui/AsyncState";
import { StatCard } from "@/components/ui/StatCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useProject } from "@/context/ProjectContext";
import { useAsyncLoad } from "@/hooks/useAsyncLoad";
import { ApiClientError } from "@/services/api-client";
import {
  getProjectBacklinkReport,
  listProjectBacklinks,
  type CampaignBacklink,
} from "@/services/backlink-campaign-service";

const FILTERS = [
  { id: "all", label: "All" },
  { id: "published", label: "Published" },
  { id: "verified", label: "Verified" },
  { id: "lost", label: "Lost" },
  { id: "broken", label: "Broken" },
];

export function ProjectBacklinksView() {
  const { selectedId, projects } = useProject();
  const projectId = selectedId === "all" ? projects[0]?.id : selectedId;
  const [filter, setFilter] = useState("all");
  const [items, setItems] = useState<CampaignBacklink[]>([]);
  const [stats, setStats] = useState({ total_backlinks: 0, verified: 0, referring_domains: 0 });
  const [report, setReport] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useAsyncLoad(async () => {
    if (!projectId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const [links, summary] = await Promise.all([
        listProjectBacklinks(projectId, filter === "all" ? undefined : { status: filter }),
        getProjectBacklinkReport(projectId),
      ]);
      setItems(links.items);
      setStats({
        total_backlinks: links.total_backlinks,
        verified: links.verified,
        referring_domains: links.referring_domains,
      });
      setReport(summary);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to load backlinks");
    } finally {
      setLoading(false);
    }
  }, [projectId, filter]);

  const visible = useMemo(() => items, [items]);

  return (
    <PageScaffold>
      <div className="surface-card p-4 mb-4">
        <h2 className="section-title mb-1">Project backlinks</h2>
        <p className="text-muted small mb-0">
          Verified means the source page is reachable and contains the target URL. Published is not the same as indexed.
        </p>
      </div>
      <div className="row g-3 mb-4">
        <div className="col-md-4">
          <StatCard label="Link records" value={String(stats.total_backlinks)} icon="bi-link-45deg" />
        </div>
        <div className="col-md-4">
          <StatCard label="Verified" value={String(stats.verified)} icon="bi-shield-check" />
        </div>
        <div className="col-md-4">
          <StatCard label="Referring domains" value={String(stats.referring_domains)} icon="bi-globe" />
        </div>
      </div>
      {report ? (
        <div className="surface-card p-3 mb-4 small">
          Target: <code>{String(report.target || "—")}</code> · SEO score: {String(report.seo_score ?? "—")} · Lost:{" "}
          {String(report.lost ?? 0)}
        </div>
      ) : null}
      <div className="d-flex flex-wrap gap-2 mb-3">
        {FILTERS.map((f) => (
          <button
            key={f.id}
            type="button"
            className={`btn btn-sm ${filter === f.id ? "btn-accent" : "btn-ghost"}`}
            onClick={() => setFilter(f.id)}
          >
            {f.label}
          </button>
        ))}
      </div>
      {loading ? <LoadingState label="Loading backlinks…" /> : null}
      {error ? <ErrorState title="Unable to load" message={error} /> : null}
      {!loading && !error ? (
        <div className="surface-card">
          <div className="table-responsive">
            <table className="table table-clean mb-0">
              <thead>
                <tr>
                  <th>Source domain</th>
                  <th>Source URL</th>
                  <th>Target</th>
                  <th>Anchor</th>
                  <th>Tier</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Last checked</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((b) => (
                  <tr key={b.id}>
                    <td>
                      {b.source_domain}
                      {b.is_mock ? <span className="badge-soft ms-1">MOCK</span> : null}
                      {b.link_kind === "internal" ? <span className="badge-soft ms-1">internal</span> : null}
                    </td>
                    <td className="small">
                      <a href={b.source_url} target="_blank" rel="noreferrer">
                        {b.source_url}
                      </a>
                    </td>
                    <td className="small">
                      <code>{b.target_url}</code>
                    </td>
                    <td>{b.anchor_text}</td>
                    <td>{b.tier}</td>
                    <td>{b.source_type}</td>
                    <td>
                      <StatusBadge value={b.status} />
                    </td>
                    <td className="small">{b.last_checked_at || "—"}</td>
                  </tr>
                ))}
                {visible.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="text-muted">
                      No backlink records for this filter.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </PageScaffold>
  );
}

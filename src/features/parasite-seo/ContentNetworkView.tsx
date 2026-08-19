"use client";

import Link from "next/link";
import { useCallback, useMemo, useState } from "react";
import { PageScaffold } from "@/components/layout/PageScaffold";
import { ErrorState, LoadingState } from "@/components/ui/AsyncState";
import { StatCard } from "@/components/ui/StatCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useProject } from "@/context/ProjectContext";
import { useAsyncLoad } from "@/hooks/useAsyncLoad";
import { ApiClientError } from "@/services/api-client";
import {
  analyzeContentNetwork,
  approveLinkSuggestion,
  createOrphanSuggestion,
  getContentNetwork,
  getLinkSettings,
  getOrphanOpportunities,
  listLinkSuggestions,
  rejectLinkSuggestion,
  removeBrokenLink,
  updateLinkSettings,
  updateLinkSuggestion,
  type LinkSettings,
  type LinkSuggestion,
  type NetworkOverview,
} from "@/services/content-network-service";

type Tab = "overview" | "suggestions" | "orphans" | "broken" | "graph" | "health";

function NetworkGraph({ overview }: { overview: NetworkOverview }) {
  const nodes = overview.nodes.slice(0, 18);
  const width = 720;
  const height = 420;
  const cx = width / 2;
  const cy = height / 2;
  const radius = Math.min(width, height) * 0.36;
  const positions = useMemo(() => {
    return nodes.map((node, i) => {
      const angle = (Math.PI * 2 * i) / Math.max(nodes.length, 1) - Math.PI / 2;
      return {
        ...node,
        x: cx + radius * Math.cos(angle),
        y: cy + radius * Math.sin(angle),
      };
    });
  }, [nodes, cx, cy, radius]);
  const byId = useMemo(() => Object.fromEntries(positions.map((n) => [n.content_id, n])), [positions]);
  const [selectedEdge, setSelectedEdge] = useState<string | null>(null);
  const edge = overview.edges.find((e) => e.id === selectedEdge);

  return (
    <div>
      <svg viewBox={`0 0 ${width} ${height}`} className="network-graph" role="img" aria-label="Content network graph">
        {overview.edges.map((e) => {
          const s = byId[e.source_content_id];
          const t = byId[e.target_content_id];
          if (!s || !t) return null;
          return (
            <line
              key={e.id}
              x1={s.x}
              y1={s.y}
              x2={t.x}
              y2={t.y}
              className={`network-edge${selectedEdge === e.id ? " is-active" : ""}`}
              onClick={() => setSelectedEdge(e.id)}
            />
          );
        })}
        {positions.map((n) => (
          <g key={n.content_id}>
            <circle
              cx={n.x}
              cy={n.y}
              r={n.orphan ? 16 : 14}
              className={`network-node${n.orphan ? " is-orphan" : ""}`}
            />
            <text x={n.x} y={n.y + 28} textAnchor="middle" className="network-label">
              {n.title.length > 22 ? `${n.title.slice(0, 20)}…` : n.title}
            </text>
          </g>
        ))}
      </svg>
      {edge ? (
        <div className="surface-card p-3 mt-3">
          <div className="small text-muted mb-1">Selected internal link</div>
          <div>
            <strong>{byId[edge.source_content_id]?.title}</strong> →{" "}
            <strong>{byId[edge.target_content_id]?.title}</strong>
          </div>
          <div>Anchor: {edge.anchor_text}</div>
          <div>Status: {edge.status}</div>
          <div>
            URL: <code>{edge.target_url}</code>
          </div>
        </div>
      ) : (
        <p className="text-muted small mt-2 mb-0">Click an edge to inspect source, target, and anchor.</p>
      )}
    </div>
  );
}

export function ContentNetworkView() {
  const { selectedId, projects } = useProject();
  const projectId = selectedId === "all" ? projects[0]?.id : selectedId;
  const [tab, setTab] = useState<Tab>("overview");
  const [overview, setOverview] = useState<NetworkOverview | null>(null);
  const [suggestions, setSuggestions] = useState<LinkSuggestion[]>([]);
  const [settings, setSettings] = useState<LinkSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [editId, setEditId] = useState<string | null>(null);
  const [editAnchor, setEditAnchor] = useState("");

  const refresh = useCallback(async () => {
    if (!projectId) {
      setError("Create or select a project first");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [net, sug, set] = await Promise.all([
        getContentNetwork(projectId),
        listLinkSuggestions(projectId),
        getLinkSettings(projectId),
      ]);
      setOverview(net);
      setSuggestions(sug.items);
      setSettings(set);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to load content network");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useAsyncLoad(() => refresh(), [refresh]);

  async function wrap(label: string, fn: () => Promise<void>) {
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      await fn();
      setMessage(label);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  const pending = suggestions.filter((s) => s.status === "suggested");

  return (
    <PageScaffold
      actions={
        <div className="d-flex gap-2">
          <Link href="/parasite-seo" className="btn btn-ghost">
            ← Parasite SEO AI
          </Link>
          <button
            type="button"
            className="btn btn-accent"
            disabled={busy || !projectId}
            onClick={() =>
              void wrap("Network analysis complete", async () => {
                if (!projectId) return;
                await analyzeContentNetwork(projectId, true);
              })
            }
          >
            Analyze network
          </button>
        </div>
      }
    >
      <div className="surface-card p-4 mb-4">
        <h2 className="section-title mb-1">Content network</h2>
        <p className="text-muted mb-2">
          Discover relationships between your published pages and manage same-domain{" "}
          <strong>internal links</strong>. A backlink is a link from another website to yours — these are different.
        </p>
        {settings ? (
          <div className="d-flex flex-wrap align-items-center gap-3">
            <label className="form-check mb-0">
              <input
                className="form-check-input"
                type="checkbox"
                checked={settings.automatic_internal_linking}
                disabled={busy}
                onChange={(e) =>
                  void wrap("Settings updated", async () => {
                    if (!projectId) return;
                    await updateLinkSettings(projectId, {
                      automatic_internal_linking: e.target.checked,
                    });
                  })
                }
              />
              <span className="form-check-label ms-2">Automatic internal linking (off by default)</span>
            </label>
            <label className="small mb-0">
              Min relevance{" "}
              <select
                className="form-select form-select-sm d-inline-block w-auto"
                value={settings.min_relevance_score}
                disabled={busy}
                onChange={(e) =>
                  void wrap("Threshold updated", async () => {
                    if (!projectId) return;
                    await updateLinkSettings(projectId, {
                      min_relevance_score: Number(e.target.value),
                    });
                  })
                }
              >
                {[70, 80, 85, 90].map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            </label>
          </div>
        ) : null}
      </div>

      {message ? <div className="alert alert-success">{message}</div> : null}
      {loading ? <LoadingState label="Loading content network…" /> : null}
      {!loading && error ? (
        <ErrorState title="Unable to load" message={error} onRetry={() => void refresh()} />
      ) : null}

      {!loading && overview ? (
        <>
          <div className="row g-3 mb-4">
            <div className="col-6 col-lg-3">
              <StatCard label="Pages" value={String(overview.total_pages)} icon="bi-file-earmark-text" />
            </div>
            <div className="col-6 col-lg-3">
              <StatCard label="Internal links" value={String(overview.total_internal_links)} icon="bi-diagram-3" />
            </div>
            <div className="col-6 col-lg-3">
              <StatCard label="Orphan pages" value={String(overview.orphan_pages)} icon="bi-exclamation-circle" />
            </div>
            <div className="col-6 col-lg-3">
              <StatCard label="Link health" value={`${overview.link_health_score}/100`} icon="bi-heart-pulse" />
            </div>
          </div>

          <div className="d-flex flex-wrap gap-2 mb-3">
            {(
              [
                ["overview", "Overview"],
                ["suggestions", "Link suggestions"],
                ["orphans", "Orphan pages"],
                ["broken", "Broken links"],
                ["graph", "Graph"],
                ["health", "Health"],
              ] as const
            ).map(([id, label]) => (
              <button
                key={id}
                type="button"
                className={`btn btn-sm ${tab === id ? "btn-accent" : "btn-ghost"}`}
                onClick={() => setTab(id)}
              >
                {label}
              </button>
            ))}
          </div>

          {tab === "overview" ? (
            <div className="surface-card">
              <div className="p-3 border-bottom d-flex justify-content-between">
                <h3 className="section-title mb-0">Pages</h3>
                <span className="text-muted small">
                  Broken: {overview.broken_links} · Pending suggestions: {overview.pending_suggestions}
                </span>
              </div>
              <div className="table-responsive">
                <table className="table table-clean">
                  <thead>
                    <tr>
                      <th>Page</th>
                      <th>Incoming</th>
                      <th>Outgoing</th>
                      <th>SEO</th>
                      <th>Status</th>
                      <th>Orphan</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {overview.nodes.map((node) => (
                      <tr key={node.content_id}>
                        <td>
                          <div>{node.title}</div>
                          <code className="small">/{node.slug}</code>
                        </td>
                        <td>{node.incoming_links}</td>
                        <td>{node.outgoing_links}</td>
                        <td>{node.seo_score ?? "—"}</td>
                        <td>
                          <StatusBadge value={node.link_density === "excessive" ? "warning" : "ready"} />
                        </td>
                        <td>{node.orphan ? "Yes" : "No"}</td>
                        <td>
                          <a className="btn btn-sm btn-ghost" href={node.public_url} target="_blank" rel="noreferrer">
                            Open
                          </a>
                          <Link className="btn btn-sm btn-ghost" href={`/content-studio/${node.content_id}`}>
                            Edit
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : null}

          {tab === "suggestions" ? (
            <div className="surface-card p-3">
              <div className="d-flex justify-content-between align-items-center mb-3">
                <h3 className="section-title mb-0">Link suggestions</h3>
                <button
                  type="button"
                  className="btn btn-sm btn-accent"
                  disabled={busy || !projectId}
                  onClick={() =>
                    void wrap("Suggestions generated", async () => {
                      if (!projectId) return;
                      await analyzeContentNetwork(projectId, true);
                    })
                  }
                >
                  Generate suggestions
                </button>
              </div>
              {pending.length === 0 ? <p className="text-muted">No pending suggestions.</p> : null}
              {pending.map((s) => (
                <div key={s.id} className="border rounded p-3 mb-3">
                  <div className="fw-semibold">
                    {s.source_title} → {s.target_title}
                  </div>
                  <div className="small text-muted mb-2">{s.reason}</div>
                  {editId === s.id ? (
                    <div className="input-group mb-2">
                      <input
                        className="form-control"
                        value={editAnchor}
                        onChange={(e) => setEditAnchor(e.target.value)}
                      />
                      <button
                        type="button"
                        className="btn btn-ghost"
                        onClick={() =>
                          void wrap("Anchor updated", async () => {
                            await updateLinkSuggestion(s.id, { anchor_text: editAnchor });
                            setEditId(null);
                          })
                        }
                      >
                        Save
                      </button>
                    </div>
                  ) : (
                    <div className="mb-2">
                      Anchor: <strong>{s.anchor_text}</strong> · Relevance: {s.relevance_score ?? "—"}% · Confidence:{" "}
                      {s.confidence_score ?? "—"}%
                    </div>
                  )}
                  <div className="d-flex flex-wrap gap-2">
                    <button
                      type="button"
                      className="btn btn-sm btn-accent"
                      disabled={busy}
                      onClick={() =>
                        void wrap("Internal link inserted", async () => {
                          await approveLinkSuggestion(s.id);
                        })
                      }
                    >
                      Accept
                    </button>
                    <button
                      type="button"
                      className="btn btn-sm btn-ghost"
                      disabled={busy}
                      onClick={() =>
                        void wrap("Suggestion rejected", async () => {
                          await rejectLinkSuggestion(s.id);
                        })
                      }
                    >
                      Reject
                    </button>
                    <button
                      type="button"
                      className="btn btn-sm btn-ghost"
                      onClick={() => {
                        setEditId(s.id);
                        setEditAnchor(s.anchor_text);
                      }}
                    >
                      Edit
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : null}

          {tab === "orphans" ? (
            <div className="surface-card p-3">
              <h3 className="section-title">Orphan pages</h3>
              {overview.orphans.length === 0 ? <p className="text-muted">No orphan pages detected.</p> : null}
              {overview.orphans.map((node) => (
                <div key={node.content_id} className="border rounded p-3 mb-3">
                  <div className="fw-semibold">{node.title}</div>
                  <div className="small text-muted mb-2">Incoming links: 0</div>
                  <button
                    type="button"
                    className="btn btn-sm btn-accent"
                    disabled={busy || !projectId}
                    onClick={() =>
                      void wrap("Opportunities created", async () => {
                        if (!projectId) return;
                        const ideas = await getOrphanOpportunities(projectId, node.content_id);
                        for (const idea of ideas.slice(0, 2)) {
                          await createOrphanSuggestion({
                            project_id: projectId,
                            source_content_id: idea.source_content_id,
                            target_content_id: idea.target_content_id,
                            anchor_text: idea.recommended_anchor,
                          });
                        }
                        setTab("suggestions");
                      })
                    }
                  >
                    Find link opportunities
                  </button>
                </div>
              ))}
            </div>
          ) : null}

          {tab === "broken" ? (
            <div className="surface-card p-3">
              <h3 className="section-title">Broken internal links</h3>
              {overview.broken.length === 0 ? <p className="text-muted">No broken internal links.</p> : null}
              {overview.broken.map((link) => (
                <div key={link.id} className="border rounded p-3 mb-3">
                  <div>
                    <strong>{link.source_title}</strong> → <code>{link.target_url}</code>
                  </div>
                  <div className="small text-muted">{link.reason}</div>
                  <button
                    type="button"
                    className="btn btn-sm btn-ghost mt-2"
                    disabled={busy}
                    onClick={() =>
                      void wrap("Broken link removed", async () => {
                        await removeBrokenLink(link.id);
                      })
                    }
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          ) : null}

          {tab === "graph" ? (
            <div className="surface-card p-3">
              <h3 className="section-title">Network graph</h3>
              <NetworkGraph overview={overview} />
            </div>
          ) : null}

          {tab === "health" ? (
            <div className="surface-card p-3">
              <h3 className="section-title">Internal link health</h3>
              <p>
                Score: <strong>{overview.link_health_score}/100</strong>
              </p>
              <ul>
                <li>✓ {overview.total_internal_links} valid internal links</li>
                <li>
                  {overview.orphan_pages === 0 ? "✓" : "⚠"} {overview.orphan_pages} orphan pages
                </li>
                <li>
                  {overview.broken_links === 0 ? "✓" : "⚠"} {overview.broken_links} broken links
                </li>
                <li>
                  Average SEO score: {overview.average_seo_score ?? "—"} (editorial score, not a ranking guarantee)
                </li>
              </ul>
              {overview.anchor_diversity.length ? (
                <>
                  <h4 className="h6">Anchor diversity</h4>
                  <ul>
                    {overview.anchor_diversity.slice(0, 8).map((item) => (
                      <li key={item.target_content_id}>
                        {item.target_title}: {item.unique_anchors}/{item.anchor_count} unique — {item.recommendation}
                      </li>
                    ))}
                  </ul>
                </>
              ) : null}
              <div className="alert alert-secondary small mb-0">
                {overview.terminology.internal_link} {overview.terminology.backlink}
              </div>
            </div>
          ) : null}
        </>
      ) : null}
    </PageScaffold>
  );
}

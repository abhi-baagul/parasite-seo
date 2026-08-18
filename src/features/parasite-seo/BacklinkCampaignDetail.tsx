"use client";

import Link from "next/link";
import { useCallback, useMemo, useState } from "react";
import { PageScaffold } from "@/components/layout/PageScaffold";
import { ErrorState, LoadingState } from "@/components/ui/AsyncState";
import { StatCard } from "@/components/ui/StatCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useAsyncLoad } from "@/hooks/useAsyncLoad";
import { ApiClientError } from "@/services/api-client";
import {
  approveBacklinkCampaign,
  archiveBacklinkCampaign,
  campaignReportUrl,
  duplicateBacklinkCampaign,
  generateCampaignAssets,
  getBacklinkCampaign,
  publishCampaignAssets,
  retryFailedCampaignAssets,
  startBacklinkCampaign,
  updateBacklinkCampaign,
  updateOutreachProspect,
  verifyCampaignBacklinks,
  type BacklinkCampaign,
  type CampaignAsset,
  type CampaignBacklink,
} from "@/services/backlink-campaign-service";

type Tab = "overview" | "network" | "assets" | "backlinks" | "domains" | "outreach" | "logs" | "reports";

function CampaignNetworkGraph({
  campaign,
  onSelect,
}: {
  campaign: BacklinkCampaign;
  onSelect: (asset: CampaignAsset | null, link: CampaignBacklink | null) => void;
}) {
  const graph = campaign.graph;
  const assets = campaign.assets || [];
  const links = campaign.backlinks || [];
  const width = 780;
  const height = 460;

  const positions = useMemo(() => {
    const map = new Map<string, { x: number; y: number }>();
    map.set("target", { x: width / 2, y: 48 });
    const tier1 = assets.filter((a) => a.tier === 1 || a.asset_type === "cloud" || a.asset_type === "pr");
    const tier2 = assets.filter((a) => a.tier === 2);
    tier1.forEach((a, i) => {
      const span = Math.max(tier1.length - 1, 1);
      map.set(a.id, { x: 80 + (i * (width - 160)) / span, y: 180 });
    });
    tier2.forEach((a, i) => {
      const parent = a.parent_asset_id ? map.get(a.parent_asset_id) : null;
      const baseX = parent?.x ?? width / 2;
      const siblings = tier2.filter((x) => x.parent_asset_id === a.parent_asset_id);
      const idx = siblings.findIndex((x) => x.id === a.id);
      const offset = (idx - (siblings.length - 1) / 2) * 70;
      map.set(a.id, { x: baseX + offset, y: 340 });
    });
    return map;
  }, [assets]);

  if (!graph) return <p className="text-muted">No graph yet — generate assets first.</p>;

  return (
    <div>
      <svg viewBox={`0 0 ${width} ${height}`} className="network-graph" role="img" aria-label="Backlink campaign graph">
        {(graph.edges || [])
          .filter((e) => e.kind !== "backlink")
          .map((e, i) => {
            const from = positions.get(e.from);
            const to = positions.get(e.to);
            if (!from || !to) return null;
            return (
              <line
                key={`${e.from}-${e.to}-${i}`}
                x1={from.x}
                y1={from.y}
                x2={to.x}
                y2={to.y}
                className="network-edge"
              />
            );
          })}
        {Array.from(positions.entries()).map(([id, pos]) => {
          const asset = assets.find((a) => a.id === id);
          const label = id === "target" ? "TARGET" : asset?.title || id;
          const link = links.find((l) => l.asset_id === id);
          return (
            <g
              key={id}
              style={{ cursor: "pointer" }}
              onClick={() => onSelect(asset || null, link || null)}
            >
              <circle
                cx={pos.x}
                cy={pos.y}
                r={id === "target" ? 22 : 14}
                className={`network-node${id === "target" ? " is-orphan" : ""}`}
              />
              <text x={pos.x} y={pos.y + 28} textAnchor="middle" className="network-label">
                {(label.length > 24 ? `${label.slice(0, 22)}…` : label)}
              </text>
              {asset ? (
                <text x={pos.x} y={pos.y + 42} textAnchor="middle" className="network-label">
                  {asset.asset_type} · {asset.status}
                </text>
              ) : null}
            </g>
          );
        })}
      </svg>
    </div>
  );
}

export function BacklinkCampaignDetail({ campaignId }: { campaignId: string }) {
  const [campaign, setCampaign] = useState<BacklinkCampaign | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("overview");
  const [busy, setBusy] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState<CampaignAsset | null>(null);
  const [selectedLink, setSelectedLink] = useState<CampaignBacklink | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const c = await getBacklinkCampaign(campaignId);
      setCampaign(c);
      setSelectedIds((c.assets || []).filter((a) => a.status !== "published").map((a) => a.id));
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to load campaign");
    } finally {
      setLoading(false);
    }
  }, [campaignId]);

  useAsyncLoad(() => refresh(), [refresh]);

  const referring = useMemo(() => {
    const map = new Map<string, { domain: string; count: number; verified: number; status: string }>();
    for (const b of campaign?.backlinks || []) {
      const row = map.get(b.source_domain) || {
        domain: b.source_domain,
        count: 0,
        verified: 0,
        status: b.status,
      };
      row.count += 1;
      if (b.status === "verified") row.verified += 1;
      map.set(b.source_domain, row);
    }
    return Array.from(map.values());
  }, [campaign?.backlinks]);

  if (loading) {
    return (
      <PageScaffold>
        <LoadingState label="Loading campaign…" />
      </PageScaffold>
    );
  }
  if (error || !campaign) {
    return (
      <PageScaffold>
        <ErrorState title="Unable to load" message={error || "Not found"} onRetry={() => void refresh()} />
      </PageScaffold>
    );
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "overview", label: "Overview" },
    { id: "network", label: "Network" },
    { id: "assets", label: "Assets" },
    { id: "backlinks", label: "Backlinks" },
    { id: "domains", label: "Referring domains" },
    { id: "outreach", label: "Outreach" },
    { id: "logs", label: "Logs" },
    { id: "reports", label: "Reports" },
  ];

  return (
    <PageScaffold
      actions={
        <div className="d-flex gap-2 flex-wrap">
          <Link href="/parasite-seo/campaigns" className="btn btn-ghost">
            All campaigns
          </Link>
          <Link href={`/parasite-seo/campaigns/${campaign.id}?wizard=1`} className="btn btn-ghost">
            Continue wizard
          </Link>
          <button
            type="button"
            className="btn btn-ghost"
            disabled={busy}
            onClick={() => {
              setBusy(true);
              void duplicateBacklinkCampaign(campaign.id)
                .then((c) => {
                  window.location.href = `/parasite-seo/campaigns/${c.id}`;
                })
                .catch((err) => setError(err instanceof ApiClientError ? err.message : "Duplicate failed"))
                .finally(() => setBusy(false));
            }}
          >
            Duplicate
          </button>
          <button
            type="button"
            className="btn btn-ghost"
            disabled={busy}
            onClick={() => {
              setBusy(true);
              void archiveBacklinkCampaign(campaign.id)
                .then(setCampaign)
                .catch((err) => setError(err instanceof ApiClientError ? err.message : "Archive failed"))
                .finally(() => setBusy(false));
            }}
          >
            Archive
          </button>
          <button
            type="button"
            className="btn btn-ghost"
            disabled={busy}
            onClick={() => {
              setBusy(true);
              void updateBacklinkCampaign(campaign.id, { status: "paused" })
                .then(setCampaign)
                .catch((err) => setError(err instanceof ApiClientError ? err.message : "Pause failed"))
                .finally(() => setBusy(false));
            }}
          >
            Pause
          </button>
        </div>
      }
    >
      <div className="surface-card p-4 mb-4">
        <div className="d-flex justify-content-between flex-wrap gap-2">
          <div>
            <h2 className="section-title mb-1">{campaign.name}</h2>
            <div className="text-muted small">
              Strategy: {campaign.strategy_type.replace(/_/g, " ")} · <StatusBadge value={campaign.status} />
              {campaign.mock_mode ? <span className="badge-soft ms-2">MOCK DATA</span> : null}
            </div>
            <div className="mt-2">
              Target: <code>{campaign.target_url || "Planning only"}</code>
            </div>
          </div>
          <div style={{ minWidth: 180 }}>
            <div className="small text-muted mb-1">Progress {campaign.progress_percent}%</div>
            <div className="progress" style={{ height: 10 }}>
              <div className="progress-bar" style={{ width: `${campaign.progress_percent}%` }} />
            </div>
          </div>
        </div>
        <p className="small text-muted mt-3 mb-0">{campaign.disclosure}</p>
      </div>

      <div className="row g-3 mb-4">
        <div className="col-6 col-lg-2">
          <StatCard label="Assets" value={String(campaign.counts.assets)} icon="bi-files" />
        </div>
        <div className="col-6 col-lg-2">
          <StatCard label="Tier 1" value={String(campaign.counts.tier1)} icon="bi-1-circle" />
        </div>
        <div className="col-6 col-lg-2">
          <StatCard label="Tier 2" value={String(campaign.counts.tier2)} icon="bi-2-circle" />
        </div>
        <div className="col-6 col-lg-2">
          <StatCard label="Verified" value={String(campaign.counts.verified_backlinks)} icon="bi-shield-check" />
        </div>
        <div className="col-6 col-lg-2">
          <StatCard label="Lost" value={String(campaign.counts.lost_backlinks)} icon="bi-x-octagon" />
        </div>
        <div className="col-6 col-lg-2">
          <StatCard label="Ref. domains" value={String(campaign.counts.referring_domains)} icon="bi-globe" />
        </div>
      </div>

      <div className="d-flex gap-2 flex-wrap mb-3">
        <button
          type="button"
          className="btn btn-accent btn-sm"
          disabled={busy}
          onClick={() => {
            setBusy(true);
            void approveBacklinkCampaign(campaign.id)
              .then(setCampaign)
              .catch((err) => setError(err instanceof ApiClientError ? err.message : "Approve failed"))
              .finally(() => setBusy(false));
          }}
        >
          Approve campaign
        </button>
        <button
          type="button"
          className="btn btn-accent btn-sm"
          disabled={busy || !campaign.approved_at}
          onClick={() => {
            setBusy(true);
            void startBacklinkCampaign(campaign.id)
              .then((r) => setCampaign(r.campaign))
              .catch((err) => setError(err instanceof ApiClientError ? err.message : "Start failed"))
              .finally(() => setBusy(false));
          }}
        >
          Start campaign
        </button>
        <button
          type="button"
          className="btn btn-accent btn-sm"
          disabled={busy}
          onClick={() => {
            setBusy(true);
            void generateCampaignAssets(campaign.id)
              .then((r) => setCampaign(r.campaign))
              .catch((err) => setError(err instanceof ApiClientError ? err.message : "Generate failed"))
              .finally(() => setBusy(false));
          }}
        >
          Generate assets
        </button>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          disabled={busy || selectedIds.length === 0}
          onClick={() => {
            if (selectedIds.length > 5 && !window.confirm(`Publish ${selectedIds.length} assets?`)) return;
            setBusy(true);
            void publishCampaignAssets(campaign.id, { asset_ids: selectedIds })
              .then((r) => setCampaign(r.campaign))
              .catch((err) => setError(err instanceof ApiClientError ? err.message : "Publish failed"))
              .finally(() => setBusy(false));
          }}
        >
          Publish selected
        </button>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          disabled={busy}
          onClick={() => {
            setBusy(true);
            void verifyCampaignBacklinks(campaign.id)
              .then((r) => setCampaign(r.campaign))
              .catch((err) => setError(err instanceof ApiClientError ? err.message : "Verify failed"))
              .finally(() => setBusy(false));
          }}
        >
          Verify / recheck
        </button>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          disabled={busy}
          onClick={() => {
            setBusy(true);
            void retryFailedCampaignAssets(campaign.id)
              .then((r) => setCampaign(r.campaign))
              .catch((err) => setError(err instanceof ApiClientError ? err.message : "Retry failed"))
              .finally(() => setBusy(false));
          }}
        >
          Retry failed
        </button>
      </div>

      <div className="d-flex gap-2 flex-wrap mb-3">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            className={`btn btn-sm ${tab === t.id ? "btn-accent" : "btn-ghost"}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "overview" ? (
        <div className="surface-card p-4">
          <h3 className="h5">Link groups</h3>
          {(campaign.link_groups || []).map((g) => (
            <div key={g.id} className="mb-3">
              <div className="d-flex justify-content-between small">
                <span>
                  {g.name} ({g.total}) T{g.tier} · {g.status}
                </span>
                <span>{g.progress}%</span>
              </div>
              <div className="progress" style={{ height: 10 }}>
                <div className="progress-bar" style={{ width: `${g.progress}%` }} />
              </div>
            </div>
          ))}
          <h3 className="h5 mt-4">Campaign progress</h3>
          <pre className="small mb-0" style={{ whiteSpace: "pre-wrap" }}>
            {`Planned assets: ${campaign.blueprint?.tier1 ?? 0} T1 + ${campaign.blueprint?.tier2 ?? 0} T2 + ${campaign.blueprint?.cloud ?? 0} cloud
Generated: ${campaign.counts.assets}
Published: ${campaign.counts.published}
Verified: ${campaign.counts.verified_backlinks}
Lost: ${campaign.counts.lost_backlinks}
Broken: ${campaign.counts.broken_backlinks}
Outreach prospects: ${campaign.counts.outreach}`}
          </pre>
          {(campaign.anchor_distribution || []).length > 0 ? (
            <div className="mt-3">
              <h4 className="h6">Anchor distribution</h4>
              <ul className="mb-0">
                {campaign.anchor_distribution!.map((a) => (
                  <li key={a.anchor}>
                    {a.anchor || "(empty)"} — {a.percent}%
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}

      {tab === "network" ? (
        <div className="surface-card p-4">
          <CampaignNetworkGraph
            campaign={campaign}
            onSelect={(asset, link) => {
              setSelectedAsset(asset);
              setSelectedLink(link);
            }}
          />
          {selectedAsset || selectedLink ? (
            <div className="surface-card p-3 mt-3">
              {selectedAsset ? (
                <>
                  <div className="fw-semibold">{selectedAsset.title}</div>
                  <div>Type: {selectedAsset.asset_type} · Tier {selectedAsset.tier}</div>
                  <div>Status: {selectedAsset.status}</div>
                  <div>
                    Source: <code>{selectedAsset.source_url || "—"}</code>
                  </div>
                  <div>
                    Target: <code>{selectedAsset.target_url}</code>
                  </div>
                  <div>Anchor: {selectedAsset.anchor_text}</div>
                </>
              ) : null}
              {selectedLink ? (
                <div className="mt-2">
                  <div>Backlink status: {selectedLink.status}</div>
                  <div>Last verified: {selectedLink.last_checked_at || "—"}</div>
                </div>
              ) : null}
            </div>
          ) : (
            <p className="text-muted small mt-2 mb-0">Click a node for title, domain, status, and link details.</p>
          )}
        </div>
      ) : null}

      {tab === "assets" ? (
        <div className="surface-card">
          <div className="table-responsive">
            <table className="table table-clean mb-0">
              <thead>
                <tr>
                  <th></th>
                  <th>Title</th>
                  <th>Type</th>
                  <th>Tier</th>
                  <th>Variant</th>
                  <th>Source</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {(campaign.assets || []).map((a) => (
                  <tr key={a.id}>
                    <td>
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(a.id)}
                        onChange={(e) =>
                          setSelectedIds((prev) =>
                            e.target.checked ? [...prev, a.id] : prev.filter((id) => id !== a.id),
                          )
                        }
                      />
                    </td>
                    <td>{a.title}</td>
                    <td>{a.asset_type}</td>
                    <td>{a.tier}</td>
                    <td>{a.variant_angle}</td>
                    <td className="small">
                      {a.source_url ? (
                        <a href={a.source_url} target="_blank" rel="noreferrer">
                          open
                        </a>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td>
                      <StatusBadge value={a.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      {tab === "backlinks" ? (
        <div className="surface-card">
          <div className="table-responsive">
            <table className="table table-clean mb-0">
              <thead>
                <tr>
                  <th>Source</th>
                  <th>Target</th>
                  <th>Anchor</th>
                  <th>Tier</th>
                  <th>Type</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {(campaign.backlinks || []).map((b) => (
                  <tr key={b.id}>
                    <td>
                      <div className="small">{b.source_domain}</div>
                      <a className="small" href={b.source_url} target="_blank" rel="noreferrer">
                        {b.source_url.slice(0, 48)}
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
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      {tab === "domains" ? (
        <div className="surface-card p-4">
          <p className="text-muted small">
            Referring domains count unique hosts — not total link rows. Authority metrics show Not Available unless an
            authorized data provider is connected.
          </p>
          <table className="table table-clean">
            <thead>
              <tr>
                <th>Domain</th>
                <th>Links</th>
                <th>Verified</th>
                <th>Authority</th>
              </tr>
            </thead>
            <tbody>
              {referring.map((r) => (
                <tr key={r.domain}>
                  <td>{r.domain}</td>
                  <td>{r.count}</td>
                  <td>{r.verified}</td>
                  <td>Not Available</td>
                </tr>
              ))}
              {referring.length === 0 ? (
                <tr>
                  <td colSpan={4} className="text-muted">
                    No referring domains yet.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      ) : null}

      {tab === "outreach" ? (
        <div className="surface-card p-4">
          <p className="text-muted small">Drafts only — never auto-send. Explicit approval required before any send.</p>
          <div className="d-flex flex-wrap gap-2 mb-3">
            {["prospect", "qualified", "drafted", "approved", "sent", "replied", "accepted", "rejected", "published", "verified"].map(
              (s) => (
                <span key={s} className="badge text-bg-light">
                  {s}: {(campaign.prospects || []).filter((p) => p.status === s).length}
                </span>
              ),
            )}
          </div>
          <div className="table-responsive">
            <table className="table table-clean">
              <thead>
                <tr>
                  <th>Website</th>
                  <th>Topic</th>
                  <th>Relevance</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {(campaign.prospects || []).map((p) => (
                  <tr key={p.id}>
                    <td>{p.website}</td>
                    <td>{p.topic}</td>
                    <td>{p.relevance_score}</td>
                    <td>
                      <StatusBadge value={p.status} />
                    </td>
                    <td>
                      <button
                        type="button"
                        className="btn btn-sm btn-ghost"
                        onClick={() => {
                          void updateOutreachProspect(p.id, { status: "drafted" }).then(() => refresh());
                        }}
                      >
                        Mark drafted
                      </button>
                      <button
                        type="button"
                        className="btn btn-sm btn-ghost"
                        onClick={() => {
                          if (!window.confirm("Approve this outreach draft? Sending still requires a separate action.")) return;
                          void updateOutreachProspect(p.id, { status: "approved" }).then(() => refresh());
                        }}
                      >
                        Approve draft
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      {tab === "logs" ? (
        <div className="surface-card p-4">
          <h3 className="h6">Campaign log</h3>
          <p className="small text-muted">Secrets are never written to this log.</p>
          <div className="campaign-log">
            {(campaign.logs || []).map((entry) => (
              <div key={entry.id} className={`log-line log-${entry.level}`}>
                <span className="small text-muted">{entry.created_at ? new Date(entry.created_at).toLocaleTimeString() : ""}</span>{" "}
                <strong>{entry.level.toUpperCase()}</strong> {entry.message}
              </div>
            ))}
            {(campaign.logs || []).length === 0 ? <p className="text-muted mb-0">No log entries yet.</p> : null}
          </div>
        </div>
      ) : null}

      {tab === "reports" ? (
        <div className="surface-card p-4">
          <h3 className="h5">Campaign report</h3>
          <pre className="small">{JSON.stringify(campaign.report, null, 2)}</pre>
          <div className="d-flex gap-2">
            {(["json", "csv", "pdf"] as const).map((fmt) => (
              <a key={fmt} className="btn btn-ghost btn-sm" href={campaignReportUrl(campaign.id, fmt)}>
                Export {fmt.toUpperCase()}
              </a>
            ))}
          </div>
        </div>
      ) : null}
    </PageScaffold>
  );
}

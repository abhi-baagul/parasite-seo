"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";
import { PageScaffold } from "@/components/layout/PageScaffold";
import { EmptyStateBlock, ErrorState, LoadingState } from "@/components/ui/AsyncState";
import { StatCard } from "@/components/ui/StatCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useProject } from "@/context/ProjectContext";
import { useAsyncLoad } from "@/hooks/useAsyncLoad";
import { ApiClientError } from "@/services/api-client";
import {
  createDemoBacklinkCampaign,
  listBacklinkCampaigns,
  type BacklinkCampaign,
} from "@/services/backlink-campaign-service";

export function BacklinkCampaignsList() {
  const router = useRouter();
  const { selectedId, projects } = useProject();
  const projectId = selectedId === "all" ? undefined : selectedId;
  const [items, setItems] = useState<BacklinkCampaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setItems(await listBacklinkCampaigns(projectId));
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to load campaigns");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useAsyncLoad(() => refresh(), [refresh]);

  const verified = items.reduce((n, c) => n + (c.counts?.verified_backlinks ?? 0), 0);
  const lost = items.reduce((n, c) => n + (c.counts?.lost_backlinks ?? 0), 0);

  return (
    <PageScaffold
      actions={
        <div className="d-flex gap-2 flex-wrap">
          <Link href="/parasite-seo/campaigns/backlinks" className="btn btn-ghost">
            Project backlinks
          </Link>
          <button
            type="button"
            className="btn btn-ghost"
            disabled={busy}
            onClick={() => {
              const pid = projectId ?? projects[0]?.id;
              if (!pid) {
                setError("Select a project first");
                return;
              }
              setBusy(true);
              void createDemoBacklinkCampaign(pid)
                .then((c) => router.push(`/parasite-seo/campaigns/${c.id}`))
                .catch((err) => setError(err instanceof ApiClientError ? err.message : "Demo failed"))
                .finally(() => setBusy(false));
            }}
          >
            Create demo campaign
          </button>
          <button
            type="button"
            className="btn btn-accent"
            onClick={() => {
              const pid = projectId ?? projects[0]?.id;
              if (!pid) {
                setError("Select a project first");
                return;
              }
              router.push(`/parasite-seo/campaigns/new?project=${pid}`);
            }}
          >
            Create campaign
          </button>
        </div>
      }
    >
      <div className="surface-card p-4 mb-4">
        <h2 className="section-title mb-1">Backlink campaigns</h2>
        <p className="text-muted mb-2">
          Plan authorized Tier 1 / Tier 2 assets, cloud pages, and outreach — then publish, verify, and monitor links.
        </p>
        <p className="small text-muted mb-0">
          Link acquisition and SEO metrics are informational. Search engines independently determine crawling, indexing,
          ranking, and link treatment.
        </p>
      </div>

      <div className="row g-3 mb-4">
        <div className="col-6 col-lg-3">
          <StatCard label="Campaigns" value={String(items.length)} icon="bi-flag" />
        </div>
        <div className="col-6 col-lg-3">
          <StatCard label="Verified backlinks" value={String(verified)} icon="bi-shield-check" />
        </div>
        <div className="col-6 col-lg-3">
          <StatCard label="Lost" value={String(lost)} icon="bi-exclamation-triangle" />
        </div>
        <div className="col-6 col-lg-3">
          <StatCard
            label="Referring domains"
            value={String(items.reduce((n, c) => n + (c.counts?.referring_domains ?? 0), 0))}
            icon="bi-globe2"
          />
        </div>
      </div>

      {loading ? <LoadingState label="Loading campaigns…" /> : null}
      {!loading && error ? <ErrorState title="Unable to load" message={error} onRetry={() => void refresh()} /> : null}
      {!loading && !error && items.length === 0 ? (
        <EmptyStateBlock
          title="No backlink campaigns"
          body="Create a campaign to select a target page, strategy, tiers, and authorized publishing destinations."
        />
      ) : null}

      {!loading && !error && items.length > 0 ? (
        <div className="surface-card">
          <div className="table-responsive">
            <table className="table table-clean mb-0">
              <thead>
                <tr>
                  <th>Campaign</th>
                  <th>Strategy</th>
                  <th>Target</th>
                  <th>Progress</th>
                  <th>Verified</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {items.map((c) => (
                  <tr key={c.id} style={{ cursor: "pointer" }} onClick={() => router.push(`/parasite-seo/campaigns/${c.id}`)}>
                    <td>
                      <strong>{c.name}</strong>
                      <div className="small text-muted">{c.primary_keyword || "—"}</div>
                    </td>
                    <td>{c.strategy_type.replace(/_/g, " ")}</td>
                    <td className="small">
                      <code>{c.target_url || "Planning only"}</code>
                    </td>
                    <td>
                      <div className="progress" style={{ height: 8, minWidth: 80 }}>
                        <div className="progress-bar" style={{ width: `${c.progress_percent}%` }} />
                      </div>
                      <span className="small text-muted">{c.progress_percent}%</span>
                    </td>
                    <td>
                      {c.counts.verified_backlinks}/{c.counts.assets || 0}
                    </td>
                    <td>
                      <StatusBadge value={c.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </PageScaffold>
  );
}

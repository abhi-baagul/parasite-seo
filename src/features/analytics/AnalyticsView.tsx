"use client";

import { useAsyncLoad } from "@/hooks/useAsyncLoad";
import { useCallback, useState } from "react";
import { topContent, trafficTrend } from "@/data/mock";
import { PageScaffold } from "@/components/layout/PageScaffold";
import { EmptyStateBlock, ErrorState, LoadingState } from "@/components/ui/AsyncState";
import { StatCard } from "@/components/ui/StatCard";
import { LineChart } from "@/components/ui/Charts";
import { useProject } from "@/context/ProjectContext";
import { formatNumber } from "@/lib/format";
import { ApiClientError } from "@/services/api-client";
import { getAnalyticsOverview } from "@/services/analytics-service";
import type { AnalyticsOverviewDto } from "@/services/types";

export function AnalyticsView() {
  const { selectedId } = useProject();
  const projectId = selectedId === "all" ? undefined : selectedId;
  const [overview, setOverview] = useState<AnalyticsOverviewDto | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setOverview(await getAnalyticsOverview(projectId));
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to load analytics");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useAsyncLoad(() => refresh(), [refresh]);

  return (
    <PageScaffold>
      <p className="small text-muted mb-3">
        Overview metrics come from PostgreSQL. Trend/top-content charts below remain Phase 1 mock placeholders until
        external analytics lands.
      </p>
      {loading ? <LoadingState label="Loading analytics…" /> : null}
      {!loading && error ? (
        <ErrorState title="Unable to load analytics" message={error} onRetry={() => void refresh()} />
      ) : null}
      {!loading && !error && overview ? (
        <>
          {overview.metric_count === 0 ? (
            <EmptyStateBlock
              title="No analytics metrics stored"
              body="Stored metric rows will appear here. External providers are not connected yet."
            />
          ) : null}
          <div className="row g-3 mb-4">
            <div className="col-6 col-lg">
              <StatCard label="Impressions" value={formatNumber(overview.impressions)} icon="bi-eye" />
            </div>
            <div className="col-6 col-lg">
              <StatCard label="Clicks" value={formatNumber(overview.clicks)} icon="bi-cursor" />
            </div>
            <div className="col-6 col-lg">
              <StatCard label="CTR" value={`${overview.ctr.toFixed(2)}%`} icon="bi-percent" />
            </div>
            <div className="col-6 col-lg">
              <StatCard label="Traffic" value={formatNumber(overview.traffic)} icon="bi-people" />
            </div>
            <div className="col-6 col-lg">
              <StatCard
                label="Average position"
                value={overview.average_position.toFixed(1)}
                icon="bi-graph-up"
              />
            </div>
          </div>
        </>
      ) : null}
      <div className="row g-3">
        <div className="col-lg-5">
          <div className="surface-card p-3 h-100">
            <h2 className="section-title mb-3">Traffic trend (mock)</h2>
            <LineChart
              labels={trafficTrend.map((p) => p.label)}
              values={trafficTrend.map((p) => p.value)}
              label="Sessions"
            />
          </div>
        </div>
        <div className="col-lg-7">
          <div className="surface-card h-100">
            <div className="p-3 border-bottom">
              <h2 className="section-title mb-0">Top content (mock)</h2>
            </div>
            <div className="table-responsive">
              <table className="table table-clean">
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Clicks</th>
                    <th>Impressions</th>
                    <th>CTR</th>
                    <th>Pos</th>
                  </tr>
                </thead>
                <tbody>
                  {topContent.map((row) => (
                    <tr key={row.url}>
                      <td>{row.title}</td>
                      <td>{formatNumber(row.clicks)}</td>
                      <td>{formatNumber(row.impressions)}</td>
                      <td>{row.ctr.toFixed(2)}%</td>
                      <td>{row.position.toFixed(1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </PageScaffold>
  );
}

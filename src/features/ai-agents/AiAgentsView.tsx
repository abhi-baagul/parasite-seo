"use client";

import { useAsyncLoad } from "@/hooks/useAsyncLoad";
import { useCallback, useState } from "react";
import { PageScaffold } from "@/components/layout/PageScaffold";
import { EmptyStateBlock, ErrorState, LoadingState } from "@/components/ui/AsyncState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useProject } from "@/context/ProjectContext";
import { formatCurrency, formatDateTime, formatDuration, formatNumber } from "@/lib/format";
import { ApiClientError } from "@/services/api-client";
import { listAiRuns } from "@/services/ai-service";
import type { AiRunDto } from "@/services/types";

export function AiAgentsView() {
  const { selectedId } = useProject();
  const projectId = selectedId === "all" ? undefined : selectedId;
  const [rows, setRows] = useState<AiRunDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await listAiRuns(projectId);
      setRows(result.items);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to load AI runs");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useAsyncLoad(() => refresh(), [refresh]);

  return (
    <PageScaffold>
      <p className="text-muted small mb-3">
        AI run records from PostgreSQL. Provider execution is not enabled in Phase 2B.
      </p>
      {loading ? <LoadingState label="Loading AI runs…" /> : null}
      {!loading && error ? (
        <ErrorState title="Unable to load AI runs" message={error} onRetry={() => void refresh()} />
      ) : null}
      {!loading && !error && rows.length === 0 ? (
        <EmptyStateBlock title="No AI runs yet" body="Runs will appear when Phase 3 agents start recording activity." />
      ) : null}
      {!loading && !error && rows.length > 0 ? (
        <div className="row g-3">
          {rows.map((run) => (
            <div className="col-md-6 col-xl-4" key={run.id}>
              <div className="surface-card p-3 h-100">
                <div className="d-flex justify-content-between align-items-start mb-2">
                  <h2 className="h6 mb-1">{run.agent_type}</h2>
                  <StatusBadge value={run.status} />
                </div>
                <dl className="row small mb-0">
                  <dt className="col-5">Last run</dt>
                  <dd className="col-7">{formatDateTime(run.created_at)}</dd>
                  <dt className="col-5">Duration</dt>
                  <dd className="col-7">
                    {run.execution_time_ms != null ? formatDuration(run.execution_time_ms) : "—"}
                  </dd>
                  <dt className="col-5">Tokens</dt>
                  <dd className="col-7">{formatNumber(run.total_tokens)}</dd>
                  <dt className="col-5">Cost</dt>
                  <dd className="col-7">{formatCurrency(run.estimated_cost)}</dd>
                  <dt className="col-5">Result</dt>
                  <dd className="col-7">{run.output_summary || run.error_message || "—"}</dd>
                </dl>
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </PageScaffold>
  );
}

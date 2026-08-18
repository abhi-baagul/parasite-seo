"use client";

import { useAsyncLoad } from "@/hooks/useAsyncLoad";
import { useCallback, useState } from "react";
import { PageScaffold } from "@/components/layout/PageScaffold";
import { EmptyStateBlock, ErrorState, LoadingState } from "@/components/ui/AsyncState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useProject } from "@/context/ProjectContext";
import { formatDate } from "@/lib/format";
import { ApiClientError } from "@/services/api-client";
import { listPublishingHistory } from "@/services/publishing-service";
import type { PublishedAssetDto } from "@/services/types";

export function PublishedAssetsView() {
  const { selectedId } = useProject();
  const projectId = selectedId === "all" ? undefined : selectedId;
  const [rows, setRows] = useState<PublishedAssetDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await listPublishingHistory(projectId);
      setRows(result.items);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to load published assets");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useAsyncLoad(() => refresh(), [refresh]);

  return (
    <PageScaffold>
      {loading ? <LoadingState label="Loading published assets…" /> : null}
      {!loading && error ? (
        <ErrorState title="Unable to load published assets" message={error} onRetry={() => void refresh()} />
      ) : null}
      {!loading && !error && rows.length === 0 ? (
        <EmptyStateBlock
          title="No published assets yet"
          body="Published asset records will appear when publishing jobs create history rows."
        />
      ) : null}
      {!loading && !error && rows.length > 0 ? (
        <div className="surface-card">
          <div className="table-responsive">
            <table className="table table-clean">
              <thead>
                <tr>
                  <th>URL</th>
                  <th>Status</th>
                  <th>Published</th>
                  <th>Last checked</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.id}>
                    <td>{row.published_url || "—"}</td>
                    <td>
                      <StatusBadge value={row.status} />
                    </td>
                    <td>{row.published_at ? formatDate(row.published_at) : "—"}</td>
                    <td>{row.last_checked_at ? formatDate(row.last_checked_at) : "—"}</td>
                    <td>
                      {row.published_url ? (
                        <a className="btn btn-sm btn-ghost" href={row.published_url} target="_blank" rel="noreferrer">
                          Open
                        </a>
                      ) : (
                        "—"
                      )}
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

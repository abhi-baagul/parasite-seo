"use client";

import { useAsyncLoad } from "@/hooks/useAsyncLoad";
import Link from "next/link";
import { useCallback, useState } from "react";
import { PageScaffold } from "@/components/layout/PageScaffold";
import { EmptyStateBlock, ErrorState, LoadingState } from "@/components/ui/AsyncState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useProject } from "@/context/ProjectContext";
import { formatDate } from "@/lib/format";
import { ApiClientError } from "@/services/api-client";
import { listAssetLibrary } from "@/services/studio-service";

export function AssetLibraryView() {
  const { selectedId } = useProject();
  const projectId = selectedId === "all" ? undefined : selectedId;
  const [q, setQ] = useState("");
  const [view, setView] = useState<"grid" | "list">("list");
  const [items, setItems] = useState<
    Array<{
      id: string;
      name: string;
      type: string;
      subtype: string;
      status: string;
      href: string;
      url?: string | null;
      updated_at: string | null;
    }>
  >([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await listAssetLibrary(projectId, 1, q || undefined);
      setItems(result.items);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to load assets");
    } finally {
      setLoading(false);
    }
  }, [projectId, q]);

  useAsyncLoad(() => refresh(), [refresh]);

  return (
    <PageScaffold
      actions={
        <div className="d-flex gap-2">
          <button type="button" className={`btn btn-sm ${view === "list" ? "btn-accent" : "btn-ghost"}`} onClick={() => setView("list")}>
            List
          </button>
          <button type="button" className={`btn btn-sm ${view === "grid" ? "btn-accent" : "btn-ghost"}`} onClick={() => setView("grid")}>
            Grid
          </button>
        </div>
      }
    >
      <div className="surface-card p-3 mb-3">
        <div className="row g-2">
          <div className="col-md-8">
            <input
              className="form-control"
              placeholder="Search assets…"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>
          <div className="col-md-4">
            <button type="button" className="btn btn-ghost w-100" onClick={() => void refresh()}>
              Search
            </button>
          </div>
        </div>
      </div>

      {loading ? <LoadingState label="Loading assets…" /> : null}
      {!loading && error ? <ErrorState title="Unable to load assets" message={error} onRetry={() => void refresh()} /> : null}
      {!loading && !error && items.length === 0 ? (
        <EmptyStateBlock title="No assets" body="Content and media for this project will appear here." />
      ) : null}

      {!loading && !error && items.length > 0 && view === "list" ? (
        <div className="surface-card">
          <div className="table-responsive">
            <table className="table table-clean">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Updated</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={`${item.type}-${item.id}`}>
                    <td>
                      <Link href={item.href}>{item.name}</Link>
                    </td>
                    <td>
                      {item.type}/{item.subtype}
                    </td>
                    <td>
                      <StatusBadge value={item.status} />
                    </td>
                    <td>{item.updated_at ? formatDate(item.updated_at) : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      {!loading && !error && items.length > 0 && view === "grid" ? (
        <div className="row g-3">
          {items.map((item) => (
            <div className="col-md-4 col-lg-3" key={`${item.type}-${item.id}`}>
              <Link href={item.href} className="surface-card p-3 d-block h-100">
                <div className="small text-muted text-uppercase mb-1">
                  {item.type} · {item.subtype}
                </div>
                <div className="fw-semibold mb-2">{item.name}</div>
                <StatusBadge value={item.status} />
              </Link>
            </div>
          ))}
        </div>
      ) : null}
    </PageScaffold>
  );
}

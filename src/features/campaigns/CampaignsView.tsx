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
import { createCampaign, listCampaigns } from "@/services/campaign-service";
import type { CampaignDto } from "@/services/types";

export function CampaignsView() {
  const { projects, selectedId, selectedProject, loading: projectsLoading } = useProject();
  const [rows, setRows] = useState<CampaignDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);

  const projectId = selectedId === "all" ? projects[0]?.id : selectedId;

  const refresh = useCallback(async () => {
    if (!projectId) {
      setRows([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await listCampaigns(projectId);
      setRows(result.items);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to load campaigns");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useAsyncLoad(() => refresh(), [refresh]);

  async function onCreate(event: React.FormEvent) {
    event.preventDefault();
    if (!projectId) return;
    setSaving(true);
    try {
      await createCampaign(projectId, {
        name: name.trim(),
        default_content_type: "article",
        default_word_count: 1200,
      });
      setName("");
      await refresh();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to create campaign");
    } finally {
      setSaving(false);
    }
  }

  return (
    <PageScaffold>
      <div className="alert alert-light border mb-3">
        Current project: <strong>{selectedProject?.name ?? projects.find((p) => p.id === projectId)?.name ?? "None"}</strong>
        {selectedId === "all" ? " (using first project for campaign scope)" : null}
      </div>
      <div className="row g-3">
        <div className="col-lg-4">
          <form className="surface-card p-4" onSubmit={onCreate}>
            <h2 className="section-title mb-3">Create campaign</h2>
            <div className="mb-3">
              <label className="form-label" htmlFor="campaign-name">
                Name
              </label>
              <input
                id="campaign-name"
                className="form-control"
                value={name}
                onChange={(event) => setName(event.target.value)}
                required
                disabled={!projectId}
              />
            </div>
            <button className="btn btn-accent" type="submit" disabled={saving || !projectId}>
              {saving ? "Saving…" : "Create campaign"}
            </button>
          </form>
        </div>
        <div className="col-lg-8">
          {projectsLoading || loading ? <LoadingState label="Loading campaigns…" /> : null}
          {!loading && error ? (
            <ErrorState title="Unable to load campaigns" message={error} onRetry={() => void refresh()} />
          ) : null}
          {!loading && !error && !projectId ? (
            <EmptyStateBlock title="No projects yet" body="Create a project before adding campaigns." />
          ) : null}
          {!loading && !error && projectId && rows.length === 0 ? (
            <EmptyStateBlock title="No campaigns yet" body="Create a campaign to group content assets." />
          ) : null}
          {!loading && !error && rows.length > 0 ? (
            <div className="surface-card">
              <div className="table-responsive">
                <table className="table table-clean">
                  <thead>
                    <tr>
                      <th>Campaign</th>
                      <th>Status</th>
                      <th>Type</th>
                      <th>Words</th>
                      <th>Updated</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row) => (
                      <tr key={row.id}>
                        <td>
                          <div className="fw-semibold">{row.name}</div>
                          <div className="small text-muted">{row.description || "—"}</div>
                        </td>
                        <td>
                          <StatusBadge value={row.status} />
                        </td>
                        <td>{row.default_content_type}</td>
                        <td>{row.default_word_count}</td>
                        <td>{formatDate(row.updated_at)}</td>
                        <td className="text-end">
                          <Link className="btn btn-sm btn-accent" href={`/projects/${row.project_id}`}>
                            Open project
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </PageScaffold>
  );
}

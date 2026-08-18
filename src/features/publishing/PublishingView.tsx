"use client";

import { useAsyncLoad } from "@/hooks/useAsyncLoad";
import { useCallback, useState } from "react";
import { PageScaffold } from "@/components/layout/PageScaffold";
import { EmptyStateBlock, ErrorState, LoadingState } from "@/components/ui/AsyncState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useProject } from "@/context/ProjectContext";
import { formatDateTime } from "@/lib/format";
import { ApiClientError } from "@/services/api-client";
import {
  createPublishingChannel,
  listPublishingChannels,
  listPublishingHistory,
} from "@/services/publishing-service";
import type { PublishedAssetDto, PublishingChannelDto } from "@/services/types";

export function PublishingView() {
  const { selectedId, projects } = useProject();
  const projectId = selectedId === "all" ? undefined : selectedId;
  const [channels, setChannels] = useState<PublishingChannelDto[]>([]);
  const [history, setHistory] = useState<PublishedAssetDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [channelPage, historyPage] = await Promise.all([
        listPublishingChannels(projectId),
        listPublishingHistory(projectId),
      ]);
      setChannels(channelPage.items);
      setHistory(historyPage.items);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to load publishing data");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useAsyncLoad(() => refresh(), [refresh]);

  async function onCreate(event: React.FormEvent) {
    event.preventDefault();
    const targetProject = projectId ?? projects[0]?.id;
    if (!targetProject) {
      setError("Create a project before adding publishing channels");
      return;
    }
    try {
      await createPublishingChannel({
        project_id: targetProject,
        name: name.trim(),
        channel_type: "wordpress",
        configuration: { site_url: "https://example.com" },
        is_active: true,
      });
      setName("");
      await refresh();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to create channel");
    }
  }

  return (
    <PageScaffold>
      <form className="surface-card p-3 mb-3" onSubmit={onCreate}>
        <div className="row g-2 align-items-end">
          <div className="col-md-8">
            <label className="form-label" htmlFor="channel-name">
              Channel name
            </label>
            <input
              id="channel-name"
              className="form-control"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          <div className="col-md-4">
            <button className="btn btn-accent w-100" type="submit">
              Add channel
            </button>
          </div>
        </div>
        <p className="small text-muted mb-0 mt-2">
          Channel management only. Actual publishing integrations arrive in a later phase.
        </p>
      </form>

      {loading ? <LoadingState label="Loading publishing…" /> : null}
      {!loading && error ? (
        <ErrorState title="Unable to load publishing" message={error} onRetry={() => void refresh()} />
      ) : null}

      {!loading && !error ? (
        <>
          <h2 className="h6 mb-2">Channels</h2>
          {channels.length === 0 ? (
            <EmptyStateBlock title="No channels yet" body="Add an authorized publishing destination." />
          ) : (
            <div className="row g-3 mb-4">
              {channels.map((channel) => (
                <div className="col-md-4" key={channel.id}>
                  <div className="surface-card p-3 h-100">
                    <div className="d-flex justify-content-between">
                      <h3 className="h6 mb-1">{channel.name}</h3>
                      <StatusBadge value={channel.is_active ? "active" : "inactive"} />
                    </div>
                    <div className="small text-muted">{channel.channel_type}</div>
                    <div className="small mt-2">Updated {formatDateTime(channel.updated_at)}</div>
                  </div>
                </div>
              ))}
            </div>
          )}

          <h2 className="h6 mb-2">Publishing history</h2>
          {history.length === 0 ? (
            <EmptyStateBlock
              title="No published assets yet"
              body="History will appear after publishing jobs create records."
            />
          ) : (
            <div className="surface-card">
              <div className="table-responsive">
                <table className="table table-clean">
                  <thead>
                    <tr>
                      <th>URL</th>
                      <th>Status</th>
                      <th>Published</th>
                      <th>Last checked</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((row) => (
                      <tr key={row.id}>
                        <td>{row.published_url || "—"}</td>
                        <td>
                          <StatusBadge value={row.status} />
                        </td>
                        <td>{row.published_at ? formatDateTime(row.published_at) : "—"}</td>
                        <td>{row.last_checked_at ? formatDateTime(row.last_checked_at) : "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      ) : null}
    </PageScaffold>
  );
}

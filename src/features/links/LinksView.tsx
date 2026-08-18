"use client";

import { useAsyncLoad } from "@/hooks/useAsyncLoad";
import { useCallback, useState } from "react";
import { PageScaffold } from "@/components/layout/PageScaffold";
import { EmptyStateBlock, ErrorState, LoadingState } from "@/components/ui/AsyncState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useProject } from "@/context/ProjectContext";
import { formatDate } from "@/lib/format";
import { ApiClientError } from "@/services/api-client";
import { listContent } from "@/services/content-service";
import { createLink, deleteLink, listLinks, updateLink } from "@/services/link-service";
import type { ContentDto, LinkDto } from "@/services/types";

const attributes = ["standard", "sponsored", "ugc", "nofollow"] as const;

export function LinksView() {
  const { selectedId } = useProject();
  const projectId = selectedId === "all" ? undefined : selectedId;
  const [rows, setRows] = useState<LinkDto[]>([]);
  const [contentOptions, setContentOptions] = useState<ContentDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState({
    content_asset_id: "",
    target_url: "",
    anchor_text: "",
    placement_description: "In-body paragraph",
    link_attribute: "standard",
  });

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [links, content] = await Promise.all([listLinks({ projectId }), listContent(projectId)]);
      setRows(links.items);
      setContentOptions(content.items);
      setDraft((current) => ({
        ...current,
        content_asset_id: current.content_asset_id || content.items[0]?.id || "",
      }));
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to load links");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useAsyncLoad(() => refresh(), [refresh]);

  async function onCreate(event: React.FormEvent) {
    event.preventDefault();
    try {
      await createLink({
        content_asset_id: draft.content_asset_id,
        target_url: draft.target_url,
        anchor_text: draft.anchor_text,
        placement_description: draft.placement_description,
        link_attribute: draft.link_attribute,
      });
      setDraft((current) => ({ ...current, target_url: "", anchor_text: "" }));
      await refresh();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to create link");
    }
  }

  return (
    <PageScaffold>
      <div className="row g-3">
        <div className="col-xl-4">
          <form className="surface-card p-4" onSubmit={onCreate}>
            <h2 className="section-title mb-3">Add authorized link</h2>
            <p className="small text-muted">
              Links are planned for content you own. Mass arbitrary link creation is not supported.
            </p>
            <div className="mb-3">
              <label className="form-label" htmlFor="source">
                Source content
              </label>
              <select
                id="source"
                className="form-select"
                value={draft.content_asset_id}
                onChange={(e) => setDraft({ ...draft, content_asset_id: e.target.value })}
                required
              >
                {contentOptions.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.title}
                  </option>
                ))}
              </select>
            </div>
            <div className="mb-3">
              <label className="form-label" htmlFor="target">
                Target URL
              </label>
              <input
                id="target"
                className="form-control"
                required
                value={draft.target_url}
                onChange={(e) => setDraft({ ...draft, target_url: e.target.value })}
              />
            </div>
            <div className="mb-3">
              <label className="form-label" htmlFor="anchor">
                Anchor text
              </label>
              <input
                id="anchor"
                className="form-control"
                required
                value={draft.anchor_text}
                onChange={(e) => setDraft({ ...draft, anchor_text: e.target.value })}
              />
            </div>
            <div className="mb-3">
              <label className="form-label" htmlFor="attr">
                Link attribute
              </label>
              <select
                id="attr"
                className="form-select"
                value={draft.link_attribute}
                onChange={(e) => setDraft({ ...draft, link_attribute: e.target.value })}
              >
                {attributes.map((attr) => (
                  <option key={attr} value={attr}>
                    {attr}
                  </option>
                ))}
              </select>
            </div>
            <button className="btn btn-accent" type="submit" disabled={!draft.content_asset_id}>
              Save link plan
            </button>
          </form>
        </div>
        <div className="col-xl-8">
          {loading ? <LoadingState label="Loading links…" /> : null}
          {!loading && error ? (
            <ErrorState title="Unable to load links" message={error} onRetry={() => void refresh()} />
          ) : null}
          {!loading && !error && rows.length === 0 ? (
            <EmptyStateBlock title="No links yet" body="Create an authorized link for content you control." />
          ) : null}
          {!loading && !error && rows.length > 0 ? (
            <div className="surface-card">
              <div className="table-responsive">
                <table className="table table-clean">
                  <thead>
                    <tr>
                      <th>Target URL</th>
                      <th>Anchor</th>
                      <th>Attribute</th>
                      <th>Status</th>
                      <th>Created</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row) => (
                      <tr key={row.id}>
                        <td className="small">{row.target_url}</td>
                        <td>{row.anchor_text}</td>
                        <td>
                          <StatusBadge value={row.link_attribute} />
                        </td>
                        <td>
                          <StatusBadge value={row.status} />
                        </td>
                        <td>{formatDate(row.created_at)}</td>
                        <td className="text-nowrap">
                          <button
                            type="button"
                            className="btn btn-sm btn-ghost me-1"
                            onClick={() =>
                              void updateLink(row.id, {
                                status: row.status === "planned" ? "inserted" : "planned",
                              }).then(refresh)
                            }
                          >
                            Toggle
                          </button>
                          <button
                            type="button"
                            className="btn btn-sm btn-ghost"
                            onClick={() => void deleteLink(row.id).then(refresh)}
                          >
                            Delete
                          </button>
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

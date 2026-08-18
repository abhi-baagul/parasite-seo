"use client";

import { useAsyncLoad } from "@/hooks/useAsyncLoad";
import Link from "next/link";
import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { PageScaffold } from "@/components/layout/PageScaffold";
import { EmptyStateBlock, ErrorState, LoadingState } from "@/components/ui/AsyncState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useProject } from "@/context/ProjectContext";
import { formatDate } from "@/lib/format";
import { ApiClientError } from "@/services/api-client";
import { createContent, listContent } from "@/services/content-service";
import type { ContentDto } from "@/services/types";

function slugify(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "")
    .slice(0, 80);
}

export function ContentStudioList() {
  const router = useRouter();
  const { selectedId, projects } = useProject();
  const projectId = selectedId === "all" ? undefined : selectedId;
  const [rows, setRows] = useState<ContentDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [saving, setSaving] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await listContent(projectId, 1, 50, {
        q: query || undefined,
        status: status || undefined,
      });
      setRows(result.items);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to load content");
    } finally {
      setLoading(false);
    }
  }, [projectId, query, status]);

  useAsyncLoad(() => refresh(), [refresh]);

  async function onCreate(event: React.FormEvent) {
    event.preventDefault();
    const targetProject = projectId ?? projects[0]?.id;
    if (!targetProject) {
      setError("Create a project before adding content");
      return;
    }
    setSaving(true);
    try {
      const created = await createContent({
        project_id: targetProject,
        title: title.trim(),
        slug: `${slugify(title)}-${Date.now().toString(36)}`,
        content: "<p></p>",
        content_type: "article",
        status: "draft",
      });
      setTitle("");
      router.push(`/content-studio/${created.id}`);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to create content");
      setSaving(false);
    }
  }

  return (
    <PageScaffold
      actions={
        <form className="d-flex gap-2" onSubmit={onCreate}>
          <input
            className="form-control form-control-sm"
            placeholder="New article title"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            required
          />
          <button className="btn btn-sm btn-accent" type="submit" disabled={saving}>
            New draft
          </button>
        </form>
      }
    >
      <div className="surface-card p-3 mb-3">
        <div className="row g-2 align-items-end">
          <div className="col-md-6">
            <label className="form-label" htmlFor="content-search">
              Search
            </label>
            <input
              id="content-search"
              className="form-control"
              placeholder="Title, slug, keyword…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <div className="col-md-3">
            <label className="form-label" htmlFor="content-status">
              Status
            </label>
            <select id="content-status" className="form-select" value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="">All</option>
              <option value="draft">Draft</option>
              <option value="review">Review</option>
              <option value="approved">Approved</option>
              <option value="archived">Archived</option>
              <option value="failed">Failed</option>
            </select>
          </div>
          <div className="col-md-3">
            <button type="button" className="btn btn-ghost w-100" onClick={() => void refresh()}>
              Apply filters
            </button>
          </div>
        </div>
      </div>

      {loading ? <LoadingState label="Loading content…" /> : null}
      {!loading && error ? (
        <ErrorState title="Unable to load content" message={error} onRetry={() => void refresh()} />
      ) : null}
      {!loading && !error && rows.length === 0 ? (
        <EmptyStateBlock title="No content yet" body="Create a draft to start editing in Content Studio." />
      ) : null}
      {!loading && !error && rows.length > 0 ? (
        <div className="surface-card">
          <div className="table-responsive">
            <table className="table table-clean">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Status</th>
                  <th>SEO</th>
                  <th>Updated</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.id}>
                    <td>
                      <Link href={`/content-studio/${row.id}`}>{row.title}</Link>
                      <div className="small text-muted">
                        {row.word_count} words · {row.content_type}
                      </div>
                    </td>
                    <td>
                      <StatusBadge value={row.status} />
                    </td>
                    <td>{row.seo_score ?? "—"}</td>
                    <td>{formatDate(row.updated_at)}</td>
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

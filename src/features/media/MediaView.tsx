"use client";

import { useAsyncLoad } from "@/hooks/useAsyncLoad";
import { useCallback, useState } from "react";
import { PageScaffold } from "@/components/layout/PageScaffold";
import { EmptyStateBlock, ErrorState, LoadingState } from "@/components/ui/AsyncState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useProject } from "@/context/ProjectContext";
import { formatDate, labelize } from "@/lib/format";
import { ApiClientError } from "@/services/api-client";
import { createMedia, listMedia } from "@/services/media-service";
import type { MediaDto } from "@/services/types";

export function MediaView() {
  const { selectedId, projects } = useProject();
  const projectId = selectedId === "all" ? undefined : selectedId;
  const [rows, setRows] = useState<MediaDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [titlePrompt, setTitlePrompt] = useState("");
  const [altText, setAltText] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await listMedia(projectId, 1, {
        mediaType: typeFilter === "all" ? undefined : typeFilter,
      });
      setRows(result.items);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to load media");
    } finally {
      setLoading(false);
    }
  }, [projectId, typeFilter]);

  useAsyncLoad(() => refresh(), [refresh]);

  async function onCreate(event: React.FormEvent) {
    event.preventDefault();
    const targetProject = projectId ?? projects[0]?.id;
    if (!targetProject) {
      setError("Create a project before adding media metadata");
      return;
    }
    try {
      await createMedia({
        project_id: targetProject,
        media_type: "generated_image",
        prompt: titlePrompt,
        alt_text: altText,
        status: "draft",
      });
      setTitlePrompt("");
      setAltText("");
      await refresh();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to create media record");
    }
  }

  return (
    <PageScaffold>
      <form className="surface-card p-3 mb-3" onSubmit={onCreate}>
        <div className="row g-2 align-items-end">
          <div className="col-md-5">
            <label className="form-label" htmlFor="media-prompt">
              Image prompt / title
            </label>
            <input
              id="media-prompt"
              className="form-control"
              value={titlePrompt}
              onChange={(e) => setTitlePrompt(e.target.value)}
              required
            />
          </div>
          <div className="col-md-5">
            <label className="form-label" htmlFor="media-alt">
              Alt text
            </label>
            <input
              id="media-alt"
              className="form-control"
              value={altText}
              onChange={(e) => setAltText(e.target.value)}
              required
            />
          </div>
          <div className="col-md-2">
            <button className="btn btn-accent w-100" type="submit">
              Add metadata
            </button>
          </div>
        </div>
        <p className="small text-muted mb-0 mt-2">
          Media library metadata for Phase 4. Image binary generation lands later.
        </p>
      </form>

      <div className="d-flex flex-wrap gap-2 mb-3">
        {["all", "image", "video", "diagram", "infographic", "generated_image", "video_embed"].map((type) => (
          <button
            key={type}
            type="button"
            className={`btn btn-sm ${typeFilter === type ? "btn-accent" : "btn-ghost"}`}
            onClick={() => setTypeFilter(type)}
          >
            {type}
          </button>
        ))}
      </div>

      {loading ? <LoadingState label="Loading media…" /> : null}
      {!loading && error ? (
        <ErrorState title="Unable to load media" message={error} onRetry={() => void refresh()} />
      ) : null}
      {!loading && !error && rows.length === 0 ? (
        <EmptyStateBlock title="No media yet" body="Add media metadata records for future generation." />
      ) : null}
      {!loading && !error && rows.length > 0 ? (
        <div className="row g-3">
          {rows.map((item) => (
            <div className="col-md-6 col-xl-4" key={item.id}>
              <div className="surface-card p-3 h-100">
                <div className="media-thumb mb-3">
                  <i className={`bi ${item.media_type === "video_embed" ? "bi-play-btn" : "bi-image"} fs-2`} />
                </div>
                <div className="d-flex justify-content-between align-items-start gap-2">
                  <h2 className="h6 mb-1">{item.prompt || item.alt_text || "Untitled media"}</h2>
                  <StatusBadge value={item.media_type} />
                </div>
                <dl className="small mb-0">
                  <dt>Alt text</dt>
                  <dd>{item.alt_text || "—"}</dd>
                  <dt>Caption</dt>
                  <dd>{item.caption || "—"}</dd>
                  <dt>Source / license</dt>
                  <dd>
                    {item.source || "—"} · {item.license_information || "—"}
                  </dd>
                  <dt>Status</dt>
                  <dd>{labelize(item.status)}</dd>
                  <dt>Created</dt>
                  <dd>{formatDate(item.created_at)}</dd>
                </dl>
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </PageScaffold>
  );
}

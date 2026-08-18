"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";
import { useAsyncLoad } from "@/hooks/useAsyncLoad";
import { PageScaffold } from "@/components/layout/PageScaffold";
import { EmptyStateBlock, ErrorState, LoadingState } from "@/components/ui/AsyncState";
import { StatCard } from "@/components/ui/StatCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useProject } from "@/context/ProjectContext";
import { formatDate } from "@/lib/format";
import { ApiClientError } from "@/services/api-client";
import {
  archiveWebPage,
  listParasiteJobs,
  listPublicPages,
  unpublishWebPage,
  type ParasiteJob,
  type WebPageSummary,
} from "@/services/parasite-seo-service";

export function ParasiteSeoHub() {
  const router = useRouter();
  const { selectedId, projects } = useProject();
  const projectId = selectedId === "all" ? undefined : selectedId;
  const [items, setItems] = useState<ParasiteJob[]>([]);
  const [pages, setPages] = useState<WebPageSummary[]>([]);
  const [stats, setStats] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [jobsData, pagesData] = await Promise.all([
        listParasiteJobs(projectId),
        listPublicPages(projectId),
      ]);
      setItems(jobsData.items);
      setStats(jobsData.stats);
      setPages(pagesData.items);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to load Parasite SEO AI");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useAsyncLoad(() => refresh(), [refresh]);

  return (
    <PageScaffold
      actions={
        <div className="d-flex gap-2">
          <Link href="/parasite-seo/campaigns" className="btn btn-ghost">
            Backlink campaigns
          </Link>
          <Link href="/parasite-seo/network" className="btn btn-ghost">
            Content network
          </Link>
          <button
            type="button"
            className="btn btn-accent"
            onClick={() => {
              const pid = projectId ?? projects[0]?.id;
              if (!pid) {
                setError("Create a project first");
                return;
              }
              router.push(`/parasite-seo/new?project=${pid}`);
            }}
          >
            New generation
          </button>
        </div>
      }
    >
      <div className="surface-card p-4 mb-4">
        <h2 className="section-title mb-1">Parasite SEO AI</h2>
        <p className="text-muted mb-0">
          Create AI-powered web content, optimize it for SEO, add media and contextual links, and generate a public
          web page.
        </p>
      </div>

      <div className="row g-3 mb-4">
        <div className="col-md-4">
          <Link href="/parasite-seo/campaigns" className="surface-card p-4 d-block text-decoration-none h-100">
            <div className="text-muted small mb-1">
              <i className="bi bi-diagram-3 me-1" /> Phase 8
            </div>
            <h3 className="h5 mb-1">Backlink campaigns</h3>
            <p className="text-muted small mb-0">
              Select a target page, build Tier 1 / Tier 2 / cloud assets on authorized destinations, verify links.
            </p>
          </Link>
        </div>
        <div className="col-md-4">
          <Link href="/parasite-seo/network" className="surface-card p-4 d-block text-decoration-none h-100">
            <div className="text-muted small mb-1">
              <i className="bi bi-share me-1" /> Phase 7
            </div>
            <h3 className="h5 mb-1">Content network</h3>
            <p className="text-muted small mb-0">Internal links between your published public pages.</p>
          </Link>
        </div>
        <div className="col-md-4">
          <button
            type="button"
            className="surface-card p-4 d-block text-start w-100 border-0 h-100"
            onClick={() => {
              const pid = projectId ?? projects[0]?.id;
              if (!pid) {
                setError("Create a project first");
                return;
              }
              router.push(`/parasite-seo/new?project=${pid}`);
            }}
          >
            <div className="text-muted small mb-1">
              <i className="bi bi-stars me-1" /> Create
            </div>
            <h3 className="h5 mb-1">New generation</h3>
            <p className="text-muted small mb-0">Prompt → content → SEO → public page.</p>
          </button>
        </div>
      </div>

      {message ? <div className="alert alert-success">{message}</div> : null}

      <div className="row g-3 mb-4">
        <div className="col-6 col-lg-3">
          <StatCard label="Total generated" value={String(stats.total_generated_pages ?? 0)} icon="bi-stars" />
        </div>
        <div className="col-6 col-lg-3">
          <StatCard label="Published pages" value={String(stats.published_pages ?? 0)} icon="bi-globe2" />
        </div>
        <div className="col-6 col-lg-3">
          <StatCard label="Drafts" value={String(stats.draft_pages ?? 0)} icon="bi-file-earmark" />
        </div>
        <div className="col-6 col-lg-3">
          <StatCard label="Avg SEO score" value={String(stats.average_seo_score ?? 0)} icon="bi-speedometer2" />
        </div>
      </div>

      {loading ? <LoadingState label="Loading generations…" /> : null}
      {!loading && error ? (
        <ErrorState title="Unable to load" message={error} onRetry={() => void refresh()} />
      ) : null}
      {!loading && !error && items.length === 0 ? (
        <EmptyStateBlock
          title="No generations yet"
          body="Start with a single natural-language prompt to create a full public article page."
        />
      ) : null}

      {!loading && !error && items.length > 0 ? (
        <div className="surface-card mb-4">
          <div className="p-3 border-bottom">
            <h2 className="section-title mb-0">Recent generations</h2>
          </div>
          <div className="table-responsive">
            <table className="table table-clean">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>SEO</th>
                  <th>Status</th>
                  <th>Public URL</th>
                  <th>Created</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {items.map((job) => (
                  <tr key={job.id}>
                    <td>
                      <Link href={`/parasite-seo/${job.id}`}>
                        {job.content?.title || "Untitled generation"}
                      </Link>
                      <div className="small text-muted text-truncate" style={{ maxWidth: 360 }}>
                        {job.original_prompt.slice(0, 120)}
                      </div>
                    </td>
                    <td>{job.content?.seo_score ?? "—"}</td>
                    <td>
                      <StatusBadge value={job.status} />
                    </td>
                    <td>
                      {job.is_public && job.public_url ? (
                        <a href={job.public_url} target="_blank" rel="noreferrer">
                          Open page
                        </a>
                      ) : (
                        <span className="text-muted">—</span>
                      )}
                    </td>
                    <td>{job.created_at ? formatDate(job.created_at) : "—"}</td>
                    <td className="text-end">
                      <div className="d-flex flex-wrap gap-2 justify-content-end">
                        <Link className="btn btn-sm btn-accent" href={`/parasite-seo/${job.id}`}>
                          Open
                        </Link>
                        {job.content_id ? (
                          <Link className="btn btn-sm btn-ghost" href={`/content-studio/${job.content_id}`}>
                            Studio
                          </Link>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      {!loading && !error && pages.length > 0 ? (
        <div className="surface-card">
          <div className="p-3 border-bottom">
            <h2 className="section-title mb-0">Public pages</h2>
          </div>
          <div className="table-responsive">
            <table className="table table-clean">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>SEO</th>
                  <th>Status</th>
                  <th>Slug</th>
                  <th>Published</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {pages.map((page) => (
                  <tr key={page.id}>
                    <td>
                      <Link href={`/parasite-seo/${page.job_id}`}>{page.title}</Link>
                    </td>
                    <td>{page.seo_score ?? "—"}</td>
                    <td>
                      <StatusBadge value={page.status} />
                    </td>
                    <td>
                      <code>/p/{page.slug}</code>
                    </td>
                    <td>{page.published_at ? formatDate(page.published_at) : "—"}</td>
                    <td>
                      <div className="d-flex flex-wrap gap-2">
                        {page.status === "published" && page.public_url ? (
                          <a className="btn btn-sm btn-ghost" href={page.public_url} target="_blank" rel="noreferrer">
                            Open
                          </a>
                        ) : null}
                        <Link className="btn btn-sm btn-ghost" href={`/parasite-seo/${page.job_id}`}>
                          Edit
                        </Link>
                        {page.public_url ? (
                          <button
                            type="button"
                            className="btn btn-sm btn-ghost"
                            onClick={() => {
                              void navigator.clipboard.writeText(page.public_url!);
                              setMessage("URL copied.");
                            }}
                          >
                            Copy URL
                          </button>
                        ) : null}
                        {page.status === "published" ? (
                          <button
                            type="button"
                            className="btn btn-sm btn-ghost"
                            onClick={() =>
                              void (async () => {
                                await unpublishWebPage(page.job_id);
                                setMessage("Page unpublished");
                                await refresh();
                              })()
                            }
                          >
                            Unpublish
                          </button>
                        ) : null}
                        {page.status !== "archived" ? (
                          <button
                            type="button"
                            className="btn btn-sm btn-ghost"
                            onClick={() =>
                              void (async () => {
                                if (!window.confirm("Archive this public page?")) return;
                                await archiveWebPage(page.job_id);
                                setMessage("Page archived");
                                await refresh();
                              })()
                            }
                          >
                            Archive
                          </button>
                        ) : null}
                      </div>
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

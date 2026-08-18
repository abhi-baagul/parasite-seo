"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";
import { PageScaffold } from "@/components/layout/PageScaffold";
import { EmptyStateBlock, ErrorState, LoadingState } from "@/components/ui/AsyncState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useProject } from "@/context/ProjectContext";
import { useAsyncLoad } from "@/hooks/useAsyncLoad";
import { formatDate } from "@/lib/format";
import { ApiClientError } from "@/services/api-client";
import { listCampaigns } from "@/services/campaign-service";
import { listContent } from "@/services/content-service";
import { listParasiteJobs, type ParasiteJob } from "@/services/parasite-seo-service";
import { deleteProject, getProject, updateProject } from "@/services/project-service";
import type { CampaignDto, ContentDto, ProjectDto } from "@/services/types";

export function ProjectDetailView({ id }: { id: string }) {
  const router = useRouter();
  const { setSelectedId, refreshProjects } = useProject();
  const [project, setProject] = useState<ProjectDto | null>(null);
  const [content, setContent] = useState<ContentDto[]>([]);
  const [jobs, setJobs] = useState<ParasiteJob[]>([]);
  const [campaigns, setCampaigns] = useState<CampaignDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({
    name: "",
    niche: "",
    country: "",
    language: "",
    description: "",
    target_audience: "",
    monetization_model: "",
    status: "active",
  });

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [nextProject, contentResult, jobsResult, campaignResult] = await Promise.all([
        getProject(id),
        listContent(id, 1, 50),
        listParasiteJobs(id),
        listCampaigns(id),
      ]);
      setProject(nextProject);
      setSelectedId(nextProject.id);
      setContent(contentResult.items);
      setJobs(jobsResult.items);
      setCampaigns(campaignResult.items);
      setForm({
        name: nextProject.name,
        niche: nextProject.niche ?? "",
        country: nextProject.country ?? "",
        language: nextProject.language ?? "",
        description: nextProject.description ?? "",
        target_audience: nextProject.target_audience ?? "",
        monetization_model: nextProject.monetization_model ?? "",
        status: nextProject.status,
      });
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to load project");
    } finally {
      setLoading(false);
    }
  }, [id, setSelectedId]);

  useAsyncLoad(() => refresh(), [refresh]);

  async function onSave(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const updated = await updateProject(id, {
        name: form.name.trim(),
        niche: form.niche.trim() || null,
        country: form.country.trim() || null,
        language: form.language.trim() || null,
        description: form.description.trim() || null,
        target_audience: form.target_audience.trim() || null,
        monetization_model: form.monetization_model.trim() || null,
        status: form.status,
      });
      setProject(updated);
      setEditing(false);
      await refreshProjects();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to save project");
    } finally {
      setSaving(false);
    }
  }

  async function onDelete() {
    if (!window.confirm("Delete this project? This only works if it has no campaigns or content.")) return;
    setDeleting(true);
    setError(null);
    try {
      await deleteProject(id);
      await refreshProjects();
      setSelectedId("all");
      router.push("/projects");
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to delete project");
      setDeleting(false);
    }
  }

  if (loading) {
    return (
      <PageScaffold>
        <LoadingState label="Loading project…" />
      </PageScaffold>
    );
  }

  if (error && !project) {
    return (
      <PageScaffold>
        <ErrorState title="Unable to open project" message={error} onRetry={() => void refresh()} />
      </PageScaffold>
    );
  }

  if (!project) return null;

  return (
    <PageScaffold
      actions={
        <div className="d-flex flex-wrap gap-2">
          <Link href={`/parasite-seo/new?project=${project.id}`} className="btn btn-accent">
            New generation
          </Link>
          <Link href={`/content-studio?project=${project.id}`} className="btn btn-ghost">
            Content studio
          </Link>
          <button type="button" className="btn btn-ghost" onClick={() => setEditing((open) => !open)}>
            {editing ? "Close editor" : "Edit project"}
          </button>
          <button type="button" className="btn btn-ghost text-danger" disabled={deleting} onClick={() => void onDelete()}>
            {deleting ? "Deleting…" : "Delete"}
          </button>
        </div>
      }
    >
      {error ? <div className="alert alert-danger">{error}</div> : null}

      <div className="surface-card p-4 mb-4">
        <div className="d-flex justify-content-between align-items-start gap-3 flex-wrap">
          <div>
            <div className="small text-uppercase text-muted fw-semibold mb-1">Project profile</div>
            <h2 className="h4 mb-2">{project.name}</h2>
            <p className="text-muted mb-2">{project.description || "No description yet."}</p>
            <div className="d-flex flex-wrap gap-3 small text-muted">
              <span>{project.niche || "No niche"}</span>
              <span>
                {project.country || "—"} · {project.language || "—"}
              </span>
              <span>{project.content_count} assets</span>
              <span>{project.campaign_count} campaigns</span>
              <span>Updated {formatDate(project.updated_at)}</span>
            </div>
          </div>
          <StatusBadge value={project.status} />
        </div>
      </div>

      {editing ? (
        <form className="surface-card p-4 mb-4" onSubmit={onSave}>
          <h3 className="section-title mb-3">Edit project</h3>
          <div className="row g-3">
            <div className="col-md-6">
              <label className="form-label" htmlFor="edit-name">
                Name
              </label>
              <input
                id="edit-name"
                className="form-control"
                value={form.name}
                onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                required
              />
            </div>
            <div className="col-md-3">
              <label className="form-label" htmlFor="edit-status">
                Status
              </label>
              <select
                id="edit-status"
                className="form-select"
                value={form.status}
                onChange={(event) => setForm((current) => ({ ...current, status: event.target.value }))}
              >
                <option value="active">Active</option>
                <option value="paused">Paused</option>
                <option value="archived">Archived</option>
              </select>
            </div>
            <div className="col-md-3">
              <label className="form-label" htmlFor="edit-niche">
                Niche
              </label>
              <input
                id="edit-niche"
                className="form-control"
                value={form.niche}
                onChange={(event) => setForm((current) => ({ ...current, niche: event.target.value }))}
              />
            </div>
            <div className="col-md-6">
              <label className="form-label" htmlFor="edit-country">
                Country
              </label>
              <input
                id="edit-country"
                className="form-control"
                value={form.country}
                onChange={(event) => setForm((current) => ({ ...current, country: event.target.value }))}
              />
            </div>
            <div className="col-md-6">
              <label className="form-label" htmlFor="edit-language">
                Language
              </label>
              <input
                id="edit-language"
                className="form-control"
                value={form.language}
                onChange={(event) => setForm((current) => ({ ...current, language: event.target.value }))}
              />
            </div>
            <div className="col-md-6">
              <label className="form-label" htmlFor="edit-audience">
                Target audience
              </label>
              <input
                id="edit-audience"
                className="form-control"
                value={form.target_audience}
                onChange={(event) => setForm((current) => ({ ...current, target_audience: event.target.value }))}
              />
            </div>
            <div className="col-md-6">
              <label className="form-label" htmlFor="edit-monetization">
                Monetization
              </label>
              <input
                id="edit-monetization"
                className="form-control"
                value={form.monetization_model}
                onChange={(event) => setForm((current) => ({ ...current, monetization_model: event.target.value }))}
              />
            </div>
            <div className="col-12">
              <label className="form-label" htmlFor="edit-description">
                Description
              </label>
              <textarea
                id="edit-description"
                className="form-control"
                rows={3}
                value={form.description}
                onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
              />
            </div>
          </div>
          <button className="btn btn-accent mt-3" type="submit" disabled={saving}>
            {saving ? "Saving…" : "Save changes"}
          </button>
        </form>
      ) : null}

      <div className="surface-card mb-4">
        <div className="p-3 border-bottom d-flex justify-content-between align-items-center">
          <h3 className="section-title mb-0">Generated content</h3>
          <Link href={`/parasite-seo?project=${project.id}`} className="btn btn-sm btn-ghost">
            All generations
          </Link>
        </div>
        {jobs.length === 0 ? (
          <div className="p-3">
            <EmptyStateBlock title="No generations yet" body="Create AI content for this project to see it here." />
          </div>
        ) : (
          <div className="table-responsive">
            <table className="table table-clean">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Status</th>
                  <th>SEO</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => (
                  <tr key={job.id}>
                    <td>
                      <Link href={`/parasite-seo/${job.id}`}>{job.content?.title || "Untitled generation"}</Link>
                      <div className="small text-muted text-truncate" style={{ maxWidth: 360 }}>
                        {job.original_prompt.slice(0, 100)}
                      </div>
                    </td>
                    <td>
                      <StatusBadge value={job.status} />
                    </td>
                    <td>{job.content?.seo_score ?? "—"}</td>
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
                        {job.is_public && job.public_url ? (
                          <a className="btn btn-sm btn-ghost" href={job.public_url} target="_blank" rel="noreferrer">
                            Page
                          </a>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="surface-card mb-4">
        <div className="p-3 border-bottom">
          <h3 className="section-title mb-0">Content assets</h3>
        </div>
        {content.length === 0 ? (
          <div className="p-3">
            <EmptyStateBlock title="No assets yet" body="Drafts from Content Studio will appear here." />
          </div>
        ) : (
          <div className="table-responsive">
            <table className="table table-clean">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Status</th>
                  <th>Words</th>
                  <th>Updated</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {content.map((row) => (
                  <tr key={row.id}>
                    <td>
                      <Link href={`/content-studio/${row.id}`}>{row.title}</Link>
                    </td>
                    <td>
                      <StatusBadge value={row.status} />
                    </td>
                    <td>{row.word_count}</td>
                    <td>{formatDate(row.updated_at)}</td>
                    <td className="text-end">
                      <Link className="btn btn-sm btn-accent" href={`/content-studio/${row.id}`}>
                        Open
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="surface-card">
        <div className="p-3 border-bottom">
          <h3 className="section-title mb-0">Campaigns</h3>
        </div>
        {campaigns.length === 0 ? (
          <div className="p-3">
            <EmptyStateBlock title="No campaigns" body="Campaigns for this project will show here." />
          </div>
        ) : (
          <div className="table-responsive">
            <table className="table table-clean">
              <thead>
                <tr>
                  <th>Campaign</th>
                  <th>Status</th>
                  <th>Updated</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {campaigns.map((row) => (
                  <tr key={row.id}>
                    <td>{row.name}</td>
                    <td>
                      <StatusBadge value={row.status} />
                    </td>
                    <td>{formatDate(row.updated_at)}</td>
                    <td className="text-end">
                      <Link className="btn btn-sm btn-ghost" href="/campaigns">
                        View in campaigns
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </PageScaffold>
  );
}

"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { PageScaffold } from "@/components/layout/PageScaffold";
import { EmptyStateBlock, ErrorState, LoadingState } from "@/components/ui/AsyncState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useProject } from "@/context/ProjectContext";
import { formatDate } from "@/lib/format";
import { ApiClientError } from "@/services/api-client";
import { createProject, deleteProject } from "@/services/project-service";

export function ProjectsView() {
  const router = useRouter();
  const { projects, setSelectedId, loading, error, refreshProjects } = useProject();
  const [name, setName] = useState("");
  const [niche, setNiche] = useState("");
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  async function onCreate(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      const project = await createProject({
        name: name.trim(),
        niche: niche.trim() || null,
        country: "United States",
        language: "English",
      });
      setName("");
      setNiche("");
      await refreshProjects();
      setSelectedId(project.id);
      router.push(`/projects/${project.id}`);
    } catch (err) {
      setFormError(err instanceof ApiClientError ? err.message : "Unable to create project");
    } finally {
      setSaving(false);
    }
  }

  async function onDelete(projectId: string, projectName: string) {
    if (!window.confirm(`Delete “${projectName}”? This only works if it has no campaigns or content.`)) return;
    setFormError(null);
    try {
      await deleteProject(projectId);
      await refreshProjects();
    } catch (err) {
      setFormError(err instanceof ApiClientError ? err.message : "Unable to delete project");
    }
  }

  return (
    <PageScaffold>
      <div className="row g-3 mb-4">
        <div className="col-lg-5">
          <form className="surface-card p-4" onSubmit={onCreate}>
            <h2 className="section-title mb-3">Create project</h2>
            <div className="mb-3">
              <label className="form-label" htmlFor="project-name">
                Name
              </label>
              <input
                id="project-name"
                className="form-control"
                value={name}
                onChange={(event) => setName(event.target.value)}
                required
              />
            </div>
            <div className="mb-3">
              <label className="form-label" htmlFor="project-niche">
                Niche
              </label>
              <input
                id="project-niche"
                className="form-control"
                value={niche}
                onChange={(event) => setNiche(event.target.value)}
              />
            </div>
            {formError ? <div className="alert alert-danger py-2">{formError}</div> : null}
            <button className="btn btn-accent" type="submit" disabled={saving}>
              {saving ? "Saving…" : "Create project"}
            </button>
          </form>
        </div>
        <div className="col-lg-7">
          {loading ? <LoadingState label="Loading projects…" /> : null}
          {!loading && error ? (
            <ErrorState title="Unable to load projects" message={error} onRetry={() => void refreshProjects()} />
          ) : null}
          {!loading && !error && projects.length === 0 ? (
            <EmptyStateBlock title="No projects yet" body="Create your first project to organize campaigns and content." />
          ) : null}
          {!loading && !error && projects.length > 0 ? (
            <div className="row g-3">
              {projects.map((project) => (
                <div className="col-md-6" key={project.id}>
                  <div className="surface-card p-4 h-100">
                    <div className="d-flex justify-content-between align-items-start mb-3">
                      <h2 className="h5 mb-0">
                        <Link href={`/projects/${project.id}`}>{project.name}</Link>
                      </h2>
                      <StatusBadge value={project.status} />
                    </div>
                    <p className="text-muted small mb-3">{project.niche || "No niche set"}</p>
                    <div className="small mb-1">{project.country || "—"} · {project.language || "—"}</div>
                    <div className="d-flex gap-3 small text-muted mb-3">
                      <span>{project.content_count} assets</span>
                      <span>{project.campaign_count} campaigns</span>
                    </div>
                    <div className="small text-muted mb-3">Updated {formatDate(project.updated_at)}</div>
                    <div className="d-flex flex-wrap gap-2">
                      <Link className="btn btn-sm btn-accent" href={`/projects/${project.id}`}>
                        Open
                      </Link>
                      <Link
                        className="btn btn-sm btn-ghost"
                        href={`/projects/${project.id}`}
                        onClick={() => setSelectedId(project.id)}
                      >
                        Edit
                      </Link>
                      <button
                        className="btn btn-sm btn-ghost"
                        type="button"
                        onClick={() => void onDelete(project.id, project.name)}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      </div>
    </PageScaffold>
  );
}

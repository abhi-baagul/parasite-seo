"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { PageScaffold } from "@/components/layout/PageScaffold";
import { ErrorState, LoadingState } from "@/components/ui/AsyncState";
import { useProject } from "@/context/ProjectContext";
import { ApiClientError } from "@/services/api-client";
import {
  analyzeParasiteJob,
  archiveWebPage,
  createParasiteJob,
  createWebPage,
  decideOptimizeParasiteJob,
  generateParasiteJob,
  getParasiteJob,
  getWebPage,
  linkAnalyzeParasiteJob,
  mediaAnalyzeParasiteJob,
  optimizeParasiteJob,
  publishWebPage,
  runParasiteGenerationPipeline,
  seoAnalyzeParasiteJob,
  unpublishWebPage,
  updateParasiteRequirements,
  updatePublishedWebPage,
  updateWebPage,
  uploadParasiteMedia,
  type ParasiteJob,
  type PublicPagePayload,
  type WebPageSummary,
} from "@/services/parasite-seo-service";
import { PublicArticleView } from "@/features/parasite-seo/PublicArticleView";
import { downloadExport } from "@/services/studio-service";

const STEPS = [
  "Input",
  "Analyze",
  "Generate",
  "SEO",
  "Media & Links",
  "Web Page",
  "Publish",
] as const;

const EXAMPLE = `As an SEO content writer, write an informative blog post on

[DIClock Referral Code "WL1Z375N" - Get 40% Off on Annual Plan]

of around 1000 words targeting keyword
[DIClock Referral Code].

Also include H1, H2, H3, bullet points,
tables and a clear CTA.

Primary keywords:

DIClock Referral Code For New User
DIClock Referral Code 2026
DIClock Referral Code Latest
DIClock Referral Code Signup`;

type UploadCard = {
  id: string;
  name: string;
  type: string;
  size: number;
  previewUrl?: string;
};

function stepIndex(job: ParasiteJob | null, uiStep: number): number {
  if (!job) return uiStep;
  const map: Record<string, number> = {
    input: 0,
    analyze: 1,
    generate: 2,
    seo: 3,
    media: 4,
    preview: 5,
    publish: 6,
  };
  return Math.max(uiStep, map[job.current_step] ?? uiStep);
}

export function ParasiteSeoWorkflow({ jobId }: { jobId?: string }) {
  const router = useRouter();
  const search = useSearchParams();
  const { selectedId, projects } = useProject();
  const projectFromQuery = search.get("project");
  const projectId = projectFromQuery || (selectedId !== "all" ? selectedId : projects[0]?.id);

  const [job, setJob] = useState<ParasiteJob | null>(null);
  const [step, setStep] = useState(0);
  const [prompt, setPrompt] = useState(EXAMPLE);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showTarget, setShowTarget] = useState(false);
  const [language, setLanguage] = useState("");
  const [country, setCountry] = useState("");
  const [audience, setAudience] = useState("");
  const [tone, setTone] = useState("");
  const [contentType, setContentType] = useState("");
  const [wordCount, setWordCount] = useState("");
  const [targetUrl, setTargetUrl] = useState("");
  const [anchorText, setAnchorText] = useState("");
  const [linkAttribute, setLinkAttribute] = useState("sponsored");
  const [uploads, setUploads] = useState<UploadCard[]>([]);
  const [requirementsJson, setRequirementsJson] = useState("");
  const [editingReqs, setEditingReqs] = useState(false);
  const [previewDevice, setPreviewDevice] = useState<"desktop" | "tablet" | "mobile">("desktop");
  const [webPage, setWebPage] = useState<WebPageSummary | null>(null);
  const [slugDraft, setSlugDraft] = useState("");
  const [confirmCreate, setConfirmCreate] = useState(false);
  const [showQr, setShowQr] = useState(false);
  const [exporting, setExporting] = useState<string | null>(null);
  const [previewPayload, setPreviewPayload] = useState<PublicPagePayload | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(Boolean(jobId));
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [progressLabel, setProgressLabel] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;
    void (async () => {
      setLoading(true);
      try {
        const data = await getParasiteJob(jobId);
        setJob(data);
        setPrompt(data.original_prompt);
        if (data.requirements) setRequirementsJson(JSON.stringify(data.requirements, null, 2));
        if (data.web_page) {
          setWebPage(data.web_page);
          setSlugDraft(data.web_page.slug);
        }
        setStep(stepIndex(data, 0));
      } catch (err) {
        setError(err instanceof ApiClientError ? err.message : "Unable to load job");
      } finally {
        setLoading(false);
      }
    })();
  }, [jobId]);

  const activeStep = useMemo(() => stepIndex(job, step), [job, step]);

  async function wrap(label: string, action: () => Promise<void>) {
    setBusy(true);
    setError(null);
    setMessage(null);
    setProgressLabel(label);
    try {
      await action();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : err instanceof Error ? err.message : "Step failed");
    } finally {
      setBusy(false);
      setProgressLabel(null);
    }
  }

  async function exportPublished(format: "pdf" | "doc" | "csv") {
    const contentId = job?.content_id || job?.content?.id;
    if (!contentId) {
      setError("No article to export yet");
      return;
    }
    setExporting(format);
    setError(null);
    try {
      await downloadExport(contentId, format);
      setMessage(`Exported ${format.toUpperCase()}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setExporting(null);
    }
  }

  async function onGenerateContent() {
    if (!projectId) {
      setError("Select or create a project first");
      return;
    }
    await wrap("Analyzing your prompt…", async () => {
      let current = job;
      if (!current) {
        current = await createParasiteJob({
          project_id: projectId,
          prompt,
          advanced_settings: {
            language: language || undefined,
            country: country || undefined,
            audience: audience || undefined,
            tone: tone || undefined,
            content_type: contentType || undefined,
            word_count: wordCount || undefined,
          },
          target_link: targetUrl
            ? { target_url: targetUrl, anchor_text: anchorText || null, link_attribute: linkAttribute }
            : null,
        });
        setJob(current);
        router.replace(`/parasite-seo/${current.id}`);
        await flushPendingUploads(current.id);
      }
      const analyzed = await analyzeParasiteJob(current.id);
      setJob(analyzed);
      setRequirementsJson(JSON.stringify(analyzed.requirements || {}, null, 2));
      setStep(1);
      setMessage("Prompt analyzed — review requirements");
    });
  }

  async function uploadFiles(files: FileList | null) {
    if (!files?.length) return;
    const list = Array.from(files);
    if (!job) {
      // stash as local previews until job exists
      setUploads((prev) => [
        ...prev,
        ...list.map((file, idx) => ({
          id: `pending-${Date.now()}-${idx}`,
          name: file.name,
          type: file.type,
          size: file.size,
          previewUrl: file.type.startsWith("image/") ? URL.createObjectURL(file) : undefined,
          file,
        })),
      ] as UploadCard[]);
      // attach file via weak map on element - use state with any
      (window as unknown as { __pseoFiles?: File[] }).__pseoFiles = [
        ...((window as unknown as { __pseoFiles?: File[] }).__pseoFiles || []),
        ...list,
      ];
      return;
    }
    await wrap("Uploading media…", async () => {
      for (const file of list) {
        const uploaded = await uploadParasiteMedia(job.id, file);
        setUploads((prev) => [
          ...prev,
          {
            id: uploaded.id,
            name: uploaded.filename,
            type: uploaded.content_type,
            size: uploaded.size_bytes,
            previewUrl: uploaded.url,
          },
        ]);
      }
      setJob(await getParasiteJob(job.id));
    });
  }

  async function flushPendingUploads(jobIdValue: string) {
    const pending = (window as unknown as { __pseoFiles?: File[] }).__pseoFiles || [];
    for (const file of pending) {
      const uploaded = await uploadParasiteMedia(jobIdValue, file);
      setUploads((prev) => [
        ...prev.filter((u) => !u.id.startsWith("pending-")),
        {
          id: uploaded.id,
          name: uploaded.filename,
          type: uploaded.content_type,
          size: uploaded.size_bytes,
          previewUrl: uploaded.url,
        },
      ]);
    }
    (window as unknown as { __pseoFiles?: File[] }).__pseoFiles = [];
  }

  if (loading) return <LoadingState label="Loading workflow…" />;
  if (error && !job && jobId) return <ErrorState title="Unable to load" message={error} />;

  const req = (job?.requirements || {}) as Record<string, unknown>;
  const seo = (job?.seo_analysis || {}) as Record<string, unknown>;
  const stepState = job?.step_state || {};

  return (
    <PageScaffold
      actions={
        <Link href="/parasite-seo" className="btn btn-ghost btn-sm">
          All generations
        </Link>
      }
    >
      <div className="surface-card p-4 mb-3">
        <h1 className="section-title mb-1">Parasite SEO AI</h1>
        <p className="text-muted mb-3">Create a complete AI-powered web content page from a single prompt.</p>
        <div className="d-flex flex-wrap gap-2">
          {STEPS.map((label, index) => (
            <button
              key={label}
              type="button"
              className={`btn btn-sm ${activeStep === index ? "btn-accent" : "btn-ghost"}`}
              onClick={() => setStep(index)}
            >
              {index + 1}. {label}
            </button>
          ))}
        </div>
      </div>

      {error ? (
        <div className="alert alert-danger d-flex justify-content-between align-items-center">
          <span>{error}</span>
        </div>
      ) : null}
      {message ? <div className="alert alert-success">{message}</div> : null}
      {progressLabel ? <div className="alert alert-info">{progressLabel}</div> : null}

      {activeStep === 0 ? (
        <div className="surface-card p-4">
          <label className="form-label fw-semibold" htmlFor="pseo-prompt">
            Content prompt
          </label>
          <textarea
            id="pseo-prompt"
            className="form-control mb-3"
            rows={14}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter what you want to create..."
          />

          <button type="button" className="btn btn-ghost btn-sm mb-2" onClick={() => setShowAdvanced((v) => !v)}>
            {showAdvanced ? "Hide" : "Show"} advanced settings
          </button>
          {showAdvanced ? (
            <div className="row g-2 mb-3">
              {[
                ["Language", language, setLanguage],
                ["Country", country, setCountry],
                ["Target audience", audience, setAudience],
                ["Tone", tone, setTone],
                ["Content type", contentType, setContentType],
                ["Approx. word count", wordCount, setWordCount],
              ].map(([label, value, setter]) => (
                <div className="col-md-4" key={label as string}>
                  <label className="form-label">{label as string}</label>
                  <input
                    className="form-control"
                    value={value as string}
                    onChange={(e) => (setter as (v: string) => void)(e.target.value)}
                  />
                </div>
              ))}
            </div>
          ) : null}

          <div className="mb-3">
            <div className="fw-semibold mb-2">Upload media (optional)</div>
            <input
              className="form-control"
              type="file"
              multiple
              accept="image/jpeg,image/png,image/webp,image/gif,video/mp4,video/webm"
              onChange={(e) => void uploadFiles(e.target.files)}
            />
            <div className="row g-2 mt-2">
              {uploads.map((file) => (
                <div className="col-md-3" key={file.id}>
                  <div className="border rounded p-2 h-100">
                    {file.previewUrl && file.type.startsWith("image/") ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={file.previewUrl} alt="" className="img-fluid rounded mb-2" />
                    ) : (
                      <div className="small text-muted mb-2">{file.type || "file"}</div>
                    )}
                    <div className="small fw-semibold text-truncate">{file.name}</div>
                    <div className="small text-muted">{Math.round(file.size / 1024)} KB</div>
                    <button
                      type="button"
                      className="btn btn-ghost btn-sm mt-1"
                      onClick={() => setUploads((prev) => prev.filter((u) => u.id !== file.id))}
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <button type="button" className="btn btn-ghost btn-sm mb-2" onClick={() => setShowTarget((v) => !v)}>
            {showTarget ? "Hide" : "Show"} optional target link
          </button>
          {showTarget ? (
            <div className="row g-2 mb-3">
              <div className="col-md-6">
                <label className="form-label">Target URL</label>
                <input className="form-control" value={targetUrl} onChange={(e) => setTargetUrl(e.target.value)} placeholder="https://…" />
              </div>
              <div className="col-md-3">
                <label className="form-label">Anchor text</label>
                <input className="form-control" value={anchorText} onChange={(e) => setAnchorText(e.target.value)} />
              </div>
              <div className="col-md-3">
                <label className="form-label">Link attribute</label>
                <select className="form-select" value={linkAttribute} onChange={(e) => setLinkAttribute(e.target.value)}>
                  <option value="sponsored">sponsored</option>
                  <option value="nofollow">nofollow</option>
                  <option value="ugc">ugc</option>
                  <option value="standard">standard</option>
                </select>
              </div>
              <p className="small text-muted mb-0">
                Optional. If omitted, the system will not invent a target URL. Internal links ≠ backlinks.
              </p>
            </div>
          ) : null}

          <button type="button" className="btn btn-accent" disabled={busy} onClick={() => void onGenerateContent()}>
            {busy ? "Working…" : "Generate content"}
          </button>
        </div>
      ) : null}

      {activeStep === 1 && job ? (
        <div className="surface-card p-4">
          <h2 className="section-title">Content analysis</h2>
          {!editingReqs ? (
            <>
              <div className="row g-3 mb-3">
                <div className="col-md-6">
                  <div className="small text-muted">Topic</div>
                  <div className="fw-semibold">{String(req.topic || "—")}</div>
                </div>
                <div className="col-md-6">
                  <div className="small text-muted">Primary keyword</div>
                  <div className="fw-semibold">{String(req.main_keyword || "—")}</div>
                </div>
                <div className="col-md-6">
                  <div className="small text-muted">Intent</div>
                  <div>{String(req.intent || "—")}</div>
                </div>
                <div className="col-md-6">
                  <div className="small text-muted">Word count</div>
                  <div>~{String(req.word_count || "—")}</div>
                </div>
              </div>
              <div className="mb-3">
                <div className="small text-muted">Secondary keywords</div>
                <ul>
                  {((req.secondary_keywords as string[]) || []).map((kw) => (
                    <li key={kw}>{kw}</li>
                  ))}
                </ul>
              </div>
              <div className="mb-3">
                <div className="small text-muted">Required elements</div>
                <div>{((req.required_elements as string[]) || []).map((el) => `✓ ${el}`).join("  ")}</div>
              </div>
            </>
          ) : (
            <textarea
              className="form-control font-monospace mb-3"
              rows={16}
              value={requirementsJson}
              onChange={(e) => setRequirementsJson(e.target.value)}
            />
          )}
          <div className="d-flex flex-wrap gap-2">
            <button
              type="button"
              className="btn btn-ghost"
              disabled={busy}
              onClick={() => {
                if (editingReqs) {
                  void wrap("Saving requirements…", async () => {
                    const parsed = JSON.parse(requirementsJson) as Record<string, unknown>;
                    const updated = await updateParasiteRequirements(job.id, parsed);
                    setJob(updated);
                    setEditingReqs(false);
                    setMessage("Requirements updated");
                  });
                } else setEditingReqs(true);
              }}
            >
              {editingReqs ? "Save edits" : "Edit"}
            </button>
            <button
              type="button"
              className="btn btn-accent"
              disabled={busy}
              onClick={() =>
                void wrap("Preparing generation…", async () => {
                  if (job.content?.content) {
                    setStep(2);
                    setMessage("Article already generated");
                    return;
                  }
                  await flushPendingUploads(job.id);
                  const generated = await runParasiteGenerationPipeline(job.id, (label) => {
                    setProgressLabel(label);
                  });
                  setJob(generated);
                  setStep(2);
                  setMessage("Article generated");
                })
              }
            >
              Continue
            </button>
          </div>
        </div>
      ) : null}

      {activeStep === 2 && job ? (
        <div className="surface-card p-4">
          <h2 className="section-title">Content generation</h2>
          <ul className="list-unstyled mb-3">
            {[
              ["prompt_analysis", "Prompt analyzed"],
              ["content_generation", "Content generation"],
              ["seo_analysis", "SEO analysis"],
              ["media_analysis", "Media processing"],
              ["link_analysis", "Link analysis"],
              ["web_page", "Final page"],
            ].map(([key, label]) => {
              const state = stepState[key] || "pending";
              const mark = state === "completed" ? "✓" : state === "running" ? "●" : state === "failed" ? "✕" : "○";
              return (
                <li key={key} className="mb-1">
                  {mark} {label}
                </li>
              );
            })}
          </ul>
          {job.content ? (
            <>
              <h3 className="h5">{job.content.title}</h3>
              <div
                className="border rounded p-3 mb-3 preview-frame"
                dangerouslySetInnerHTML={{ __html: job.content.content }}
              />
              <button type="button" className="btn btn-accent" disabled={busy} onClick={() => setStep(3)}>
                Continue to SEO
              </button>
            </>
          ) : (
            <button
              type="button"
              className="btn btn-accent"
              disabled={busy}
              onClick={() =>
                void wrap("Retrying generation…", async () => {
                  const generated = await runParasiteGenerationPipeline(job.id, (label) => {
                    setProgressLabel(label);
                  });
                  setJob(generated);
                })
              }
            >
              Retry generation
            </button>
          )}
        </div>
      ) : null}

      {activeStep === 3 && job ? (
        <div className="surface-card p-4">
          <h2 className="section-title">SEO AI analysis</h2>
          <button
            type="button"
            className="btn btn-ghost mb-3"
            disabled={busy}
            onClick={() =>
              void wrap("Running SEO analysis…", async () => {
                const result = await seoAnalyzeParasiteJob(job.id);
                setJob(result);
                setMessage("SEO analysis complete");
              })
            }
          >
            Run / refresh SEO analysis
          </button>
          <div className="display-6 mb-2">{Number(seo.overall_score ?? job.content?.seo_score ?? 0)} / 100</div>
          <pre className="small bg-light border rounded p-3 mb-3" style={{ whiteSpace: "pre-wrap" }}>
            {JSON.stringify(seo || { note: "Run SEO analysis to populate scores" }, null, 2)}
          </pre>
          {job.optimize_after ? (
            <div className="row g-3 mb-3">
              <div className="col-md-6">
                <h3 className="h6">Before</h3>
                <div className="border rounded p-2 small" dangerouslySetInnerHTML={{ __html: job.optimize_before || "" }} />
              </div>
              <div className="col-md-6">
                <h3 className="h6">After</h3>
                <div className="border rounded p-2 small" dangerouslySetInnerHTML={{ __html: job.optimize_after || "" }} />
              </div>
              <div className="d-flex gap-2">
                <button
                  type="button"
                  className="btn btn-accent"
                  disabled={busy}
                  onClick={() =>
                    void wrap("Accepting changes…", async () => {
                      setJob(await decideOptimizeParasiteJob(job.id, true));
                      setMessage("Optimization accepted (new version created)");
                    })
                  }
                >
                  Accept changes
                </button>
                <button
                  type="button"
                  className="btn btn-ghost"
                  disabled={busy}
                  onClick={() =>
                    void wrap("Rejecting changes…", async () => {
                      setJob(await decideOptimizeParasiteJob(job.id, false));
                    })
                  }
                >
                  Reject changes
                </button>
              </div>
            </div>
          ) : (
            <button
              type="button"
              className="btn btn-ghost me-2"
              disabled={busy}
              onClick={() =>
                void wrap("Optimizing content…", async () => {
                  setJob(await optimizeParasiteJob(job.id));
                })
              }
            >
              Optimize content
            </button>
          )}
          <button type="button" className="btn btn-accent" disabled={busy} onClick={() => setStep(4)}>
            Continue
          </button>
        </div>
      ) : null}

      {activeStep === 4 && job ? (
        <div className="surface-card p-4">
          <h2 className="section-title">Media & links</h2>
          <p className="text-muted">
            Internal links connect pages on this platform. External / target links point elsewhere. Backlinks are
            inbound from independent sites (not created here).
          </p>
          <div className="d-flex flex-wrap gap-2 mb-3">
            <button
              type="button"
              className="btn btn-ghost"
              disabled={busy}
              onClick={() =>
                void wrap("Analyzing links…", async () => {
                  setJob(await linkAnalyzeParasiteJob(job.id));
                })
              }
            >
              Run link analysis
            </button>
            <button
              type="button"
              className="btn btn-ghost"
              disabled={busy}
              onClick={() =>
                void wrap("Planning media…", async () => {
                  setJob(await mediaAnalyzeParasiteJob(job.id));
                  setMessage("Media & links ready");
                })
              }
            >
              Run media analysis
            </button>
          </div>
          <h3 className="h6">Attached media</h3>
          <ul>
            {(job.media || []).map((m) => (
              <li key={m.id}>
                {m.media_type}: {m.alt_text || m.url}
              </li>
            ))}
          </ul>
          <button type="button" className="btn btn-accent" onClick={() => setStep(5)}>
            Continue to web page
          </button>
        </div>
      ) : null}

      {activeStep === 5 && job?.content ? (
        <div className="surface-card p-4">
          <h2 className="section-title">Web page</h2>
          <p className="text-muted mb-3">
            Create a public web page from the approved content. This does not regenerate the article.
          </p>

          <div className="row g-3 mb-3">
            <div className="col-md-4">
              <div className="small text-muted">SEO score</div>
              <strong>{job.content.seo_score ?? "—"}/100</strong>
            </div>
            <div className="col-md-4">
              <div className="small text-muted">Content quality</div>
              <strong>{job.content.quality_score ?? "—"}/100</strong>
            </div>
            <div className="col-md-4">
              <div className="small text-muted">Media</div>
              <strong>{job.media?.length ?? 0}</strong>
            </div>
          </div>

          {!webPage ? (
            <>
              {!confirmCreate ? (
                <button
                  type="button"
                  className="btn btn-accent"
                  disabled={busy || !job.content.content}
                  onClick={() => setConfirmCreate(true)}
                >
                  Create web page
                </button>
              ) : (
                <div className="border rounded p-3">
                  <p className="mb-3">Create a public web page from this content?</p>
                  <div className="d-flex gap-2">
                    <button type="button" className="btn btn-ghost" onClick={() => setConfirmCreate(false)}>
                      Cancel
                    </button>
                    <button
                      type="button"
                      className="btn btn-accent"
                      disabled={busy}
                      onClick={() =>
                        void wrap("Building web page…", async () => {
                          const page = await createWebPage(job.id);
                          setWebPage(page);
                          setSlugDraft(page.slug);
                          setPreviewPayload(page.preview || null);
                          setConfirmCreate(false);
                          setMessage("Web page ready for preview");
                          const refreshed = await getParasiteJob(job.id);
                          setJob(refreshed);
                        })
                      }
                    >
                      Create page
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <>
              <label className="form-label">Slug</label>
              <div className="input-group mb-3">
                <span className="input-group-text">/p/</span>
                <input
                  className="form-control"
                  value={slugDraft}
                  disabled={webPage.status === "published" || busy}
                  onChange={(e) => setSlugDraft(e.target.value)}
                />
                {webPage.status !== "published" ? (
                  <button
                    type="button"
                    className="btn btn-ghost"
                    disabled={busy}
                    onClick={() =>
                      void wrap("Updating slug…", async () => {
                        const page = await updateWebPage(job.id, { slug: slugDraft });
                        setWebPage(page);
                        setSlugDraft(page.slug);
                        setPreviewPayload(page.preview || null);
                        setMessage("Slug updated");
                      })
                    }
                  >
                    Save slug
                  </button>
                ) : null}
              </div>

              <div className="mb-3">
                <div>
                  <strong>Status:</strong> {webPage.status}
                </div>
                <div>
                  <strong>Visibility:</strong> {webPage.visibility}
                </div>
                {webPage.public_url ? (
                  <div>
                    <strong>Public URL:</strong> {webPage.public_url}
                  </div>
                ) : null}
              </div>

              <div className="d-flex justify-content-between align-items-center mb-2">
                <h3 className="h6 mb-0">Preview</h3>
                <div className="d-flex gap-2">
                  {(["desktop", "tablet", "mobile"] as const).map((device) => (
                    <button
                      key={device}
                      type="button"
                      className={`btn btn-sm ${previewDevice === device ? "btn-accent" : "btn-ghost"}`}
                      onClick={() => setPreviewDevice(device)}
                    >
                      {device}
                    </button>
                  ))}
                </div>
              </div>

              <div className={`preview-frame preview-${previewDevice} mb-3`}>
                {previewPayload ? (
                  <PublicArticleView page={previewPayload} preview />
                ) : (
                  <button
                    type="button"
                    className="btn btn-ghost"
                    disabled={busy}
                    onClick={() =>
                      void wrap("Loading preview…", async () => {
                        const page = await getWebPage(job.id, true);
                        setWebPage(page);
                        setPreviewPayload(page.preview || null);
                      })
                    }
                  >
                    Preview page
                  </button>
                )}
              </div>

              <div className="d-flex flex-wrap gap-2">
                <button
                  type="button"
                  className="btn btn-ghost"
                  disabled={busy}
                  onClick={() =>
                    void wrap("Loading preview…", async () => {
                      const page = await getWebPage(job.id, true);
                      setWebPage(page);
                      setPreviewPayload(page.preview || null);
                    })
                  }
                >
                  Preview page
                </button>
                <button type="button" className="btn btn-accent" onClick={() => setStep(6)}>
                  Continue to publish
                </button>
              </div>
            </>
          )}
        </div>
      ) : null}

      {activeStep === 6 && job ? (
        <div className="surface-card p-4">
          <h2 className="section-title">Publication</h2>

          {webPage?.has_newer_content ? (
            <div className="alert alert-warning">
              Published page has newer changes.
              <div className="d-flex gap-2 mt-2">
                <button
                  type="button"
                  className="btn btn-sm btn-accent"
                  disabled={busy}
                  onClick={() =>
                    void wrap("Updating published page…", async () => {
                      const page = await updatePublishedWebPage(job.id);
                      setWebPage(page);
                      setPreviewPayload(page.preview || null);
                      setMessage("Published page updated");
                    })
                  }
                >
                  Update published page
                </button>
                <button type="button" className="btn btn-sm btn-ghost" onClick={() => setMessage("Kept current published version")}>
                  Keep current published version
                </button>
              </div>
            </div>
          ) : null}

          {webPage?.status === "published" && webPage.visibility === "public" ? (
            <>
              <div className="alert alert-success">Content published</div>
              <p>
                Public URL:{" "}
                <a href={webPage.public_url || "#"} target="_blank" rel="noreferrer">
                  {webPage.public_url}
                </a>
              </p>
              {webPage.public_url && /localhost|127\.0\.0\.1/.test(webPage.public_url) ? (
                <div className="alert alert-warning">
                  <strong>Local URL only.</strong> <code>localhost</code> works on this computer. Other phones and PCs
                  cannot open it until you deploy the app (or a tunnel) and set <code>PUBLIC_APP_URL</code> to your real
                  public domain, then republish.
                </div>
              ) : null}
              <div className="surface-card p-3 mb-3">
                <div className="fw-semibold mb-1">Want supporting links / backlinks?</div>
                <p className="small text-muted mb-2">
                  Publishing a public page does <strong>not</strong> automatically create links on random third-party
                  websites. That would be unauthorized posting. Use{" "}
                  <Link href="/parasite-seo/campaigns">Backlink Campaigns</Link> to plan Tier 1 / Tier 2 / cloud pages on{" "}
                  <em>your</em> authorized destinations (your sites, your cloud storage, connected CMS), then verify those
                  links.
                </p>
                <p className="small text-muted mb-2">
                  Link acquisition and SEO metrics are informational. Search engines independently determine crawling,
                  indexing, ranking, and link treatment.
                </p>
                <Link
                  href={`/parasite-seo/campaigns/new?project=${job.project_id}&job=${job.id}`}
                  className="btn btn-sm btn-accent"
                >
                  Create backlink campaign
                </Link>
              </div>
              <div className="surface-card p-3 mb-3">
                <div className="fw-semibold mb-1">Export</div>
                <p className="small text-muted mb-2">
                  Download this article as PDF, Word (.doc), or a CSV of title, URL, SEO fields, headings, and links.
                </p>
                <div className="d-flex flex-wrap gap-2">
                  {(["pdf", "doc", "csv"] as const).map((fmt) => (
                    <button
                      key={fmt}
                      type="button"
                      className="btn btn-sm btn-ghost"
                      disabled={Boolean(exporting) || !(job.content_id || job.content?.id)}
                      onClick={() => void exportPublished(fmt)}
                    >
                      {exporting === fmt ? "Exporting…" : fmt.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>
              <div className="d-flex flex-wrap gap-2">
                <a className="btn btn-accent" href={webPage.public_url || "#"} target="_blank" rel="noreferrer">
                  Open page
                </a>
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => {
                    if (webPage.public_url) void navigator.clipboard.writeText(webPage.public_url);
                    setMessage("URL copied.");
                  }}
                >
                  Copy URL
                </button>
                <button type="button" className="btn btn-ghost" onClick={() => setShowQr((v) => !v)}>
                  {showQr ? "Hide QR" : "Generate QR"}
                </button>
                <button
                  type="button"
                  className="btn btn-ghost"
                  disabled={busy}
                  onClick={() =>
                    void wrap("Unpublishing…", async () => {
                      const page = await unpublishWebPage(job.id);
                      setWebPage(page);
                      const refreshed = await getParasiteJob(job.id);
                      setJob(refreshed);
                      setMessage("Page unpublished");
                    })
                  }
                >
                  Unpublish
                </button>
                <button
                  type="button"
                  className="btn btn-ghost"
                  disabled={busy}
                  onClick={() => {
                    if (!window.confirm("Archive this public page? It will no longer be public.")) return;
                    void wrap("Archiving…", async () => {
                      const page = await archiveWebPage(job.id);
                      setWebPage(page);
                      const refreshed = await getParasiteJob(job.id);
                      setJob(refreshed);
                      setMessage("Page archived");
                    });
                  }}
                >
                  Archive
                </button>
              </div>
              {showQr && webPage.public_url ? (
                <div className="mt-3">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={`https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(webPage.public_url)}`}
                    alt="QR code for public URL"
                    width={180}
                    height={180}
                  />
                  <p className="small text-muted mt-2 mb-0" style={{ maxWidth: 420 }}>
                    The image is generated by qrserver.com with this page URL encoded as the QR payload. A camera scan
                    opens that URL directly — there is no extra redirect hop.
                  </p>
                </div>
              ) : null}
            </>
          ) : (
            <button
              type="button"
              className="btn btn-accent"
              disabled={busy || !webPage}
              onClick={() =>
                void wrap("Publishing public page…", async () => {
                  if (!webPage) {
                    const created = await createWebPage(job.id);
                    setWebPage(created);
                  }
                  const page = await publishWebPage(job.id);
                  setWebPage(page);
                  const refreshed = await getParasiteJob(job.id);
                  setJob(refreshed);
                  setMessage("Public page is live");
                })
              }
            >
              Make public
            </button>
          )}
          {!webPage ? (
            <p className="text-muted mt-3 mb-0">Create a web page in the previous step before publishing.</p>
          ) : null}
        </div>
      ) : null}
    </PageScaffold>
  );
}

"use client";

import { useAsyncLoad } from "@/hooks/useAsyncLoad";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { EmptyStateBlock, ErrorState, LoadingState } from "@/components/ui/AsyncState";
import { SeoAssetsPanel } from "@/features/content-studio/SeoAssetsPanel";
import { formatDateTime } from "@/lib/format";
import { ApiClientError } from "@/services/api-client";
import {
  approveOutline,
  getOutline,
  getResearch,
  getStrategy,
  runOutline,
  runResearch,
  runStrategy,
  type OutlineSection,
} from "@/services/ai-service";
import { generateContent } from "@/services/content-generation-service";
import {
  createContentVersion,
  getContent,
  listContentVersions,
  updateContent,
} from "@/services/content-service";
import { listLinks } from "@/services/link-service";
import {
  listQualityChecks,
  optimizeContent,
  runQualityCheck,
  runSeoCheck,
  type QualityCheckRow,
} from "@/services/quality-service";
import type { ContentDto, ContentVersionDto, LinkDto } from "@/services/types";

const STEPS = [
  "Prompt",
  "Requirements",
  "Research",
  "Strategy",
  "Outline",
  "Generate",
  "SEO Check",
  "Quality Check",
  "Final Review",
] as const;

type StepIndex = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8;
type StudioTab = "content" | "seo";

export function StudioEditor({ contentId }: { contentId: string }) {
  const editorRef = useRef<HTMLDivElement>(null);
  const [asset, setAsset] = useState<ContentDto | null>(null);
  const [versions, setVersions] = useState<ContentVersionDto[]>([]);
  const [checks, setChecks] = useState<QualityCheckRow[]>([]);
  const [links, setLinks] = useState<LinkDto[]>([]);
  const [selectedLink, setSelectedLink] = useState<LinkDto | null>(null);
  const [title, setTitle] = useState("");
  const [slug, setSlug] = useState("");
  const [draftHtml, setDraftHtml] = useState("");
  const [editorEpoch, setEditorEpoch] = useState(0);
  const [tab, setTab] = useState<StudioTab>("content");
  const [step, setStep] = useState<StepIndex>(2);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [research, setResearch] = useState<Record<string, unknown> | null>(null);
  const [strategy, setStrategy] = useState<Record<string, unknown> | null>(null);
  const [outlineH1, setOutlineH1] = useState("");
  const [outlineSections, setOutlineSections] = useState<OutlineSection[]>([]);
  const [outlineApproved, setOutlineApproved] = useState(false);
  const [seoReport, setSeoReport] = useState<Record<string, unknown> | null>(null);
  const [qualityReport, setQualityReport] = useState<Record<string, unknown> | null>(null);
  const [suggestions, setSuggestions] = useState<Array<{ before: string; after: string; reason: string }>>([]);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      let content = await getContent(contentId);
      const [versionPage, qualityRows, linkPage] = await Promise.all([
        listContentVersions(contentId),
        listQualityChecks(contentId).catch(() => []),
        listLinks({ contentAssetId: contentId }).catch(() => ({
          items: [] as LinkDto[],
          pagination: { page: 1, page_size: 50, total: 0 },
        })),
      ]);

      // If live body was wiped (e.g. empty editor save) but a version has HTML, restore it.
      if (!hasMeaningfulHtml(content.content)) {
        const recoverable = versionPage.items.find((row) => hasMeaningfulHtml(row.content));
        if (recoverable) {
          content = await updateContent(contentId, { content: recoverable.content });
          setMessage(`Restored article from version ${recoverable.version_number}`);
        }
      }

      setAsset(content);
      setTitle(content.title);
      setSlug(content.slug);
      paintEditor(content.content || "");
      setVersions(versionPage.items);
      setChecks(qualityRows);
      setLinks(linkPage.items);

      let hasResearch = false;
      let hasStrategy = false;
      let hasOutline = false;
      let outlineIsApproved = false;
      try {
        const r = await getResearch(contentId);
        if (r.research) {
          setResearch(r.research);
          hasResearch = true;
        } else {
          setResearch(null);
        }
      } catch {
        setResearch(null);
      }
      try {
        const s = await getStrategy(contentId);
        if (s.strategy) {
          setStrategy(s.strategy);
          hasStrategy = true;
        } else {
          setStrategy(null);
        }
      } catch {
        setStrategy(null);
      }
      try {
        const o = await getOutline(contentId);
        if (o.outline) {
          setOutlineH1(o.outline.h1);
          setOutlineSections(o.outline.sections || []);
          outlineIsApproved = Boolean(o.is_approved);
          hasOutline = true;
          setOutlineApproved(outlineIsApproved);
        } else {
          setOutlineH1("");
          setOutlineSections([]);
          setOutlineApproved(false);
        }
      } catch {
        setOutlineH1("");
        setOutlineSections([]);
        setOutlineApproved(false);
      }

      if (hasMeaningfulHtml(content.content)) {
        setStep(6);
      } else if (outlineIsApproved) setStep(5);
      else if (hasOutline) setStep(4);
      else if (hasStrategy) setStep(3);
      else if (hasResearch) setStep(2);
      else setStep(2);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to load content");
    } finally {
      setLoading(false);
    }
  }

  function paintEditor(html: string) {
    setDraftHtml(html);
    setEditorEpoch((value) => value + 1);
  }

  useAsyncLoad(() => load(), [contentId]);

  useEffect(() => {
    if (step < 6 || tab !== "content") return;
    const el = editorRef.current;
    if (!el) return;
    el.innerHTML = draftHtml;
    // draftHtml intentionally omitted: typing should not re-trigger; paintEditor bumps editorEpoch.
    // eslint-disable-next-line react-hooks/exhaustive-deps -- paint only on mount/step/tab/epoch
  }, [step, tab, editorEpoch]);

  function command(cmd: string, value?: string) {
    editorRef.current?.focus();
    document.execCommand(cmd, false, value);
  }

  async function wrap(action: () => Promise<void>) {
    setBusy(true);
    setMessage(null);
    setError(null);
    try {
      await action();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Agent failed");
    } finally {
      setBusy(false);
    }
  }

  function editorHtml(): string {
    const fromEditor = editorRef.current?.innerHTML?.trim() ?? "";
    if (hasMeaningfulHtml(fromEditor)) return fromEditor;
    if (hasMeaningfulHtml(draftHtml)) return draftHtml.trim();
    return (asset?.content ?? "").trim();
  }

  function hasBodyContent(): boolean {
    return hasMeaningfulHtml(editorHtml());
  }

  async function onSave() {
    if (!asset) return;
    await wrap(async () => {
      const html = editorHtml();
      if (!html && hasMeaningfulHtml(asset.content)) {
        throw new ApiClientError(
          400,
          "EMPTY_CONTENT",
          "Editor is empty — not overwriting the saved article. Refresh to restore, or paste content first.",
        );
      }
      const updated = await updateContent(asset.id, { title, slug, content: html });
      setAsset(updated);
      paintEditor(updated.content || html);
      setMessage("Saved");
    });
  }

  async function onSnapshot() {
    if (!asset) return;
    await wrap(async () => {
      if (!hasBodyContent()) {
        throw new ApiClientError(
          400,
          "EMPTY_CONTENT",
          "Nothing to snapshot — generate or write article content first.",
        );
      }
      const html = editorHtml();
      await createContentVersion(asset.id, {
        content: html,
        change_summary: "Manual snapshot from Content Studio",
      });
      const versionPage = await listContentVersions(asset.id);
      setVersions(versionPage.items);
      setMessage("Version snapshot created");
    });
  }

  if (loading) return <LoadingState label="Loading editor…" />;
  if (error && !asset) return <ErrorState title="Unable to load content" message={error} onRetry={() => void load()} />;
  if (!asset) return <EmptyStateBlock title="Content not found" body="This draft is not available." />;

  return (
    <div className="row g-3">
      <div className="col-12">
        <div className="surface-card p-3">
          <div className="d-flex flex-wrap gap-2 mb-3">
            <button
              type="button"
              className={`btn btn-sm ${tab === "content" ? "btn-accent" : "btn-ghost"}`}
              onClick={() => setTab("content")}
            >
              Content
            </button>
            <button
              type="button"
              className={`btn btn-sm ${tab === "seo" ? "btn-accent" : "btn-ghost"}`}
              onClick={() => {
                if (editorRef.current) {
                  setDraftHtml(editorRef.current.innerHTML);
                }
                setTab("seo");
              }}
            >
              SEO & Assets
            </button>
          </div>
          {tab === "content" ? (
            <div className="d-flex flex-wrap gap-2 align-items-center">
              {STEPS.map((label, index) => (
                <button
                  key={label}
                  type="button"
                  className={`btn btn-sm ${step === index ? "btn-accent" : "btn-ghost"}`}
                  onClick={() => setStep(index as StepIndex)}
                >
                  {index + 1}. {label}
                </button>
              ))}
            </div>
          ) : null}
          <div className="small text-muted mt-2">
            Status: {asset.status}. Word count: {asset.word_count}. Content SEO Score is editorial — not a ranking
            guarantee.
          </div>
          {error ? <div className="alert alert-danger py-2 mt-2 mb-0">{error}</div> : null}
          {message ? <div className="alert alert-success py-2 mt-2 mb-0">{message}</div> : null}
        </div>
      </div>

      {tab === "seo" ? (
        <div className="col-12">
          <SeoAssetsPanel
            contentId={contentId}
            onContentUpdated={(html) => {
              paintEditor(html);
              void load();
            }}
          />
        </div>
      ) : null}

      {tab === "content" ? (
      <>
      <div className="col-xl-8">
        {step <= 1 ? (
          <div className="surface-card p-4">
            <h2 className="section-title">Prompt & requirements</h2>
            <p className="text-muted">
              Prompt analysis and requirement confirmation happen on Create Content. Continue with research here.
            </p>
            <button type="button" className="btn btn-accent" onClick={() => setStep(2)}>
              Continue to research
            </button>
          </div>
        ) : null}

        {step === 2 ? (
          <StageCard
            title="Research"
            busy={busy}
            actionLabel={research ? "Re-run research" : "Create research brief"}
            onAction={() =>
              void wrap(async () => {
                const result = await runResearch(contentId);
                if (result.research) setResearch(result.research);
                setMessage(result.message || "Research brief saved");
                setStep(3);
              })
            }
          >
            {research ? <JsonBlock data={research} /> : <p className="text-muted mb-0">No research brief yet.</p>}
          </StageCard>
        ) : null}

        {step === 3 ? (
          <StageCard
            title="Strategy"
            busy={busy}
            actionLabel={strategy ? "Re-run strategy" : "Create strategy"}
            onAction={() =>
              void wrap(async () => {
                const result = await runStrategy(contentId);
                if (result.strategy) setStrategy(result.strategy);
                setMessage(result.message || "Strategy saved");
                setStep(4);
              })
            }
          >
            {strategy ? <JsonBlock data={strategy} /> : <p className="text-muted mb-0">Run research first, then strategy.</p>}
          </StageCard>
        ) : null}

        {step === 4 ? (
          <div className="surface-card p-4">
            <h2 className="section-title mb-3">Outline</h2>
            <div className="d-flex flex-wrap gap-2 mb-3">
              <button
                type="button"
                className="btn btn-accent"
                disabled={busy}
                onClick={() =>
                  void wrap(async () => {
                    const result = await runOutline(contentId);
                    if (!result.outline) {
                      throw new ApiClientError(500, "EMPTY_OUTLINE", "Outline generation returned no outline");
                    }
                    setOutlineH1(result.outline.h1);
                    setOutlineSections(result.outline.sections || []);
                    setOutlineApproved(false);
                    setMessage(result.message || "Outline generated");
                  })
                }
              >
                {busy ? "Working…" : outlineSections.length ? "Re-generate outline" : "Generate outline"}
              </button>
              <button
                type="button"
                className="btn btn-ghost"
                disabled={busy || !outlineSections.length}
                onClick={() =>
                  void wrap(async () => {
                    await approveOutline(contentId, { h1: outlineH1, sections: outlineSections });
                    setOutlineApproved(true);
                    setMessage("Outline approved");
                    setStep(5);
                  })
                }
              >
                Approve outline
              </button>
            </div>
            <label className="form-label" htmlFor="outline-h1">
              H1
            </label>
            <input
              id="outline-h1"
              className="form-control mb-3"
              value={outlineH1}
              onChange={(e) => setOutlineH1(e.target.value)}
            />
            <ul className="list-unstyled mb-0">
              {outlineSections.map((section, index) => (
                <li key={`${section.heading}-${index}`} className="mb-2" style={{ paddingLeft: `${(section.level - 1) * 12}px` }}>
                  <input
                    className="form-control form-control-sm"
                    value={section.heading}
                    onChange={(e) => {
                      const next = [...outlineSections];
                      next[index] = { ...section, heading: e.target.value };
                      setOutlineSections(next);
                    }}
                  />
                  <div className="small text-muted">
                    H{section.level}
                    {section.purpose ? ` · ${section.purpose}` : ""}
                  </div>
                </li>
              ))}
            </ul>
            {outlineApproved ? <div className="small text-success mt-3">Outline approved for generation.</div> : null}
          </div>
        ) : null}

        {step === 5 ? (
          <StageCard
            title="Generate article"
            busy={busy}
            actionLabel="Generate content"
            onAction={() =>
              void wrap(async () => {
                const result = await generateContent({ content_id: contentId });
                const refreshed = await getContent(contentId);
                setAsset(refreshed);
                setTitle(result.title || refreshed.title);
                setSlug(result.slug || refreshed.slug);
                const html = result.content || refreshed.content || "";
                paintEditor(html);
                const versionPage = await listContentVersions(contentId);
                setVersions(versionPage.items);
                setMessage(`Generated ${result.word_count} words`);
                setStep(6);
              })
            }
          >
            <p className="text-muted mb-0">
              Uses approved requirements, research, strategy, and outline. Creates a ContentVersion and AI run.
            </p>
          </StageCard>
        ) : null}

        {step >= 6 ? (
          <>
            <div className="surface-card p-3 mb-3">
              <div className="row g-3">
                <div className="col-md-8">
                  <label className="form-label" htmlFor="article-title">
                    Article title
                  </label>
                  <input
                    id="article-title"
                    className="form-control"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                  />
                </div>
                <div className="col-md-4">
                  <label className="form-label" htmlFor="slug">
                    Slug
                  </label>
                  <input id="slug" className="form-control" value={slug} onChange={(e) => setSlug(e.target.value)} />
                </div>
              </div>
              <div className="d-flex gap-2 mt-3">
                <button type="button" className="btn btn-accent" onClick={() => void onSave()} disabled={busy}>
                  Save
                </button>
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => void onSnapshot()}
                  disabled={busy || !hasBodyContent()}
                  title={hasBodyContent() ? "Save a version snapshot" : "Generate or write content first"}
                >
                  Save version
                </button>
              </div>
            </div>

            <div className="editor-toolbar" role="toolbar" aria-label="Formatting">
              <button type="button" title="Bold" onClick={() => command("bold")}>
                <i className="bi bi-type-bold" />
              </button>
              <button type="button" title="Italic" onClick={() => command("italic")}>
                <i className="bi bi-type-italic" />
              </button>
              <button type="button" title="H2" onClick={() => command("formatBlock", "H2")}>
                H2
              </button>
              <button type="button" title="H3" onClick={() => command("formatBlock", "H3")}>
                H3
              </button>
              <button type="button" title="Bullet list" onClick={() => command("insertUnorderedList")}>
                <i className="bi bi-list-ul" />
              </button>
              <button type="button" title="Numbered list" onClick={() => command("insertOrderedList")}>
                <i className="bi bi-list-ol" />
              </button>
              <button
                type="button"
                title="Insert link"
                onClick={() => {
                  const href = window.prompt("Link URL");
                  if (href) command("createLink", href);
                }}
              >
                <i className="bi bi-link-45deg" />
              </button>
            </div>
            <div
              ref={editorRef}
              className="editor-frame"
              contentEditable
              suppressContentEditableWarning
              role="textbox"
              aria-label="Article body"
              onClick={(event) => {
                const target = event.target as HTMLElement;
                if (target.tagName === "A") {
                  const href = target.getAttribute("href");
                  setSelectedLink(links.find((l) => l.target_url === href) || null);
                }
              }}
            />
          </>
        ) : null}
      </div>

      <div className="col-xl-4">
        <div className="surface-card p-3 mb-3">
          <h2 className="section-title mb-3">Quality panel</h2>
          <ScoreRow label="SEO Score" value={asset.seo_score ?? 0} />
          <ScoreRow label="Content Quality" value={asset.quality_score ?? 0} />
              <div className="d-grid gap-2 mt-3">
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  disabled={busy || !asset.content}
                  onClick={() =>
                    void wrap(async () => {
                      const result = await runSeoCheck(contentId);
                      setSeoReport(result.report);
                      setChecks(await listQualityChecks(contentId));
                      setAsset(await getContent(contentId));
                      setMessage("SEO check complete (editorial diagnostic)");
                      setStep(6);
                    })
                  }
                >
                  Run SEO check
                </button>
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  disabled={busy || !asset.content}
                  onClick={() =>
                    void wrap(async () => {
                      const result = await runQualityCheck(contentId);
                      setQualityReport(result.report);
                      setChecks(await listQualityChecks(contentId));
                      setAsset(await getContent(contentId));
                      setMessage(`Quality status: ${result.report.status}`);
                      setStep(7);
                    })
                  }
                >
                  Run quality check
                </button>
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  disabled={busy || !asset.content}
                  onClick={() =>
                    void wrap(async () => {
                      const result = await optimizeContent(contentId);
                      setSuggestions(result.suggestions);
                      setMessage("Optimization suggestions ready — accept manually in the editor");
                      setStep(8);
                    })
                  }
                >
                  Suggest optimizations
                </button>
                <button type="button" className="btn btn-accent btn-sm" onClick={() => setTab("seo")}>
                  Open SEO & Assets
                </button>
              </div>
              {selectedLink ? (
                <div className="small mt-3 border-top pt-3">
                  <strong>LINK</strong>
                  <div>Anchor: {selectedLink.anchor_text}</div>
                  <div>Target: {selectedLink.target_url}</div>
                  <div>Attribute: {selectedLink.link_attribute}</div>
                  <div>Status: {selectedLink.status}</div>
                </div>
              ) : null}
          {seoReport ? (
            <div className="small mt-3">
              <strong>SEO issues</strong>
              <ul>
                {((seoReport.issues as string[]) || []).map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {qualityReport ? (
            <div className="small mt-3">
              <strong>Quality</strong>
              <div>Status: {String(qualityReport.status)}</div>
              <ul>
                {((qualityReport.issues as string[]) || []).map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {suggestions.length ? (
            <div className="small mt-3">
              <strong>Suggestions (not auto-applied)</strong>
              {suggestions.map((item) => (
                <div key={`${item.before}-${item.after}`} className="border-top py-2">
                  <div>
                    <em>Before:</em> {item.before}
                  </div>
                  <div>
                    <em>After:</em> {item.after}
                  </div>
                  <div className="text-muted">{item.reason}</div>
                </div>
              ))}
            </div>
          ) : null}
        </div>

        <div className="surface-card p-3 mb-3">
          <h2 className="section-title mb-3">Stored checks</h2>
          {checks.length === 0 ? <p className="small text-muted mb-0">No quality checks yet.</p> : null}
          <ul className="list-unstyled mb-0">
            {checks.map((check) => (
              <li key={check.id} className="border-bottom py-2 small">
                <div className="fw-semibold">
                  {check.check_type} · {check.status} · {check.score ?? "—"}
                </div>
                <div className="text-muted">{formatDateTime(check.created_at)}</div>
              </li>
            ))}
          </ul>
        </div>

        <div className="surface-card p-3">
          <h2 className="section-title mb-3">Versions</h2>
          {versions.length === 0 ? <p className="small text-muted mb-0">No snapshots yet.</p> : null}
          <ul className="list-unstyled mb-0">
            {versions.map((version) => (
              <li key={version.id} className="border-bottom py-2">
                <div className="fw-semibold">v{version.version_number}</div>
                <div className="small text-muted">{version.change_summary || "Snapshot"}</div>
                <div className="small text-muted">{formatDateTime(version.created_at)}</div>
              </li>
            ))}
          </ul>
        </div>
      </div>
      </>
      ) : null}
    </div>
  );
}

function hasMeaningfulHtml(html: string | null | undefined): boolean {
  if (!html) return false;
  const text = html
    .replace(/<[^>]*>/g, " ")
    .replace(/&nbsp;/gi, " ")
    .replace(/\s+/g, " ")
    .trim();
  return text.length > 0;
}

function StageCard({
  title,
  children,
  actionLabel,
  onAction,
  busy,
}: {
  title: string;
  children: ReactNode;
  actionLabel: string;
  onAction: () => void;
  busy: boolean;
}) {
  return (
    <div className="surface-card p-4">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h2 className="section-title mb-0">{title}</h2>
        <button type="button" className="btn btn-accent" disabled={busy} onClick={onAction}>
          {busy ? "Working…" : actionLabel}
        </button>
      </div>
      {children}
    </div>
  );
}

function JsonBlock({ data }: { data: Record<string, unknown> }) {
  return (
    <pre className="small bg-light border rounded p-3 mb-0" style={{ whiteSpace: "pre-wrap" }}>
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

function ScoreRow({ label, value }: { label: string; value: number }) {
  return (
    <div className="mb-3">
      <div className="d-flex justify-content-between small mb-1">
        <span>{label}</span>
        <span>{value}</span>
      </div>
      <div className="progress progress-thin">
        <div className="progress-bar" style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

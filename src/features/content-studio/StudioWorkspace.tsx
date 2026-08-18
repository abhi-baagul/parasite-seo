"use client";

import { useAsyncLoad } from "@/hooks/useAsyncLoad";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { EmptyStateBlock, ErrorState, LoadingState } from "@/components/ui/AsyncState";
import { StudioOutlineNav } from "@/features/content-studio/StudioOutlineNav";
import { StudioTopBar } from "@/features/content-studio/StudioTopBar";
import { formatDateTime } from "@/lib/format";
import { ApiClientError } from "@/services/api-client";
import {
  createContentVersion,
  getContentVersion,
  updateContent,
} from "@/services/content-service";
import {
  approveContent,
  archiveContent,
  compareVersions,
  downloadExport,
  duplicateContent,
  getStudio,
  restoreVersion,
  sectionEdit,
  type StudioPayload,
} from "@/services/studio-service";
import { generateMetadata, analyzeSeo } from "@/services/seo-service";
import { runQualityCheck, runSeoCheck } from "@/services/quality-service";
import { getParasiteJobByContent } from "@/services/parasite-seo-service";
import {
  approveLinkSuggestion,
  listLinkSuggestions,
  rejectLinkSuggestion,
  type LinkSuggestion,
} from "@/services/content-network-service";

type RightTab = "seo" | "quality" | "links" | "internal" | "media" | "meta" | "ai" | "refs" | "versions";
type PreviewDevice = "desktop" | "tablet" | "mobile";
type SaveState = "idle" | "dirty" | "saving" | "saved" | "failed";

const AI_ACTIONS = [
  { id: "improve", label: "Improve writing" },
  { id: "more_concise", label: "Make more concise" },
  { id: "more_detailed", label: "Make more detailed" },
  { id: "rewrite", label: "Rewrite" },
  { id: "change_tone", label: "Change tone" },
  { id: "clarity", label: "Improve clarity" },
  { id: "fix_grammar", label: "Fix grammar" },
  { id: "add_examples", label: "Add examples" },
];

function textStats(html: string) {
  const text = html.replace(/<[^>]+>/g, " ").replace(/&nbsp;/gi, " ").replace(/\s+/g, " ").trim();
  const words = text ? text.split(" ").length : 0;
  const chars = text.length;
  const minutes = words ? Math.max(1, Math.ceil(words / 200)) : 0;
  return { words, chars, minutes };
}

function extractOutline(html: string) {
  if (typeof document === "undefined") return [];
  const doc = new DOMParser().parseFromString(html || "", "text/html");
  return Array.from(doc.querySelectorAll("h1,h2,h3")).map((el, idx) => {
    const text = el.textContent?.trim() || "";
    const anchor = el.id || `heading-${idx}`;
    return { level: Number(el.tagName.substring(1)), text, anchor };
  });
}

export function StudioWorkspace({ contentId }: { contentId: string }) {
  const router = useRouter();
  const editorRef = useRef<HTMLDivElement>(null);
  const autosaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [studio, setStudio] = useState<StudioPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [title, setTitle] = useState("");
  const [slug, setSlug] = useState("");
  const [draftHtml, setDraftHtml] = useState("");
  const [editorEpoch, setEditorEpoch] = useState(0);
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [rightTab, setRightTab] = useState<RightTab>("seo");
  const [selectionHtml, setSelectionHtml] = useState("");
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewDevice, setPreviewDevice] = useState<PreviewDevice>("desktop");
  const [exportOpen, setExportOpen] = useState(false);
  const [compareDiff, setCompareDiff] = useState<string[] | null>(null);
  const [metaSeoTitle, setMetaSeoTitle] = useState("");
  const [metaDescription, setMetaDescription] = useState("");
  const [tone, setTone] = useState("professional");
  const [internalSuggestions, setInternalSuggestions] = useState<LinkSuggestion[]>([]);

  const paintEditor = useCallback((html: string) => {
    setDraftHtml(html);
    setEditorEpoch((n) => n + 1);
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getStudio(contentId);
      setStudio(data);
      setTitle(data.content.title);
      setSlug(data.content.slug);
      paintEditor(data.content.content || "");
      setMetaSeoTitle(data.metadata.seo_title || data.content.seo_title || "");
      setMetaDescription(data.metadata.meta_description || data.content.meta_description || "");
      setSaveState("saved");
      try {
        const sug = await listLinkSuggestions(undefined, "suggested");
        setInternalSuggestions(sug.items.filter((s) => s.source_content_id === contentId));
      } catch {
        setInternalSuggestions([]);
      }
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to load Content Studio");
    } finally {
      setLoading(false);
    }
  }, [contentId, paintEditor]);

  useAsyncLoad(() => load(), [load]);

  useEffect(() => {
    const el = editorRef.current;
    if (!el) return;
    el.innerHTML = draftHtml;
  }, [editorEpoch, draftHtml]);

  useEffect(() => {
    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      if (saveState === "dirty" || saveState === "failed") {
        event.preventDefault();
        event.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [saveState]);

  function markDirty() {
    setSaveState("dirty");
    if (autosaveTimer.current) clearTimeout(autosaveTimer.current);
    autosaveTimer.current = setTimeout(() => {
      void persistDraft(false);
    }, 1600);
  }

  async function persistDraft(createVersion: boolean) {
    if (!studio) return;
    const html = editorRef.current?.innerHTML ?? draftHtml;
    setSaveState("saving");
    setError(null);
    try {
      const updated = await updateContent(contentId, {
        title,
        slug,
        content: html,
        seo_title: metaSeoTitle || null,
        meta_description: metaDescription || null,
      });
      setDraftHtml(updated.content || html);
      if (createVersion) {
        await createContentVersion(contentId, {
          content: updated.content || html,
          change_summary: "Manual version from Content Studio",
        });
        setMessage("Version saved");
      } else {
        setMessage(null);
      }
      setSaveState("saved");
      await load();
    } catch (err) {
      setSaveState("failed");
      setError(err instanceof ApiClientError ? err.message : "Save failed");
    }
  }

  function command(cmd: string, value?: string) {
    editorRef.current?.focus();
    document.execCommand(cmd, false, value);
    markDirty();
  }

  function captureSelection() {
    const sel = window.getSelection();
    if (!sel || sel.rangeCount === 0 || sel.isCollapsed) {
      setSelectionHtml("");
      return;
    }
    const range = sel.getRangeAt(0);
    if (!editorRef.current?.contains(range.commonAncestorContainer)) {
      setSelectionHtml("");
      return;
    }
    const div = document.createElement("div");
    div.appendChild(range.cloneContents());
    setSelectionHtml(div.innerHTML);
  }

  async function runAiAction(action: string) {
    if (!selectionHtml) {
      setError("Select a paragraph or section in the editor first.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const full = editorRef.current?.innerHTML ?? draftHtml;
      const result = await sectionEdit(contentId, {
        selected_html: selectionHtml,
        action,
        tone: action === "change_tone" ? tone : undefined,
        accept: true,
        full_html: full,
      });
      if (result.content) {
        paintEditor(result.content.content);
        setTitle(result.content.title);
      } else if (result.rewritten_html && selectionHtml) {
        const next = full.replace(selectionHtml, result.rewritten_html);
        paintEditor(next);
        markDirty();
      }
      setMessage(result.notes || "AI section edit applied — new version created");
      setSelectionHtml("");
      await load();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "AI edit failed");
    } finally {
      setBusy(false);
    }
  }

  function insertHtml(snippet: string) {
    editorRef.current?.focus();
    document.execCommand("insertHTML", false, snippet);
    markDirty();
  }

  function insertTable() {
    insertHtml(
      '<table><thead><tr><th>Column</th><th>Column</th></tr></thead><tbody><tr><td>Cell</td><td>Cell</td></tr></tbody></table><p></p>',
    );
  }

  function insertCta() {
    const url = window.prompt("CTA target URL", "https://example.com") || "https://example.com";
    const label = window.prompt("Button text", "Get Started") || "Get Started";
    insertHtml(
      `<section class="cta-block" data-cta="1"><h3>Ready to get started?</h3><p>Use the available offer to continue.</p><p><a href="${url}" rel="sponsored noopener" target="_blank">${label}</a></p></section><p></p>`,
    );
  }

  function insertImage() {
    const src = window.prompt("Image URL (https)");
    if (!src || !/^https:\/\//i.test(src)) {
      setError("Image URL must be https://");
      return;
    }
    const alt = window.prompt("Alt text", "") || "";
    insertHtml(`<figure><img src="${src}" alt="${alt}" loading="lazy" /><figcaption>${alt}</figcaption></figure><p></p>`);
  }

  function insertVideo() {
    const url = window.prompt("YouTube or Vimeo embed URL (https)");
    if (!url || !/^https:\/\//i.test(url)) {
      setError("Video URL must be https://");
      return;
    }
    const allowed =
      /youtube\.com\/embed\//i.test(url) ||
      /youtube-nocookie\.com\/embed\//i.test(url) ||
      /player\.vimeo\.com\/video\//i.test(url);
    if (!allowed) {
      setError("Only YouTube/Vimeo embed URLs are allowed");
      return;
    }
    insertHtml(
      `<figure class="video-embed"><iframe src="${url}" title="Video" width="560" height="315" loading="lazy" allowfullscreen></iframe></figure><p></p>`,
    );
  }

  async function onApprove() {
    setBusy(true);
    try {
      await persistDraft(false);
      await approveContent(contentId);
      setMessage("Marked approved (not published)");
      await load();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Approve failed");
    } finally {
      setBusy(false);
    }
  }

  async function onDuplicate() {
    setBusy(true);
    try {
      const copy = await duplicateContent(contentId);
      router.push(`/content-studio/${copy.id}`);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Duplicate failed");
      setBusy(false);
    }
  }

  const liveStats = textStats(editorRef.current?.innerHTML ?? draftHtml);
  const outline = extractOutline(editorRef.current?.innerHTML ?? draftHtml);
  const saveLabel =
    saveState === "saving"
      ? "Saving…"
      : saveState === "saved"
        ? "Saved"
        : saveState === "failed"
          ? "Save failed"
          : saveState === "dirty"
            ? "Unsaved changes"
            : "Ready";

  if (loading) return <LoadingState label="Loading Content Studio…" />;
  if (error && !studio) return <ErrorState title="Unable to load" message={error} onRetry={() => void load()} />;
  if (!studio) return <EmptyStateBlock title="Not found" body="This content is unavailable." />;

  const seo = studio.seo_analysis as Record<string, unknown> | null;
  const seoScore = Number(seo?.overall_score ?? studio.content.seo_score ?? 0);

  return (
    <div className="studio-workspace">
      <StudioTopBar
        title={title}
        status={studio.content.status}
        saveLabel={saveLabel}
        busy={busy || saveState === "saving"}
        onSave={() => void persistDraft(false)}
        onPreview={() => setPreviewOpen(true)}
        onExport={() => setExportOpen(true)}
        onApprove={() => void onApprove()}
        onCreateWebPage={() => {
          void (async () => {
            try {
              if (!window.confirm("Create a public web page from this content?")) return;
              const job = await getParasiteJobByContent(contentId);
              router.push(`/parasite-seo/${job.id}`);
            } catch (err) {
              setError(
                err instanceof ApiClientError
                  ? err.message
                  : "Open this content from Parasite SEO AI to create a web page.",
              );
            }
          })();
        }}
      />

      {error ? (
        <div className="alert alert-danger py-2 d-flex justify-content-between align-items-center">
          <span>{error}</span>
          {saveState === "failed" ? (
            <button type="button" className="btn btn-sm btn-ghost" onClick={() => void persistDraft(false)}>
              Retry
            </button>
          ) : null}
        </div>
      ) : null}
      {message ? <div className="alert alert-success py-2">{message}</div> : null}

      <div className="row g-3">
        <div className="col-lg-2 d-none d-lg-block">
          <div className="surface-card p-3 sticky-panel">
            <h2 className="section-title mb-2">Outline</h2>
            <StudioOutlineNav
              items={outline.length ? outline : studio.outline}
              onJump={(anchor) => {
                const el = editorRef.current?.querySelector(`#${CSS.escape(anchor)}`);
                el?.scrollIntoView({ behavior: "smooth", block: "start" });
              }}
            />
            <hr />
            <h3 className="h6">Completeness</h3>
            <ul className="list-unstyled small mb-0">
              {studio.completeness.map((item) => (
                <li key={item.key} className="mb-1">
                  {item.status === "complete" ? "✓" : item.status === "warning" ? "⚠" : "○"} {item.label}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="col-lg-6">
          <div className="surface-card p-3 mb-3">
            <div className="row g-2">
              <div className="col-md-8">
                <label className="form-label" htmlFor="studio-title">
                  Title
                </label>
                <input
                  id="studio-title"
                  className="form-control"
                  value={title}
                  onChange={(e) => {
                    setTitle(e.target.value);
                    markDirty();
                  }}
                />
              </div>
              <div className="col-md-4">
                <label className="form-label" htmlFor="studio-slug">
                  Slug
                </label>
                <input
                  id="studio-slug"
                  className="form-control"
                  value={slug}
                  onChange={(e) => {
                    setSlug(e.target.value);
                    markDirty();
                  }}
                />
              </div>
            </div>
          </div>

          <div className="editor-toolbar" role="toolbar" aria-label="Formatting">
            <button type="button" title="Bold" onClick={() => command("bold")}>
              <i className="bi bi-type-bold" />
            </button>
            <button type="button" title="Italic" onClick={() => command("italic")}>
              <i className="bi bi-type-italic" />
            </button>
            <button type="button" title="Underline" onClick={() => command("underline")}>
              <i className="bi bi-type-underline" />
            </button>
            <button type="button" title="H1" onClick={() => command("formatBlock", "H1")}>
              H1
            </button>
            <button type="button" title="H2" onClick={() => command("formatBlock", "H2")}>
              H2
            </button>
            <button type="button" title="H3" onClick={() => command("formatBlock", "H3")}>
              H3
            </button>
            <button type="button" title="Paragraph" onClick={() => command("formatBlock", "P")}>
              P
            </button>
            <button type="button" title="Quote" onClick={() => command("formatBlock", "BLOCKQUOTE")}>
              “”
            </button>
            <button type="button" title="Bullets" onClick={() => command("insertUnorderedList")}>
              <i className="bi bi-list-ul" />
            </button>
            <button type="button" title="Numbers" onClick={() => command("insertOrderedList")}>
              <i className="bi bi-list-ol" />
            </button>
            <button
              type="button"
              title="Link"
              onClick={() => {
                const href = window.prompt("Link URL (https)");
                if (href) command("createLink", href);
              }}
            >
              <i className="bi bi-link-45deg" />
            </button>
            <button type="button" title="Table" onClick={insertTable}>
              <i className="bi bi-table" />
            </button>
            <button type="button" title="Image" onClick={insertImage}>
              <i className="bi bi-image" />
            </button>
            <button type="button" title="Video" onClick={insertVideo}>
              <i className="bi bi-play-btn" />
            </button>
            <button type="button" title="CTA" onClick={insertCta}>
              CTA
            </button>
            <button type="button" title="Divider" onClick={() => insertHtml("<hr /><p></p>")}>
              ―
            </button>
          </div>

          <div
            ref={editorRef}
            className="editor-frame studio-editor-frame"
            contentEditable
            suppressContentEditableWarning
            role="textbox"
            aria-label="Article body"
            onInput={() => markDirty()}
            onMouseUp={captureSelection}
            onKeyUp={captureSelection}
          />

          <div className="surface-card p-3 mt-3">
            <div className="d-flex flex-wrap gap-2 align-items-center justify-content-between mb-2">
              <h2 className="section-title mb-0">AI actions</h2>
              <select className="form-select form-select-sm w-auto" value={tone} onChange={(e) => setTone(e.target.value)}>
                <option value="professional">Professional</option>
                <option value="friendly">Friendly</option>
                <option value="concise">Concise</option>
              </select>
            </div>
            <p className="small text-muted">
              {selectionHtml ? "Selection captured — choose an action." : "Select text in the article to edit with AI."}
            </p>
            <div className="d-flex flex-wrap gap-2">
              {AI_ACTIONS.map((action) => (
                <button
                  key={action.id}
                  type="button"
                  className="btn btn-ghost btn-sm"
                  disabled={busy || !selectionHtml}
                  onClick={() => void runAiAction(action.id)}
                >
                  {action.label}
                </button>
              ))}
            </div>
          </div>

          <div className="studio-statusbar surface-card p-2 mt-3 small text-muted d-flex flex-wrap gap-3">
            <span>{liveStats.words} words</span>
            <span>{liveStats.chars} characters</span>
            <span>~{liveStats.minutes} min read (est. 200 wpm)</span>
            <span>Version count: {studio.versions.length}</span>
            <span>Updated {formatDateTime(studio.content.updated_at)}</span>
          </div>
        </div>

        <div className="col-lg-4">
          <div className="surface-card p-2 mb-3">
            <div className="d-flex flex-wrap gap-1">
              {(
                [
                  ["seo", "SEO"],
                  ["quality", "Quality"],
                  ["links", "Links"],
                  ["internal", "Internal"],
                  ["media", "Media"],
                  ["meta", "Metadata"],
                  ["ai", "AI"],
                  ["refs", "Refs"],
                  ["versions", "Versions"],
                ] as const
              ).map(([id, label]) => (
                <button
                  key={id}
                  type="button"
                  className={`btn btn-sm ${rightTab === id ? "btn-accent" : "btn-ghost"}`}
                  onClick={() => setRightTab(id)}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="surface-card p-3 sticky-panel">
            {rightTab === "seo" ? (
              <>
                <h2 className="section-title">SEO score</h2>
                <div className="display-6">{seoScore || 0}</div>
                <p className="small text-muted">Editorial diagnostic — not a ranking guarantee.</p>
                <button
                  type="button"
                  className="btn btn-ghost btn-sm mb-3"
                  disabled={busy}
                  onClick={() =>
                    void (async () => {
                      setBusy(true);
                      try {
                        await runSeoCheck(contentId);
                        await analyzeSeo(contentId);
                        await load();
                        setMessage("SEO analysis refreshed");
                      } catch (err) {
                        setError(err instanceof ApiClientError ? err.message : "SEO check failed");
                      } finally {
                        setBusy(false);
                      }
                    })()
                  }
                >
                  Refresh SEO
                </button>
                <pre className="small bg-light border rounded p-2 mb-0" style={{ whiteSpace: "pre-wrap" }}>
                  {JSON.stringify(seo || { note: "Run SEO analysis" }, null, 2)}
                </pre>
              </>
            ) : null}

            {rightTab === "quality" ? (
              <>
                <h2 className="section-title">Quality</h2>
                <button
                  type="button"
                  className="btn btn-ghost btn-sm mb-3"
                  disabled={busy}
                  onClick={() =>
                    void (async () => {
                      setBusy(true);
                      try {
                        await runQualityCheck(contentId);
                        await load();
                        setMessage("Quality check complete");
                      } catch (err) {
                        setError(err instanceof ApiClientError ? err.message : "Quality check failed");
                      } finally {
                        setBusy(false);
                      }
                    })()
                  }
                >
                  Run quality check
                </button>
                {studio.quality.length === 0 ? <p className="text-muted small">No checks yet.</p> : null}
                <ul className="list-unstyled mb-0">
                  {studio.quality.map((q) => (
                    <li key={q.id} className="border-bottom py-2 small">
                      <div className="fw-semibold">
                        {q.check_type} · {q.status} · {q.score ?? "—"}
                      </div>
                      <div className="text-muted">{q.created_at ? formatDateTime(q.created_at) : "—"}</div>
                    </li>
                  ))}
                </ul>
              </>
            ) : null}

            {rightTab === "links" ? (
              <>
                <h2 className="section-title">Links</h2>
                {studio.links.length === 0 ? <p className="small text-muted">No managed links yet.</p> : null}
                <ul className="list-unstyled mb-0">
                  {studio.links.map((link) => (
                    <li key={link.id} className="border-bottom py-2 small">
                      <div className="fw-semibold">{link.anchor_text}</div>
                      <div className="text-truncate">{link.target_url}</div>
                      <div className="text-muted">
                        {link.link_attribute} · {link.status}
                      </div>
                    </li>
                  ))}
                </ul>
                <Link href="/links" className="btn btn-ghost btn-sm mt-2">
                  Open Link Manager
                </Link>
              </>
            ) : null}

            {rightTab === "internal" ? (
              <>
                <h2 className="section-title">Internal links</h2>
                <p className="small text-muted">
                  Same-domain contextual links. These are not backlinks.
                </p>
                <h3 className="h6">Existing</h3>
                <ul className="list-unstyled mb-3">
                  {studio.links
                    .filter((l) => (l.target_url || "").includes("/p/"))
                    .map((link) => (
                      <li key={link.id} className="border-bottom py-2 small">
                        <div className="fw-semibold">{link.anchor_text}</div>
                        <div className="text-truncate">{link.target_url}</div>
                      </li>
                    ))}
                </ul>
                <h3 className="h6">Suggested</h3>
                {internalSuggestions.length === 0 ? (
                  <p className="small text-muted">No suggestions. Run Content Network analysis.</p>
                ) : null}
                {internalSuggestions.map((s) => (
                  <div key={s.id} className="border rounded p-2 mb-2 small">
                    <div className="fw-semibold">{s.anchor_text}</div>
                    <div>Target: {s.target_title}</div>
                    <div className="text-muted">Relevance: {s.relevance_score ?? "—"}%</div>
                    <div className="d-flex gap-2 mt-2">
                      <button
                        type="button"
                        className="btn btn-sm btn-accent"
                        disabled={busy}
                        onClick={() =>
                          void (async () => {
                            setBusy(true);
                            try {
                              const result = await approveLinkSuggestion(s.id);
                              setMessage(
                                `Internal link inserted. SEO ${String((result as { seo_before?: number }).seo_before ?? "—")} → ${String((result as { seo_after?: number }).seo_after ?? "—")}`,
                              );
                              await load();
                            } catch (err) {
                              setError(err instanceof ApiClientError ? err.message : "Insert failed");
                            } finally {
                              setBusy(false);
                            }
                          })()
                        }
                      >
                        Accept
                      </button>
                      <button
                        type="button"
                        className="btn btn-sm btn-ghost"
                        disabled={busy}
                        onClick={() =>
                          void (async () => {
                            await rejectLinkSuggestion(s.id);
                            setInternalSuggestions((prev) => prev.filter((x) => x.id !== s.id));
                          })()
                        }
                      >
                        Reject
                      </button>
                    </div>
                  </div>
                ))}
                <Link href="/parasite-seo/network" className="btn btn-ghost btn-sm mt-2">
                  Open Content Network
                </Link>
              </>
            ) : null}

            {rightTab === "media" ? (
              <>
                <h2 className="section-title">Media</h2>
                {studio.media.length === 0 ? <p className="small text-muted">No attached media assets.</p> : null}
                <ul className="list-unstyled mb-0">
                  {studio.media.map((m) => (
                    <li key={m.id} className="border-bottom py-2 small">
                      <div className="fw-semibold">{m.media_type}</div>
                      <div>{m.alt_text || m.caption || m.url || "—"}</div>
                      <div className="text-muted">{m.status}</div>
                    </li>
                  ))}
                </ul>
                <Link href="/media" className="btn btn-ghost btn-sm mt-2">
                  Open Media Library
                </Link>
              </>
            ) : null}

            {rightTab === "meta" ? (
              <>
                <h2 className="section-title">Metadata</h2>
                <label className="form-label" htmlFor="meta-title">
                  SEO title ({metaSeoTitle.length}/60)
                </label>
                <input
                  id="meta-title"
                  className="form-control mb-2"
                  value={metaSeoTitle}
                  onChange={(e) => {
                    setMetaSeoTitle(e.target.value);
                    markDirty();
                  }}
                />
                <label className="form-label" htmlFor="meta-desc">
                  Meta description ({metaDescription.length}/160)
                </label>
                <textarea
                  id="meta-desc"
                  className="form-control mb-2"
                  rows={3}
                  value={metaDescription}
                  onChange={(e) => {
                    setMetaDescription(e.target.value);
                    markDirty();
                  }}
                />
                <div className="search-preview border rounded p-2 mb-3 bg-light">
                  <div className="small text-muted mb-1">Search preview (not a live Google result)</div>
                  <div className="text-primary">{metaSeoTitle || title || "Title"}</div>
                  <div className="small text-success">example.com/{slug || "slug"}</div>
                  <div className="small">{metaDescription || "Meta description preview"}</div>
                </div>
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  disabled={busy}
                  onClick={() =>
                    void (async () => {
                      setBusy(true);
                      try {
                        await generateMetadata(contentId);
                        await load();
                        setMessage("AI metadata options generated — edit manually to keep control");
                      } catch (err) {
                        setError(err instanceof ApiClientError ? err.message : "Metadata generation failed");
                      } finally {
                        setBusy(false);
                      }
                    })()
                  }
                >
                  Generate with AI
                </button>
              </>
            ) : null}

            {rightTab === "ai" ? (
              <>
                <h2 className="section-title">AI activity</h2>
                {studio.ai_runs.length === 0 ? <p className="small text-muted">No AI runs yet.</p> : null}
                <ul className="list-unstyled mb-0">
                  {studio.ai_runs.map((run) => (
                    <li key={run.id} className="border-bottom py-2 small">
                      <div className="fw-semibold">
                        {run.agent_type} · {run.status}
                      </div>
                      <div className="text-muted">
                        {run.model || "model"} · {run.total_tokens} tokens · {run.duration_ms ?? "—"} ms
                      </div>
                    </li>
                  ))}
                </ul>
              </>
            ) : null}

            {rightTab === "refs" ? (
              <>
                <h2 className="section-title">Research / references</h2>
                {studio.research.payload ? (
                  <pre className="small bg-light border rounded p-2" style={{ whiteSpace: "pre-wrap" }}>
                    {JSON.stringify(studio.research.payload, null, 2)}
                  </pre>
                ) : (
                  <p className="small text-muted">No research brief yet. Generate from Create Content / pipeline.</p>
                )}
                <h3 className="h6 mt-3">External references</h3>
                <ul className="list-unstyled mb-0">
                  {studio.references.map((ref) => (
                    <li key={ref.id} className="border-bottom py-2 small">
                      <div className="fw-semibold">{ref.title}</div>
                      <div className="text-truncate">{ref.url || "—"}</div>
                      <div className="text-muted">
                        {ref.source_type} · {ref.status}
                        {ref.requires_verification ? " · needs verification" : ""}
                      </div>
                    </li>
                  ))}
                </ul>
              </>
            ) : null}

            {rightTab === "versions" ? (
              <>
                <h2 className="section-title">Versions</h2>
                <div className="d-flex flex-wrap gap-2 mb-3">
                  <button type="button" className="btn btn-accent btn-sm" disabled={busy} onClick={() => void persistDraft(true)}>
                    Save version
                  </button>
                  <button type="button" className="btn btn-ghost btn-sm" disabled={busy} onClick={() => void onDuplicate()}>
                    Duplicate
                  </button>
                  <button
                    type="button"
                    className="btn btn-ghost btn-sm"
                    disabled={busy}
                    onClick={() =>
                      void (async () => {
                        setBusy(true);
                        try {
                          await archiveContent(contentId);
                          await load();
                          setMessage("Archived");
                        } catch (err) {
                          setError(err instanceof ApiClientError ? err.message : "Archive failed");
                        } finally {
                          setBusy(false);
                        }
                      })()
                    }
                  >
                    Archive
                  </button>
                </div>
                <ul className="list-unstyled mb-3">
                  {studio.versions.map((v) => (
                    <li key={v.id} className="border-bottom py-2 small">
                      <div className="fw-semibold">
                        v{v.version_number} · {v.source}
                      </div>
                      <div className="text-muted">{v.change_summary || "Snapshot"}</div>
                      <div className="text-muted">{v.created_at ? formatDateTime(v.created_at) : "—"}</div>
                      <div className="d-flex gap-2 mt-1">
                        <button
                          type="button"
                          className="btn btn-ghost btn-sm"
                          onClick={() =>
                            void (async () => {
                              const full = await getContentVersion(contentId, v.id);
                              paintEditor(full.content);
                              markDirty();
                              setMessage(`Viewing v${v.version_number} in editor (not restored yet)`);
                            })()
                          }
                        >
                          View
                        </button>
                        <button
                          type="button"
                          className="btn btn-ghost btn-sm"
                          disabled={busy}
                          onClick={() =>
                            void (async () => {
                              setBusy(true);
                              try {
                                await restoreVersion(contentId, v.id);
                                await load();
                                setMessage(`Restored from v${v.version_number} (history preserved)`);
                              } catch (err) {
                                setError(err instanceof ApiClientError ? err.message : "Restore failed");
                              } finally {
                                setBusy(false);
                              }
                            })()
                          }
                        >
                          Restore
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
                {studio.versions.length >= 2 ? (
                  <button
                    type="button"
                    className="btn btn-ghost btn-sm"
                    onClick={() =>
                      void (async () => {
                        const [right, left] = studio.versions;
                        const result = await compareVersions(contentId, left.id, right.id);
                        setCompareDiff(result.unified_diff);
                      })()
                    }
                  >
                    Compare latest two
                  </button>
                ) : null}
                {compareDiff ? (
                  <pre className="small bg-light border rounded p-2 mt-2" style={{ whiteSpace: "pre-wrap" }}>
                    {compareDiff.join("\n")}
                  </pre>
                ) : null}
              </>
            ) : null}
          </div>
        </div>
      </div>

      {previewOpen ? (
        <div className="studio-modal" role="dialog" aria-modal="true">
          <div className="studio-modal-card">
            <div className="d-flex justify-content-between align-items-center mb-3">
              <h2 className="section-title mb-0">Preview</h2>
              <div className="d-flex gap-2">
                {(["desktop", "tablet", "mobile"] as PreviewDevice[]).map((device) => (
                  <button
                    key={device}
                    type="button"
                    className={`btn btn-sm ${previewDevice === device ? "btn-accent" : "btn-ghost"}`}
                    onClick={() => setPreviewDevice(device)}
                  >
                    {device}
                  </button>
                ))}
                <button type="button" className="btn btn-ghost btn-sm" onClick={() => setPreviewOpen(false)}>
                  Close
                </button>
              </div>
            </div>
            <div className={`preview-frame preview-${previewDevice}`}>
              <h1>{title}</h1>
              <div dangerouslySetInnerHTML={{ __html: editorRef.current?.innerHTML || draftHtml }} />
            </div>
          </div>
        </div>
      ) : null}

      {exportOpen ? (
        <div className="studio-modal" role="dialog" aria-modal="true">
          <div className="studio-modal-card" style={{ maxWidth: 420 }}>
            <h2 className="section-title">Export</h2>
            <p className="text-muted small">Downloads sanitized article files. Paths are not exposed.</p>
            <div className="d-grid gap-2">
              {(["html", "markdown", "txt", "pdf"] as const).map((fmt) => (
                <button
                  key={fmt}
                  type="button"
                  className="btn btn-ghost"
                  disabled={busy}
                  onClick={() =>
                    void (async () => {
                      setBusy(true);
                      try {
                        await persistDraft(false);
                        await downloadExport(contentId, fmt);
                        setMessage(`Exported ${fmt}`);
                        setExportOpen(false);
                      } catch (err) {
                        setError(err instanceof Error ? err.message : "Export failed");
                      } finally {
                        setBusy(false);
                      }
                    })()
                  }
                >
                  Export {fmt.toUpperCase()}
                </button>
              ))}
              <button type="button" className="btn btn-accent" onClick={() => setExportOpen(false)}>
                Close
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

"use client";

import { useState, type ReactNode } from "react";
import { ApiClientError } from "@/services/api-client";
import {
  analyzeLinks,
  analyzeSeo,
  decideCategory,
  decideExternalRef,
  decideInternalLink,
  decideMedia,
  decideTag,
  generateAllSeoAssets,
  generateMediaPlan,
  generateMetadata,
  generateTags,
  insertTargetLink,
  listCategories,
  listExternalRefs,
  listInternalLinks,
  listMediaSuggestions,
  listTags,
  runKeywordAnalysis,
  selectMetadata,
  suggestExternalRefs,
  suggestInternalLinks,
  suggestTargetLink,
  type ExternalRef,
  type LinkSuggestion,
  type MediaSuggestion,
  type MetadataPackage,
  type SeoReport,
  type TagRow,
} from "@/services/seo-service";

type Props = {
  contentId: string;
  onContentUpdated?: (html: string) => void;
};

export function SeoAssetsPanel({ contentId, onContentUpdated }: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [seo, setSeo] = useState<SeoReport | null>(null);
  const [keywords, setKeywords] = useState<Record<string, unknown> | null>(null);
  const [metadata, setMetadata] = useState<MetadataPackage | null>(null);
  const [tags, setTags] = useState<TagRow[]>([]);
  const [categories, setCategories] = useState<TagRow[]>([]);
  const [internalLinks, setInternalLinks] = useState<LinkSuggestion[]>([]);
  const [externalRefs, setExternalRefs] = useState<ExternalRef[]>([]);
  const [media, setMedia] = useState<MediaSuggestion[]>([]);
  const [targetUrl, setTargetUrl] = useState("https://example.com/diclock");
  const [anchorText, setAnchorText] = useState("DIClock Referral Code");
  const [linkAttr, setLinkAttr] = useState("sponsored");
  const [suggestedPhrase, setSuggestedPhrase] = useState<string | null>(null);
  const [slugEdit, setSlugEdit] = useState("");

  async function wrap(action: () => Promise<void>) {
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      await action();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "SEO action failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="vstack gap-3">
      <div className="surface-card p-3">
        <div className="d-flex flex-wrap gap-2">
          <Action disabled={busy} onClick={() => void wrap(async () => { setSeo(await analyzeSeo(contentId)); setMessage("SEO analysis updated"); })}>
            Analyze SEO
          </Action>
          <Action disabled={busy} onClick={() => void wrap(async () => { setKeywords(await runKeywordAnalysis(contentId)); setMessage("Keyword analysis saved"); })}>
            Analyze keywords
          </Action>
          <Action
            disabled={busy}
            onClick={() =>
              void wrap(async () => {
                const result = await generateMetadata(contentId);
                setMetadata(result.metadata);
                setSlugEdit(result.metadata.slug || "");
                setMessage("Metadata options generated — select one to apply");
              })
            }
          >
            Generate Metadata
          </Action>
          <Action
            disabled={busy}
            onClick={() =>
              void wrap(async () => {
                const result = await generateTags(contentId);
                setTags(result.tags);
                setCategories(result.categories);
                setMessage("Tags & categories suggested");
              })
            }
          >
            Generate Tags
          </Action>
          <Action
            disabled={busy}
            onClick={() =>
              void wrap(async () => {
                const result = await suggestInternalLinks(contentId);
                setInternalLinks(result.suggestions);
                setMessage("Internal link suggestions ready");
              })
            }
          >
            Suggest Internal Links
          </Action>
          <Action
            disabled={busy}
            onClick={() =>
              void wrap(async () => {
                const result = await suggestExternalRefs(contentId);
                setExternalRefs(result.references);
                setMessage("External references require verification");
              })
            }
          >
            Suggest External References
          </Action>
          <Action disabled={busy} onClick={() => void wrap(async () => { await analyzeLinks(contentId); setMessage("Link analysis complete"); })}>
            Analyze Target Links
          </Action>
          <Action
            disabled={busy}
            onClick={() =>
              void wrap(async () => {
                const result = await generateMediaPlan(contentId);
                setMedia(result.media);
                setMessage("Media plan generated");
              })
            }
          >
            Generate Media Plan
          </Action>
          <Action
            disabled={busy}
            onClick={() =>
              void wrap(async () => {
                const result = await generateAllSeoAssets(contentId);
                setSeo(result.seo as SeoReport);
                setKeywords(result.keywords as Record<string, unknown>);
                setMetadata((result.metadata as { metadata: MetadataPackage }).metadata);
                setTags((result.tags as { tags: TagRow[] }).tags);
                setCategories((result.tags as { categories: TagRow[] }).categories);
                setInternalLinks((result.internal_links as { suggestions: LinkSuggestion[] }).suggestions);
                setExternalRefs((result.external_references as { references: ExternalRef[] }).references);
                setMedia((result.media as { media: MediaSuggestion[] }).media);
                setMessage("All SEO assets generated (review before accepting)");
              })
            }
          >
            Generate All SEO Assets
          </Action>
        </div>
        {error ? <div className="alert alert-danger py-2 mt-3 mb-0">{error}</div> : null}
        {message ? <div className="alert alert-success py-2 mt-3 mb-0">{message}</div> : null}
        <p className="small text-muted mt-3 mb-0">
          Content SEO Score is an editorial diagnostic — not a Google ranking score or guarantee.
        </p>
      </div>

      {seo ? (
        <div className="surface-card p-3">
          <h2 className="section-title">Content SEO Score · {seo.overall_score} / 100</h2>
          <div className="row g-2 small mb-3">
            <Score label="Structure" value={seo.structure_score} />
            <Score label="Keywords" value={seo.keyword_score} />
            <Score label="Readability" value={seo.readability_score} />
            <Score label="Metadata" value={seo.metadata_score} />
            <Score label="Links" value={seo.link_score} />
            <Score label="Media" value={seo.media_score} />
          </div>
          <ul className="list-unstyled mb-0">
            {seo.checklist?.map((item) => (
              <li key={item.key} className="small border-bottom py-1 d-flex justify-content-between">
                <span>{item.label}</span>
                <span className={item.status === "PASS" ? "text-success" : item.status === "FAIL" ? "text-danger" : "text-warning"}>
                  {item.status === "PASS" ? "✓" : item.status === "FAIL" ? "✗" : "⚠"} {item.status}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {keywords ? (
        <Panel title="Keyword analysis">
          <pre className="small mb-0" style={{ whiteSpace: "pre-wrap" }}>
            {JSON.stringify(keywords, null, 2)}
          </pre>
        </Panel>
      ) : null}

      {metadata ? (
        <Panel title="Metadata options">
          <div className="mb-3">
            <label className="form-label">Slug</label>
            <input className="form-control form-control-sm" value={slugEdit} onChange={(e) => setSlugEdit(e.target.value)} />
          </div>
          <h3 className="h6">SEO title options</h3>
          {metadata.title_options.map((opt) => (
            <div key={opt.title} className="border rounded p-2 mb-2 small">
              <div className="fw-semibold">{opt.title}</div>
              <div className="text-muted">
                {opt.character_count} chars · clarity {opt.clarity_score ?? "—"} · intent {opt.intent_match ?? "—"}
              </div>
              <button
                type="button"
                className="btn btn-sm btn-ghost mt-2"
                disabled={busy}
                onClick={() =>
                  void wrap(async () => {
                    await selectMetadata(contentId, { seo_title: opt.title, slug: slugEdit || metadata.slug || undefined });
                    setMessage("SEO title selected");
                  })
                }
              >
                Accept title
              </button>
            </div>
          ))}
          <h3 className="h6 mt-3">Meta description options</h3>
          {metadata.meta_options.map((opt) => (
            <div key={opt.meta_description} className="border rounded p-2 mb-2 small">
              <div>{opt.meta_description}</div>
              <div className="text-muted">{opt.character_count} chars</div>
              <button
                type="button"
                className="btn btn-sm btn-ghost mt-2"
                disabled={busy}
                onClick={() =>
                  void wrap(async () => {
                    await selectMetadata(contentId, {
                      meta_description: opt.meta_description,
                      slug: slugEdit || metadata.slug || undefined,
                      og_title: metadata.og_title || undefined,
                      og_description: metadata.og_description || undefined,
                    });
                    setMessage("Meta description selected");
                  })
                }
              >
                Accept description
              </button>
            </div>
          ))}
        </Panel>
      ) : null}

      <Panel title="Tags & categories">
        <TagList
          rows={tags}
          onDecide={(id, status) =>
            void wrap(async () => {
              await decideTag(contentId, id, status);
              setTags(await listTags(contentId));
            })
          }
        />
        <TagList
          rows={categories}
          onDecide={(id, status) =>
            void wrap(async () => {
              await decideCategory(contentId, id, status);
              setCategories(await listCategories(contentId));
            })
          }
        />
      </Panel>

      <Panel title="Internal links">
        {internalLinks.length === 0 ? <p className="small text-muted mb-0">No suggestions yet.</p> : null}
        {internalLinks.map((item) => (
          <div key={item.id} className="border-bottom py-2 small">
            <div className="fw-semibold">{item.anchor_text}</div>
            <div className="text-muted">{item.target_path}</div>
            <div>{item.reason}</div>
            <div className="mt-1">Status: {item.status}</div>
            <div className="d-flex gap-2 mt-2">
              <button type="button" className="btn btn-sm btn-ghost" disabled={busy} onClick={() => void wrap(async () => { await decideInternalLink(contentId, item.id, "approved"); setInternalLinks(await listInternalLinks(contentId)); })}>
                Accept
              </button>
              <button type="button" className="btn btn-sm btn-ghost" disabled={busy} onClick={() => void wrap(async () => { await decideInternalLink(contentId, item.id, "rejected"); setInternalLinks(await listInternalLinks(contentId)); })}>
                Reject
              </button>
            </div>
          </div>
        ))}
      </Panel>

      <Panel title="External references">
        <p className="small text-muted">Unverified URLs are not auto-inserted.</p>
        {externalRefs.map((item) => (
          <div key={item.id} className="border-bottom py-2 small">
            <div className="fw-semibold">{item.anchor_suggestion}</div>
            <div>{item.reason}</div>
            <div className="text-warning">{item.requires_verification ? "requires_verification" : "verified"}</div>
            <div className="d-flex gap-2 mt-2">
              <button type="button" className="btn btn-sm btn-ghost" disabled={busy} onClick={() => void wrap(async () => { await decideExternalRef(contentId, item.id, "approved"); setExternalRefs(await listExternalRefs(contentId)); })}>
                Accept placeholder
              </button>
              <button type="button" className="btn btn-sm btn-ghost" disabled={busy} onClick={() => void wrap(async () => { await decideExternalRef(contentId, item.id, "rejected"); setExternalRefs(await listExternalRefs(contentId)); })}>
                Reject
              </button>
            </div>
          </div>
        ))}
      </Panel>

      <Panel title="Target link">
        <div className="row g-2">
          <div className="col-md-6">
            <label className="form-label">Target URL</label>
            <input className="form-control form-control-sm" value={targetUrl} onChange={(e) => setTargetUrl(e.target.value)} />
          </div>
          <div className="col-md-6">
            <label className="form-label">Anchor text</label>
            <input className="form-control form-control-sm" value={anchorText} onChange={(e) => setAnchorText(e.target.value)} />
          </div>
          <div className="col-md-6">
            <label className="form-label">Attribute</label>
            <select className="form-select form-select-sm" value={linkAttr} onChange={(e) => setLinkAttr(e.target.value)}>
              <option value="standard">standard</option>
              <option value="sponsored">sponsored — paid/sponsored placements</option>
              <option value="ugc">ugc — user-generated content</option>
              <option value="nofollow">nofollow — do not pass ranking credit</option>
            </select>
          </div>
        </div>
        <div className="d-flex flex-wrap gap-2 mt-3">
          <button
            type="button"
            className="btn btn-sm btn-ghost"
            disabled={busy}
            onClick={() =>
              void wrap(async () => {
                const result = await suggestTargetLink(contentId, {
                  target_url: targetUrl,
                  anchor_text: anchorText,
                  link_attribute: linkAttr,
                });
                setSuggestedPhrase(result.suggested_phrase);
                setMessage(result.note);
              })
            }
          >
            Suggest placement
          </button>
          <button
            type="button"
            className="btn btn-sm btn-accent"
            disabled={busy}
            onClick={() =>
              void wrap(async () => {
                const result = await insertTargetLink(contentId, {
                  target_url: targetUrl,
                  anchor_text: anchorText,
                  link_attribute: linkAttr,
                  placement_phrase: suggestedPhrase || undefined,
                });
                onContentUpdated?.(result.content);
                setMessage("Link inserted and content version saved");
              })
            }
          >
            Insert after review
          </button>
        </div>
        {suggestedPhrase ? <p className="small mt-2 mb-0"><em>Suggested phrase:</em> {suggestedPhrase}</p> : null}
      </Panel>

      <Panel title="Media plan">
        {media.length === 0 ? <p className="small text-muted mb-0">No media suggestions yet.</p> : null}
        {media.map((item) => (
          <div key={item.id} className="border-bottom py-2 small">
            <div className="fw-semibold">
              {item.media_type} · {item.placement || "placement TBD"}
            </div>
            <div>{item.description}</div>
            {item.generation_prompt ? <div className="text-muted mt-1">Prompt: {item.generation_prompt}</div> : null}
            {item.alt_text ? <div>Alt: {item.alt_text}</div> : null}
            {item.caption ? <div>Caption: {item.caption}</div> : null}
            <div className="mt-1">Status: {item.status}</div>
            <div className="d-flex gap-2 mt-2">
              <button type="button" className="btn btn-sm btn-ghost" disabled={busy} onClick={() => void wrap(async () => { await decideMedia(contentId, item.id, "approved"); setMedia(await listMediaSuggestions(contentId)); })}>
                Accept
              </button>
              <button type="button" className="btn btn-sm btn-ghost" disabled={busy} onClick={() => void wrap(async () => { await decideMedia(contentId, item.id, "rejected"); setMedia(await listMediaSuggestions(contentId)); })}>
                Reject
              </button>
            </div>
          </div>
        ))}
      </Panel>
    </div>
  );
}

function Action({
  children,
  onClick,
  disabled,
}: {
  children: ReactNode;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button type="button" className="btn btn-sm btn-ghost" onClick={onClick} disabled={disabled}>
      {children}
    </button>
  );
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="surface-card p-3">
      <h2 className="section-title mb-3">{title}</h2>
      {children}
    </div>
  );
}

function Score({ label, value }: { label: string; value: number }) {
  return (
    <div className="col-6 col-md-4">
      <div className="d-flex justify-content-between">
        <span>{label}</span>
        <span>{value}</span>
      </div>
      <div className="progress progress-thin">
        <div className="progress-bar" style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

function TagList({
  rows,
  onDecide,
}: {
  rows: TagRow[];
  onDecide: (id: string, status: "approved" | "rejected") => void;
}) {
  if (!rows.length) return null;
  return (
    <ul className="list-unstyled mb-3">
      {rows.map((row) => (
        <li key={row.id} className="d-flex justify-content-between align-items-center border-bottom py-1 small">
          <span>
            {row.name} {row.is_accepted ? "· accepted" : "· pending"}
          </span>
          <span className="d-flex gap-1">
            <button type="button" className="btn btn-sm btn-ghost" onClick={() => onDecide(row.id, "approved")}>
              Accept
            </button>
            <button type="button" className="btn btn-sm btn-ghost" onClick={() => onDecide(row.id, "rejected")}>
              Reject
            </button>
          </span>
        </li>
      ))}
    </ul>
  );
}

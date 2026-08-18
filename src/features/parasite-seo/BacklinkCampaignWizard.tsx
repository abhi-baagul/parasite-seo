"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { PageScaffold } from "@/components/layout/PageScaffold";
import { ErrorState, LoadingState } from "@/components/ui/AsyncState";
import { useProject } from "@/context/ProjectContext";
import { ApiClientError } from "@/services/api-client";
import {
  STRATEGY_OPTIONS,
  createBacklinkCampaign,
  createContentBucket,
  createPublishingDestination,
  generateCampaignAssets,
  getBacklinkCampaign,
  listCampaignTargets,
  listContentBuckets,
  listPublishingDestinations,
  listStrategyTemplates,
  publishCampaignAssets,
  saveStrategyTemplate,
  testPublishingDestination,
  updateBacklinkCampaign,
  verifyCampaignBacklinks,
  type BacklinkCampaign,
  type ContentBucket,
  type PublishingDestination,
  type StrategyTemplate,
  type TargetOption,
} from "@/services/backlink-campaign-service";

const STEPS = [
  "Target",
  "Keywords",
  "Strategy",
  "Tier structure",
  "Content bucket",
  "Destinations",
  "Generate",
  "Link review",
  "Publish",
  "Verify",
  "Monitoring",
];

export function BacklinkCampaignWizard({ campaignId }: { campaignId?: string }) {
  const router = useRouter();
  const params = useSearchParams();
  const { selectedId, projects } = useProject();
  const projectFromQuery = params.get("project");
  const projectId = projectFromQuery || (selectedId !== "all" ? selectedId : projects[0]?.id) || "";

  const [step, setStep] = useState(1);
  const [campaign, setCampaign] = useState<BacklinkCampaign | null>(null);
  const [targets, setTargets] = useState<TargetOption[]>([]);
  const [strategies, setStrategies] = useState<StrategyTemplate[]>([]);
  const [buckets, setBuckets] = useState<ContentBucket[]>([]);
  const [destinations, setDestinations] = useState<PublishingDestination[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(Boolean(campaignId));

  const [name, setName] = useState("AI Productivity Backlink Campaign");
  const [targetPageId, setTargetPageId] = useState<string>("");
  const [externalTarget, setExternalTarget] = useState("");
  const [primaryKeyword, setPrimaryKeyword] = useState("AI Productivity Tools");
  const [secondary, setSecondary] = useState("AI Tools for Students\nAI Productivity Apps\nBest AI Tools 2026");
  const [country, setCountry] = useState("Global");
  const [language, setLanguage] = useState("English");
  const [niche, setNiche] = useState("AI Productivity");
  const [audience, setAudience] = useState("Students and remote teams");
  const [strategyType, setStrategyType] = useState("tiered_network");
  const [tier1, setTier1] = useState(5);
  const [tier2, setTier2] = useState(10);
  const [cloud, setCloud] = useState(3);
  const [pr, setPr] = useState(1);
  const [outreach, setOutreach] = useState(10);
  const [maxDepth, setMaxDepth] = useState(2);
  const [bucketId, setBucketId] = useState("");
  const [newBucketName, setNewBucketName] = useState("AI Productivity");
  const [destinationId, setDestinationId] = useState("");
  const [selectedAssets, setSelectedAssets] = useState<string[]>([]);

  const hydrate = useCallback(async (id: string) => {
    const c = await getBacklinkCampaign(id);
    setCampaign(c);
    setStep(Math.max(1, Math.min(c.wizard_step || 1, 11)));
    setName(c.name);
    setPrimaryKeyword(c.primary_keyword || "");
    setSecondary((c.secondary_keywords || []).join("\n"));
    setCountry(c.country || "");
    setLanguage(c.language || "");
    setNiche(c.niche || "");
    setAudience(c.target_audience || "");
    setStrategyType(c.strategy_type);
    setTier1(Number(c.blueprint?.tier1 ?? 5));
    setTier2(Number(c.blueprint?.tier2 ?? 10));
    setCloud(Number(c.blueprint?.cloud ?? 0));
    setPr(Number(c.blueprint?.pr ?? 0));
    setOutreach(Number(c.blueprint?.outreach ?? 0));
    setMaxDepth(Number(c.blueprint?.max_tier_depth ?? 2));
    setBucketId(c.bucket_id || "");
    setTargetPageId(c.target_public_page_id || "");
    if (c.target_url && !c.target_public_page_id) setExternalTarget(c.target_url);
    setSelectedAssets((c.assets || []).map((a) => a.id));
  }, []);

  useEffect(() => {
    if (!projectId) return;
    void (async () => {
      try {
        const [t, s, b, d] = await Promise.all([
          listCampaignTargets(projectId),
          listStrategyTemplates(projectId),
          listContentBuckets(projectId),
          listPublishingDestinations(projectId),
        ]);
        setTargets(t);
        setStrategies(s);
        setBuckets(b);
        setDestinations(d);
        if (d[0]) setDestinationId(d[0].id);
        if (b[0]) setBucketId((prev) => prev || b[0].id);
        if (campaignId) {
          await hydrate(campaignId);
        }
      } catch (err) {
        setError(err instanceof ApiClientError ? err.message : "Failed to load wizard data");
      } finally {
        setLoading(false);
      }
    })();
  }, [projectId, campaignId, hydrate]);

  async function saveProgress(nextStep: number, extra: Record<string, unknown> = {}) {
    if (!campaign) return;
    const updated = await updateBacklinkCampaign(campaign.id, {
      wizard_step: nextStep,
      ...extra,
    });
    setCampaign(updated);
    setStep(nextStep);
  }

  async function createAndContinue() {
    if (!projectId) {
      setError("Select a project first");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const secondaryKeywords = secondary
        .split("\n")
        .map((s) => s.trim())
        .filter(Boolean);
      const created = await createBacklinkCampaign({
        project_id: projectId,
        name,
        strategy_type: strategyType,
        target_public_page_id: targetPageId || null,
        target_url: targetPageId ? null : externalTarget || null,
        primary_keyword: primaryKeyword,
        secondary_keywords: secondaryKeywords,
        country,
        language,
        niche,
        target_audience: audience,
        blueprint: {
          tier1,
          tier2,
          cloud,
          pr,
          outreach,
          max_tier_depth: maxDepth,
        },
      });
      setCampaign(created);
      await updateBacklinkCampaign(created.id, { wizard_step: 3, status: "planning" });
      setStep(3);
      router.replace(`/parasite-seo/campaigns/${created.id}`);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Could not create campaign");
    } finally {
      setBusy(false);
    }
  }

  if (!projectId) {
    return (
      <PageScaffold>
        <ErrorState title="Project required" message="Select a project to create a backlink campaign." />
      </PageScaffold>
    );
  }

  if (loading) {
    return (
      <PageScaffold>
        <LoadingState label="Loading campaign wizard…" />
      </PageScaffold>
    );
  }

  const assets = campaign?.assets || [];
  const backlinks = campaign?.backlinks || [];

  return (
    <PageScaffold
      actions={
        campaign ? (
          <button type="button" className="btn btn-ghost" onClick={() => router.push(`/parasite-seo/campaigns/${campaign.id}`)}>
            Open campaign detail
          </button>
        ) : null
      }
    >
      <div className="surface-card p-4 mb-4">
        <h2 className="section-title mb-1">{campaign ? campaign.name : "Create backlink campaign"}</h2>
        <p className="text-muted mb-2">Step {step} of 11 — {STEPS[step - 1]}</p>
        <div className="d-flex flex-wrap gap-1">
          {STEPS.map((label, i) => (
            <span
              key={label}
              className={`badge ${i + 1 === step ? "text-bg-dark" : i + 1 < step ? "text-bg-secondary" : "text-bg-light"}`}
            >
              {i + 1}. {label}
            </span>
          ))}
        </div>
      </div>

      {error ? <div className="alert alert-danger">{error}</div> : null}

      {step <= 2 && !campaign ? (
        <div className="surface-card p-4">
          {step === 1 ? (
            <>
              <h3 className="h5">Campaign & target</h3>
              <div className="mb-3">
                <label className="form-label">Campaign name</label>
                <input className="form-control" value={name} onChange={(e) => setName(e.target.value)} />
              </div>
              <div className="mb-3">
                <label className="form-label">Select published public page (money page)</label>
                <div className="list-group mb-2">
                  {targets.map((t) => (
                    <button
                      key={t.public_page_id}
                      type="button"
                      className={`list-group-item list-group-item-action ${targetPageId === t.public_page_id ? "active" : ""}`}
                      onClick={() => {
                        setTargetPageId(t.public_page_id);
                        setExternalTarget("");
                      }}
                    >
                      <div className="fw-semibold">{t.title}</div>
                      <div className="small">{t.url}</div>
                      <div className="small">
                        SEO {t.seo_score ?? "—"} · Quality {t.quality_score ?? "—"} · {t.status}
                      </div>
                    </button>
                  ))}
                  {targets.length === 0 ? (
                    <div className="text-muted small p-2">No published public pages yet — you can use an external authorized URL or plan without a target.</div>
                  ) : null}
                </div>
                <label className="form-label">Or external authorized target URL</label>
                <input
                  className="form-control"
                  placeholder="https://…"
                  value={externalTarget}
                  onChange={(e) => {
                    setExternalTarget(e.target.value);
                    setTargetPageId("");
                  }}
                />
                <div className="form-text">Target is optional while the campaign is only for content planning.</div>
              </div>
              <button type="button" className="btn btn-accent" onClick={() => setStep(2)}>
                Continue to keywords
              </button>
            </>
          ) : (
            <>
              <h3 className="h5">Keywords & audience</h3>
              <div className="row g-3">
                <div className="col-md-6">
                  <label className="form-label">Primary keyword</label>
                  <input className="form-control" value={primaryKeyword} onChange={(e) => setPrimaryKeyword(e.target.value)} />
                </div>
                <div className="col-md-6">
                  <label className="form-label">Secondary keywords (one per line)</label>
                  <textarea className="form-control" rows={4} value={secondary} onChange={(e) => setSecondary(e.target.value)} />
                </div>
                <div className="col-md-3">
                  <label className="form-label">Country</label>
                  <input className="form-control" value={country} onChange={(e) => setCountry(e.target.value)} />
                </div>
                <div className="col-md-3">
                  <label className="form-label">Language</label>
                  <input className="form-control" value={language} onChange={(e) => setLanguage(e.target.value)} />
                </div>
                <div className="col-md-3">
                  <label className="form-label">Niche</label>
                  <input className="form-control" value={niche} onChange={(e) => setNiche(e.target.value)} />
                </div>
                <div className="col-md-3">
                  <label className="form-label">Audience</label>
                  <input className="form-control" value={audience} onChange={(e) => setAudience(e.target.value)} />
                </div>
              </div>
              <div className="d-flex gap-2 mt-3">
                <button type="button" className="btn btn-ghost" onClick={() => setStep(1)}>
                  Back
                </button>
                <button type="button" className="btn btn-accent" disabled={busy} onClick={() => void createAndContinue()}>
                  {busy ? "Saving…" : "Save & choose strategy"}
                </button>
              </div>
            </>
          )}
        </div>
      ) : null}

      {campaign && step === 3 ? (
        <div className="surface-card p-4">
          <h3 className="h5">Campaign strategy</h3>
          <div className="row g-3">
            {STRATEGY_OPTIONS.map((opt) => (
              <div className="col-md-6" key={opt.value}>
                <button
                  type="button"
                  className={`w-100 text-start surface-card p-3 border ${strategyType === opt.value ? "border-dark" : ""}`}
                  onClick={() => setStrategyType(opt.value)}
                >
                  <div className="fw-semibold">{opt.label}</div>
                  <div className="small text-muted">{opt.description}</div>
                </button>
              </div>
            ))}
          </div>
          {strategies.length > 0 ? (
            <div className="mt-3">
              <label className="form-label">Use saved strategy</label>
              <select
                className="form-select"
                onChange={(e) => {
                  const s = strategies.find((x) => x.id === e.target.value);
                  if (!s) return;
                  setStrategyType(s.strategy_type);
                  setTier1(Number(s.blueprint.tier1 ?? 0));
                  setTier2(Number(s.blueprint.tier2 ?? 0));
                  setCloud(Number(s.blueprint.cloud ?? 0));
                  setPr(Number(s.blueprint.pr ?? 0));
                  setOutreach(Number(s.blueprint.outreach ?? 0));
                }}
                defaultValue=""
              >
                <option value="">Select…</option>
                {strategies.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                    {s.is_system ? " (system)" : ""}
                  </option>
                ))}
              </select>
            </div>
          ) : null}
          <button
            type="button"
            className="btn btn-accent mt-3"
            disabled={busy}
            onClick={() => {
              setBusy(true);
              void saveProgress(4, { strategy_type: strategyType })
                .catch((err) => setError(err instanceof ApiClientError ? err.message : "Save failed"))
                .finally(() => setBusy(false));
            }}
          >
            Continue
          </button>
        </div>
      ) : null}

      {campaign && step === 4 ? (
        <div className="surface-card p-4">
          <h3 className="h5">Tier structure (blueprint)</h3>
          <p className="text-muted small">Configurable planning values — not mass page spam.</p>
          <div className="row g-3">
            {[
              ["Tier 1", tier1, setTier1, 20],
              ["Tier 2", tier2, setTier2, 40],
              ["Cloud", cloud, setCloud, 10],
              ["PR", pr, setPr, 5],
              ["Outreach", outreach, setOutreach, 50],
            ].map(([label, value, setter, max]) => (
              <div className="col-md-4" key={String(label)}>
                <label className="form-label">{String(label)}</label>
                <input
                  type="number"
                  className="form-control"
                  min={0}
                  max={Number(max)}
                  value={Number(value)}
                  onChange={(e) => (setter as (n: number) => void)(Number(e.target.value))}
                />
              </div>
            ))}
            <div className="col-md-4">
              <label className="form-label">Max tier depth</label>
              <select className="form-select" value={maxDepth} onChange={(e) => setMaxDepth(Number(e.target.value))}>
                <option value={1}>1</option>
                <option value={2}>2</option>
                <option value={3}>3</option>
              </select>
            </div>
          </div>
          <div className="d-flex gap-2 mt-3 flex-wrap">
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => {
                void saveStrategyTemplate({
                  project_id: projectId,
                  name: `My ${strategyType} strategy`,
                  strategy_type: strategyType,
                  blueprint: { tier1, tier2, cloud, pr, outreach, max_tier_depth: maxDepth },
                }).then(() => listStrategyTemplates(projectId).then(setStrategies));
              }}
            >
              Save as strategy
            </button>
            <button
              type="button"
              className="btn btn-accent"
              disabled={busy}
              onClick={() => {
                setBusy(true);
                void saveProgress(5, {
                  blueprint: { tier1, tier2, cloud, pr, outreach, max_tier_depth: maxDepth },
                })
                  .catch((err) => setError(err instanceof ApiClientError ? err.message : "Save failed"))
                  .finally(() => setBusy(false));
              }}
            >
              Continue
            </button>
          </div>
        </div>
      ) : null}

      {campaign && step === 5 ? (
        <div className="surface-card p-4">
          <h3 className="h5">Content bucket</h3>
          <select className="form-select mb-3" value={bucketId} onChange={(e) => setBucketId(e.target.value)}>
            <option value="">Select bucket…</option>
            {buckets.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name} ({(b.topics || []).length} topics)
              </option>
            ))}
          </select>
          <div className="input-group mb-3">
            <input className="form-control" value={newBucketName} onChange={(e) => setNewBucketName(e.target.value)} />
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => {
                void createContentBucket({
                  project_id: projectId,
                  name: newBucketName,
                  topics: secondary.split("\n").map((s) => s.trim()).filter(Boolean),
                  keywords: [primaryKeyword, ...secondary.split("\n").map((s) => s.trim()).filter(Boolean)],
                  niche,
                }).then((b) => {
                  setBuckets((prev) => [...prev, b]);
                  setBucketId(b.id);
                });
              }}
            >
              Create bucket
            </button>
          </div>
          <button
            type="button"
            className="btn btn-accent"
            disabled={busy}
            onClick={() => {
              setBusy(true);
              void saveProgress(6, { bucket_id: bucketId || null })
                .catch((err) => setError(err instanceof ApiClientError ? err.message : "Save failed"))
                .finally(() => setBusy(false));
            }}
          >
            Continue
          </button>
        </div>
      ) : null}

      {campaign && step === 6 ? (
        <div className="surface-card p-4">
          <h3 className="h5">Publishing destinations</h3>
          <p className="text-muted small">Only user-authorized destinations. Credentials never appear in the UI.</p>
          <ul className="list-group mb-3">
            {destinations.map((d) => (
              <li key={d.id} className="list-group-item d-flex justify-content-between align-items-center">
                <div>
                  <strong>{d.name}</strong>
                  <div className="small text-muted">{d.provider_type}</div>
                </div>
                <div className="d-flex gap-2">
                  <button type="button" className="btn btn-sm btn-ghost" onClick={() => setDestinationId(d.id)}>
                    {destinationId === d.id ? "Selected" : "Select"}
                  </button>
                  <button
                    type="button"
                    className="btn btn-sm btn-ghost"
                    onClick={() => void testPublishingDestination(d.id).then(() => listPublishingDestinations(projectId).then(setDestinations))}
                  >
                    Test
                  </button>
                </div>
              </li>
            ))}
          </ul>
          <div className="d-flex gap-2 flex-wrap">
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => {
                void createPublishingDestination({
                  project_id: projectId,
                  name: "Mock Local Destination",
                  provider_type: "mock_local",
                  configuration: { path_prefix: `campaigns/${campaign.id}` },
                }).then((d) => {
                  setDestinations((prev) => [...prev, d]);
                  setDestinationId(d.id);
                });
              }}
            >
              Add mock local
            </button>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => {
                void createPublishingDestination({
                  project_id: projectId,
                  name: "Cloud static (authorized)",
                  provider_type: "cloud_static",
                  configuration: { bucket: "authorized-cloud-pages" },
                }).then((d) => {
                  setDestinations((prev) => [...prev, d]);
                  setDestinationId(d.id);
                });
              }}
            >
              Add cloud static
            </button>
            <button
              type="button"
              className="btn btn-accent"
              disabled={busy}
              onClick={() => {
                setBusy(true);
                void saveProgress(7)
                  .catch((err) => setError(err instanceof ApiClientError ? err.message : "Save failed"))
                  .finally(() => setBusy(false));
              }}
            >
              Continue to generate
            </button>
          </div>
        </div>
      ) : null}

      {campaign && step === 7 ? (
        <div className="surface-card p-4">
          <h3 className="h5">Content generation</h3>
          <p className="text-muted">Generate useful variants from the blueprint — not spun duplicates.</p>
          <button
            type="button"
            className="btn btn-accent"
            disabled={busy}
            onClick={() => {
              setBusy(true);
              void generateCampaignAssets(campaign.id)
                .then((res) => {
                  setCampaign(res.campaign);
                  setSelectedAssets((res.campaign.assets || []).map((a) => a.id));
                  setStep(8);
                })
                .catch((err) => setError(err instanceof ApiClientError ? err.message : "Generation failed"))
                .finally(() => setBusy(false));
            }}
          >
            {busy ? "Generating…" : "Generate assets"}
          </button>
        </div>
      ) : null}

      {campaign && step === 8 ? (
        <div className="surface-card p-4">
          <h3 className="h5">Link review</h3>
          <p className="small text-muted mb-3">
            Internal links stay on your domain. External host → your page is a backlink only after publish + verify.
          </p>
          <div className="table-responsive">
            <table className="table table-clean">
              <thead>
                <tr>
                  <th></th>
                  <th>Title</th>
                  <th>Type</th>
                  <th>Tier</th>
                  <th>Anchor</th>
                  <th>Target</th>
                  <th>Attribute</th>
                </tr>
              </thead>
              <tbody>
                {assets.map((a) => (
                  <tr key={a.id}>
                    <td>
                      <input
                        type="checkbox"
                        checked={selectedAssets.includes(a.id)}
                        onChange={(e) => {
                          setSelectedAssets((prev) =>
                            e.target.checked ? [...prev, a.id] : prev.filter((id) => id !== a.id),
                          );
                        }}
                      />
                    </td>
                    <td>{a.title}</td>
                    <td>{a.asset_type}</td>
                    <td>{a.tier}</td>
                    <td>{a.anchor_text}</td>
                    <td>
                      <code className="small">{a.target_url}</code>
                    </td>
                    <td>{a.link_attribute}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button
            type="button"
            className="btn btn-accent"
            onClick={() => {
              setBusy(true);
              void saveProgress(9)
                .catch((err) => setError(err instanceof ApiClientError ? err.message : "Save failed"))
                .finally(() => setBusy(false));
            }}
          >
            Continue to publish
          </button>
        </div>
      ) : null}

      {campaign && step === 9 ? (
        <div className="surface-card p-4">
          <h3 className="h5">Publish selected assets</h3>
          <p className="text-muted small">Publishes only to authorized / mock destinations. Confirm before large batches.</p>
          <button
            type="button"
            className="btn btn-accent"
            disabled={busy || selectedAssets.length === 0}
            onClick={() => {
              if (selectedAssets.length > 5 && !window.confirm(`Publish ${selectedAssets.length} assets?`)) return;
              setBusy(true);
              void publishCampaignAssets(campaign.id, {
                asset_ids: selectedAssets,
                destination_id: destinationId || undefined,
              })
                .then((res) => {
                  setCampaign(res.campaign);
                  setStep(10);
                })
                .catch((err) => setError(err instanceof ApiClientError ? err.message : "Publish failed"))
                .finally(() => setBusy(false));
            }}
          >
            {busy ? "Publishing…" : `Publish ${selectedAssets.length} selected`}
          </button>
        </div>
      ) : null}

      {campaign && step === 10 ? (
        <div className="surface-card p-4">
          <h3 className="h5">Verification</h3>
          <p className="text-muted">A link is verified only when the source page exists and the target href is present.</p>
          <button
            type="button"
            className="btn btn-accent"
            disabled={busy}
            onClick={() => {
              setBusy(true);
              void verifyCampaignBacklinks(campaign.id)
                .then((res) => {
                  setCampaign(res.campaign);
                  setStep(11);
                })
                .catch((err) => setError(err instanceof ApiClientError ? err.message : "Verify failed"))
                .finally(() => setBusy(false));
            }}
          >
            {busy ? "Verifying…" : "Verify backlinks"}
          </button>
          {backlinks.length > 0 ? (
            <ul className="mt-3 mb-0">
              {backlinks.slice(0, 8).map((b) => (
                <li key={b.id}>
                  {b.status}: {b.source_domain} → {b.anchor_text}
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}

      {campaign && step === 11 ? (
        <div className="surface-card p-4">
          <h3 className="h5">Monitoring</h3>
          <p className="mb-2">
            Progress {campaign.progress_percent}% · Verified {campaign.counts.verified_backlinks} · Lost{" "}
            {campaign.counts.lost_backlinks} · Broken {campaign.counts.broken_backlinks} · Referring domains{" "}
            {campaign.counts.referring_domains}
          </p>
          <p className="small text-muted">{campaign.disclosure}</p>
          <button type="button" className="btn btn-accent" onClick={() => router.push(`/parasite-seo/campaigns/${campaign.id}`)}>
            Open campaign dashboard
          </button>
        </div>
      ) : null}
    </PageScaffold>
  );
}

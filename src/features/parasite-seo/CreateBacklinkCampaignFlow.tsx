"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { PageScaffold } from "@/components/layout/PageScaffold";
import { ErrorState, LoadingState } from "@/components/ui/AsyncState";
import { useProject } from "@/context/ProjectContext";
import { ApiClientError } from "@/services/api-client";
import {
  analyzeBacklinkCampaign,
  autoCreateBacklinkCampaign,
  type CampaignPlan,
} from "@/services/backlink-campaign-service";

export function CreateBacklinkCampaignFlow() {
  const router = useRouter();
  const params = useSearchParams();
  const { selectedId, projects } = useProject();
  const projectFromQuery = params.get("project");
  const jobId = params.get("job") || undefined;
  const projectId = projectFromQuery || (selectedId !== "all" ? selectedId : projects[0]?.id) || "";

  const [plan, setPlan] = useState<CampaignPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [customize, setCustomize] = useState(false);
  const [showPlan, setShowPlan] = useState(false);
  const [tier1, setTier1] = useState(5);
  const [tier2, setTier2] = useState(10);
  const [cloud, setCloud] = useState(3);
  const [pr, setPr] = useState(1);
  const [outreach, setOutreach] = useState(10);

  useEffect(() => {
    if (!projectId) {
      setLoading(false);
      return;
    }
    void (async () => {
      setLoading(true);
      try {
        const data = await analyzeBacklinkCampaign({ project_id: projectId, job_id: jobId });
        setPlan(data);
        setTier1(Number(data.blueprint.tier1 ?? 5));
        setTier2(Number(data.blueprint.tier2 ?? 10));
        setCloud(Number(data.blueprint.cloud ?? 3));
        setPr(Number(data.blueprint.pr ?? 1));
        setOutreach(Number(data.blueprint.outreach ?? 10));
      } catch (err) {
        setError(err instanceof ApiClientError ? err.message : "Unable to analyze project");
      } finally {
        setLoading(false);
      }
    })();
  }, [projectId, jobId]);

  async function createCampaign() {
    if (!projectId) return;
    setBusy(true);
    setError(null);
    try {
      const result = await autoCreateBacklinkCampaign({
        project_id: projectId,
        job_id: jobId,
        public_page_id: plan?.target?.public_page_id || undefined,
        blueprint: { tier1, tier2, cloud, pr, outreach, max_tier_depth: 2 },
        generate: true,
        mock_mode: true,
      });
      router.push(`/parasite-seo/campaigns/${result.campaign.id}`);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to create campaign");
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
        <LoadingState label="Analyzing project…" />
      </PageScaffold>
    );
  }

  const keyword = String(plan?.intelligence?.primary_keyword || plan?.target?.primary_keyword || "—");

  return (
    <PageScaffold
      actions={
        <Link href="/parasite-seo/campaigns/new?wizard=1" className="btn btn-ghost">
          Advanced wizard
        </Link>
      }
    >
      <div className="surface-card p-4 mb-4">
        <h2 className="section-title mb-1">Create backlink campaign</h2>
        <p className="text-muted small mb-0">
          The engine analyzes this project and proposes an authorized campaign. Publishing stays on destinations you
          control. Search engines independently determine crawling, indexing, ranking, and link treatment.
        </p>
      </div>

      {error ? <div className="alert alert-danger">{error}</div> : null}

      <div className="surface-card p-4 mb-4">
        <div className="row g-3">
          <div className="col-md-6">
            <div className="small text-muted">Project</div>
            <div className="fw-semibold">{plan?.project.name}</div>
          </div>
          <div className="col-md-6">
            <div className="small text-muted">Target</div>
            <code className="small">{plan?.target?.url || "No published page yet — publish the money page first."}</code>
          </div>
          <div className="col-md-6">
            <div className="small text-muted">Primary keyword</div>
            <div>{keyword}</div>
          </div>
          <div className="col-md-6">
            <div className="small text-muted">AI recommended strategy</div>
            <div className="fw-semibold">{plan?.strategy.label || plan?.strategy.strategy_type}</div>
            <div className="small text-muted">{plan?.strategy.reason}</div>
          </div>
        </div>
      </div>

      <div className="row g-3 mb-4">
        {[
          ["Tier 1", tier1],
          ["Tier 2", tier2],
          ["Cloud", cloud],
          ["PR", pr],
          ["Outreach", outreach],
        ].map(([label, value]) => (
          <div className="col" key={String(label)}>
            <div className="surface-card p-3 text-center">
              <div className="small text-muted">{label}</div>
              <div className="h4 mb-0">{value}</div>
            </div>
          </div>
        ))}
      </div>

      {customize ? (
        <div className="surface-card p-4 mb-4">
          <h3 className="h6">Customize campaign</h3>
          <div className="row g-2">
            {(
              [
                ["Tier 1", tier1, setTier1],
                ["Tier 2", tier2, setTier2],
                ["Cloud", cloud, setCloud],
                ["PR", pr, setPr],
                ["Outreach", outreach, setOutreach],
              ] as const
            ).map(([label, value, setter]) => (
              <div className="col-md-2" key={label}>
                <label className="form-label">{label}</label>
                <input
                  className="form-control"
                  type="number"
                  min={0}
                  max={40}
                  value={value}
                  onChange={(e) => setter(Number(e.target.value))}
                />
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {showPlan ? (
        <div className="surface-card p-4 mb-4">
          <h3 className="h6">AI plan</h3>
          <p className="small">{plan?.size_reason}</p>
          <div className="small text-muted mb-2">Supporting topics</div>
          <ol>
            {((plan?.intelligence.supporting_topics as string[]) || []).map((topic) => (
              <li key={topic}>{topic}</li>
            ))}
          </ol>
          <div className="small text-muted mb-1">Link groups</div>
          <ul>
            {(plan?.link_groups || []).map((g) => (
              <li key={g.id}>
                {g.name} — T{g.tier || "—"} ({g.planned})
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="d-flex flex-wrap gap-2">
        <button type="button" className="btn btn-ghost" onClick={() => setShowPlan((v) => !v)}>
          {showPlan ? "Hide AI plan" : "View AI plan"}
        </button>
        <button type="button" className="btn btn-ghost" onClick={() => setCustomize((v) => !v)}>
          Customize
        </button>
        <button type="button" className="btn btn-accent" disabled={busy || !plan?.target} onClick={() => void createCampaign()}>
          {busy ? "Creating…" : "Create campaign"}
        </button>
      </div>
    </PageScaffold>
  );
}

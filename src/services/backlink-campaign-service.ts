import { apiGetData, apiMutateData } from "@/services/api-client";

export type CampaignCounts = {
  assets: number;
  tier1: number;
  tier2: number;
  cloud: number;
  pr: number;
  published: number;
  verified_backlinks: number;
  lost_backlinks: number;
  broken_backlinks: number;
  planned_backlinks: number;
  referring_domains: number;
  outreach: number;
  internal_links?: number;
  mock_backlinks?: number;
};

export type CampaignAsset = {
  id: string;
  campaign_id: string;
  content_id: string | null;
  master_content_id: string | null;
  destination_id: string | null;
  title: string;
  asset_type: string;
  link_group?: string | null;
  tier: number;
  topic: string | null;
  variant_angle: string | null;
  relevance_score?: number | null;
  is_mock?: boolean;
  status: string;
  source_url: string | null;
  target_url: string | null;
  parent_asset_id: string | null;
  anchor_text: string | null;
  link_attribute: string | null;
  placement: string | null;
  quality_score: number | null;
  seo_score: number | null;
  meta: Record<string, unknown>;
};

export type CampaignBacklink = {
  id: string;
  campaign_id: string;
  asset_id: string | null;
  source_url: string;
  source_domain: string;
  target_url: string;
  target_content_id: string | null;
  anchor_text: string;
  attribute: string;
  tier: number;
  source_type: string;
  link_kind?: string;
  is_mock?: boolean;
  indexed_status?: string;
  status: string;
  first_seen: string | null;
  last_seen: string | null;
  last_checked_at: string | null;
  notes: string | null;
};

export type OutreachProspect = {
  id: string;
  campaign_id: string;
  website: string;
  contact_name: string | null;
  email: string | null;
  topic: string | null;
  relevance_score: number | null;
  status: string;
  draft_subject: string | null;
  draft_body: string | null;
  notes: string | null;
};

export type CampaignGraph = {
  nodes: Array<{
    id: string;
    label: string;
    type: string;
    tier?: number;
    status: string;
    source_url?: string | null;
    domain?: string | null;
  }>;
  edges: Array<{
    from: string;
    to: string;
    label?: string | null;
    kind: string;
    status?: string;
  }>;
};

export type BacklinkCampaign = {
  id: string;
  project_id: string;
  name: string;
  strategy_type: string;
  status: string;
  wizard_step: number;
  target_url: string | null;
  target_content_id: string | null;
  target_public_page_id: string | null;
  primary_keyword: string | null;
  secondary_keywords: string[];
  country: string | null;
  language: string | null;
  niche: string | null;
  target_audience: string | null;
  blueprint: Record<string, number>;
  settings: Record<string, unknown>;
  disclosure: string;
  bucket_id: string | null;
  progress_percent: number;
  mock_mode?: boolean;
  approved_at?: string | null;
  archived_at?: string | null;
  parasite_job_id?: string | null;
  intelligence?: Record<string, unknown>;
  counts: CampaignCounts;
  created_at: string | null;
  updated_at: string | null;
  assets?: CampaignAsset[];
  backlinks?: CampaignBacklink[];
  prospects?: OutreachProspect[];
  graph?: CampaignGraph;
  anchor_distribution?: Array<{ anchor: string; count: number; percent: number }>;
  report?: Record<string, unknown>;
  link_groups?: Array<{ id: string; name: string; tier: number; total: number; done: number; progress: number; status: string }>;
  logs?: Array<{ id: string; level: string; message: string; created_at: string | null }>;
  tasks?: Array<{ id: string; group: string | null; status: string; progress: number; error: string | null }>;
  media_usage?: Array<{ media_id: string; usage_count: number; asset_ids: string[] }>;
};

export type TargetOption = {
  public_page_id: string;
  content_id: string;
  title: string;
  slug: string;
  url: string;
  seo_score: number | null;
  quality_score: number | null;
  status: string;
  published_at: string | null;
};

export type StrategyTemplate = {
  id: string;
  name: string;
  strategy_type: string;
  blueprint: Record<string, number>;
  is_system: boolean;
};

export type ContentBucket = {
  id: string;
  project_id?: string;
  name: string;
  niche: string | null;
  topics: string[];
  keywords: string[];
};

export type PublishingDestination = {
  id: string;
  project_id: string;
  name: string;
  provider_type: string;
  base_url: string | null;
  configuration: Record<string, unknown>;
  is_active: boolean;
  test_status: string | null;
  authorization_status?: string;
  last_tested_at: string | null;
};

const BASE = "/api/v1/parasite-seo/backlink-campaigns";

export async function listBacklinkCampaigns(projectId?: string) {
  const data = await apiGetData<{ items: BacklinkCampaign[] }>(BASE, {
    project_id: projectId,
  });
  return data.items;
}

export async function getBacklinkCampaign(id: string) {
  return apiGetData<BacklinkCampaign>(`${BASE}/${id}`);
}

export async function createBacklinkCampaign(body: Record<string, unknown>) {
  return apiMutateData<BacklinkCampaign>(BASE, "POST", body);
}

export async function updateBacklinkCampaign(id: string, body: Record<string, unknown>) {
  return apiMutateData<BacklinkCampaign>(`${BASE}/${id}`, "PATCH", body);
}

export async function createDemoBacklinkCampaign(projectId: string) {
  return apiMutateData<BacklinkCampaign>(`${BASE}/demo?project_id=${encodeURIComponent(projectId)}`, "POST");
}

export async function listCampaignTargets(projectId: string) {
  const data = await apiGetData<{ items: TargetOption[] }>(`${BASE}/targets`, {
    project_id: projectId,
  });
  return data.items;
}

export async function listStrategyTemplates(projectId: string) {
  const data = await apiGetData<{ items: StrategyTemplate[] }>(`${BASE}/strategies`, {
    project_id: projectId,
  });
  return data.items;
}

export async function saveStrategyTemplate(body: {
  project_id: string;
  name: string;
  strategy_type: string;
  blueprint: Record<string, number>;
}) {
  return apiMutateData<StrategyTemplate>(`${BASE}/strategies`, "POST", body);
}

export async function listContentBuckets(projectId: string) {
  const data = await apiGetData<{ items: ContentBucket[] }>(`${BASE}/buckets`, {
    project_id: projectId,
  });
  return data.items;
}

export async function createContentBucket(body: {
  project_id: string;
  name: string;
  topics?: string[];
  keywords?: string[];
  niche?: string;
}) {
  return apiMutateData<ContentBucket>(`${BASE}/buckets`, "POST", body);
}

export async function listPublishingDestinations(projectId: string) {
  const data = await apiGetData<{ items: PublishingDestination[] }>(`${BASE}/destinations`, {
    project_id: projectId,
  });
  return data.items;
}

export async function createPublishingDestination(body: {
  project_id: string;
  name: string;
  provider_type: string;
  base_url?: string;
  configuration?: Record<string, unknown>;
}) {
  return apiMutateData<PublishingDestination>(`${BASE}/destinations`, "POST", body);
}

export async function testPublishingDestination(id: string) {
  return apiMutateData<PublishingDestination & { test_result: Record<string, unknown> }>(
    `${BASE}/destinations/${id}/test`,
    "POST",
  );
}

export async function generateCampaignAssets(id: string) {
  return apiMutateData<{ created: number; campaign: BacklinkCampaign }>(`${BASE}/${id}/generate-assets`, "POST");
}

export async function publishCampaignAssets(id: string, body?: { asset_ids?: string[]; destination_id?: string }) {
  return apiMutateData<{ published: number; campaign: BacklinkCampaign }>(`${BASE}/${id}/publish`, "POST", body ?? {});
}

export async function verifyCampaignBacklinks(id: string, body?: { backlink_ids?: string[] }) {
  return apiMutateData<{
    verified: number;
    lost: number;
    broken: number;
    campaign: BacklinkCampaign;
  }>(`${BASE}/${id}/verify`, "POST", body ?? {});
}

export async function updateOutreachProspect(id: string, body: Record<string, unknown>) {
  return apiMutateData<OutreachProspect>(`${BASE}/prospects/${id}`, "PATCH", body);
}

export async function analyzeBacklinkCampaign(params: {
  project_id: string;
  job_id?: string;
  public_page_id?: string;
}) {
  return apiGetData<CampaignPlan>(`${BASE}/analyze`, params);
}

export type CampaignPlan = {
  project: { id: string; name: string };
  job_id: string | null;
  target: {
    public_page_id: string | null;
    title: string;
    url: string;
    primary_keyword: string;
    seo_score: number | null;
    content_score: number | null;
    status: string;
  } | null;
  intelligence: Record<string, unknown>;
  strategy: { strategy_type: string; label: string; reason: string; blueprint: Record<string, number> };
  blueprint: Record<string, number>;
  size_reason: string;
  link_groups: Array<{ id: string; name: string; tier: number; planned: number }>;
  destinations: PublishingDestination[];
  disclosure: string;
};

export async function autoCreateBacklinkCampaign(body: {
  project_id: string;
  job_id?: string;
  public_page_id?: string;
  blueprint?: Record<string, number>;
  generate?: boolean;
  mock_mode?: boolean;
}) {
  return apiMutateData<{ created: number; campaign: BacklinkCampaign; plan: CampaignPlan }>(`${BASE}/auto`, "POST", body);
}

export async function approveBacklinkCampaign(id: string) {
  return apiMutateData<BacklinkCampaign>(`${BASE}/${id}/approve`, "POST");
}

export async function startBacklinkCampaign(id: string) {
  return apiMutateData<{ published: number; verified: number; campaign: BacklinkCampaign }>(`${BASE}/${id}/start`, "POST");
}

export async function retryFailedCampaignAssets(id: string) {
  return apiMutateData<{ published: number; campaign: BacklinkCampaign }>(`${BASE}/${id}/retry-failed`, "POST");
}

export async function duplicateBacklinkCampaign(id: string) {
  return apiMutateData<BacklinkCampaign>(`${BASE}/${id}/duplicate`, "POST");
}

export async function archiveBacklinkCampaign(id: string) {
  return apiMutateData<BacklinkCampaign>(`${BASE}/${id}/archive`, "POST");
}

export async function listCampaignLogs(id: string) {
  const data = await apiGetData<{ items: Array<{ id: string; level: string; message: string; created_at: string | null }> }>(
    `${BASE}/${id}/logs`,
  );
  return data.items;
}

export async function listProjectBacklinks(projectId: string, filters?: Record<string, string | number | undefined>) {
  return apiGetData<{
    items: CampaignBacklink[];
    total_backlinks: number;
    verified: number;
    referring_domains: number;
  }>(`${BASE}/project-backlinks`, { project_id: projectId, ...filters });
}

export async function getProjectBacklinkReport(projectId: string) {
  return apiGetData<Record<string, unknown>>(`${BASE}/project-report`, { project_id: projectId });
}

export function campaignReportUrl(id: string, format: "json" | "csv" | "pdf" = "json") {
  return `${BASE}/${id}/report?format=${format}`;
}

export const STRATEGY_OPTIONS = [
  { value: "single_asset", label: "Single asset", description: "One authorized content asset → target page" },
  { value: "multi_asset", label: "Multi-asset", description: "Several assets each linking to the target" },
  { value: "tiered_network", label: "Tiered content network", description: "Tier 1 → target, Tier 2 → Tier 1" },
  { value: "cloud_network", label: "Cloud content network", description: "Authorized cloud pages → target" },
  { value: "digital_pr", label: "Digital PR", description: "Research/stats assets designed for citations" },
  { value: "authorized_outreach", label: "Authorized outreach", description: "Prospects → approved outreach only" },
  { value: "hybrid", label: "Hybrid tiered network", description: "Web + supporting + optional cloud/PR on authorized destinations" },
] as const;

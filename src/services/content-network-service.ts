import { apiGetData, apiMutateData } from "@/services/api-client";

export type NetworkOverview = {
  project_id: string;
  total_pages: number;
  total_internal_links: number;
  orphan_pages: number;
  broken_links: number;
  pending_suggestions: number;
  link_health_score: number;
  average_seo_score: number | null;
  nodes: NetworkNode[];
  edges: NetworkEdge[];
  orphans: NetworkNode[];
  broken: BrokenLink[];
  anchor_diversity: Array<{
    target_content_id: string;
    target_title: string | null;
    anchor_count: number;
    unique_anchors: number;
    recommendation: string;
  }>;
  terminology: Record<string, string>;
};

export type NetworkNode = {
  content_id: string;
  page_id: string;
  title: string;
  slug: string;
  public_url: string;
  seo_score: number | null;
  incoming_links: number;
  outgoing_links: number;
  orphan: boolean;
  link_density: string;
  status: string;
};

export type NetworkEdge = {
  id: string;
  source_content_id: string;
  target_content_id: string;
  anchor_text: string;
  target_url: string;
  status: string;
};

export type BrokenLink = {
  id: string;
  source_content_id: string;
  source_title: string | null;
  target_url: string;
  anchor_text: string;
  status: string;
  reason: string;
};

export type LinkSuggestion = {
  id: string;
  project_id: string | null;
  source_content_id: string;
  target_content_id: string;
  source_title: string | null;
  target_title: string | null;
  anchor_text: string;
  target_path: string;
  reason: string | null;
  relevance_score: number | null;
  confidence_score: number | null;
  placement: string | null;
  context: string | null;
  suggestion_type: string;
  status: string;
};

export type LinkSettings = {
  automatic_internal_linking: boolean;
  min_relevance_score: number;
  max_new_links_per_article: number;
  max_links_to_same_target: number;
  max_links_per_section: number;
  related_content_limit: number;
};

export async function getContentNetwork(projectId: string) {
  return apiGetData<NetworkOverview>(`/api/v1/parasite-seo/link-network?project_id=${projectId}`);
}

export async function analyzeContentNetwork(projectId: string, useAi = true) {
  return apiMutateData<{ run: Record<string, unknown>; overview: NetworkOverview }>(
    "/api/v1/parasite-seo/link-network/analyze",
    "POST",
    { project_id: projectId, use_ai: useAi },
  );
}

export async function listLinkSuggestions(projectId?: string, status?: string) {
  return apiGetData<{ items: LinkSuggestion[] }>("/api/v1/parasite-seo/link-suggestions", {
    project_id: projectId,
    status,
  });
}

export async function approveLinkSuggestion(id: string) {
  return apiMutateData<Record<string, unknown>>(`/api/v1/parasite-seo/link-suggestions/${id}/approve`, "POST");
}

export async function rejectLinkSuggestion(id: string) {
  return apiMutateData<LinkSuggestion>(`/api/v1/parasite-seo/link-suggestions/${id}/reject`, "POST");
}

export async function updateLinkSuggestion(
  id: string,
  payload: { anchor_text?: string; placement?: string; context?: string },
) {
  return apiMutateData<LinkSuggestion>(`/api/v1/parasite-seo/link-suggestions/${id}`, "PATCH", payload);
}

export async function removeBrokenLink(linkId: string) {
  return apiMutateData<{ id: string; status: string }>(
    `/api/v1/parasite-seo/link-suggestions/broken/${linkId}`,
    "DELETE",
  );
}

export async function getLinkSettings(projectId: string) {
  return apiGetData<LinkSettings>(`/api/v1/parasite-seo/link-network/${projectId}/settings`);
}

export async function updateLinkSettings(projectId: string, payload: Partial<LinkSettings>) {
  return apiMutateData<LinkSettings>(`/api/v1/parasite-seo/link-network/${projectId}/settings`, "PATCH", payload);
}

export async function getOrphanOpportunities(projectId: string, contentId: string) {
  return apiGetData<
    Array<{
      source_content_id: string;
      source_title: string;
      target_content_id: string;
      target_title: string;
      relevance_score: number;
      recommended_anchor: string;
    }>
  >(`/api/v1/parasite-seo/link-network/orphans/${contentId}/opportunities?project_id=${projectId}`);
}

export async function createOrphanSuggestion(payload: {
  project_id: string;
  source_content_id: string;
  target_content_id: string;
  anchor_text?: string;
}) {
  return apiMutateData<LinkSuggestion>("/api/v1/parasite-seo/link-network/suggestions", "POST", payload);
}

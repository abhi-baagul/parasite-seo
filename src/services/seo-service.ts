import { apiGetData, apiMutateData } from "@/services/api-client";

export type SeoChecklistItem = {
  key: string;
  label: string;
  status: "PASS" | "WARNING" | "FAIL" | string;
  detail?: string | null;
};

export type SeoReport = {
  label?: string;
  disclaimer?: string;
  overall_score: number;
  structure_score: number;
  keyword_score: number;
  readability_score: number;
  metadata_score: number;
  link_score: number;
  media_score: number;
  issues: string[];
  recommendations: string[];
  checklist: SeoChecklistItem[];
  keywords?: Record<string, unknown>;
};

export type MetadataPackage = {
  title_options: Array<{
    title: string;
    character_count?: number;
    keyword_position?: string;
    clarity_score?: number;
    intent_match?: number;
  }>;
  meta_options: Array<{
    meta_description: string;
    character_count?: number;
    primary_keyword_present?: boolean;
    cta_presence?: boolean;
  }>;
  slug?: string | null;
  og_title?: string | null;
  og_description?: string | null;
  twitter_title?: string | null;
  twitter_description?: string | null;
  selected_seo_title?: string | null;
  selected_meta_description?: string | null;
};

export type TagRow = { id: string; name: string; source: string; is_accepted: boolean };
export type LinkSuggestion = {
  id: string;
  target_content_id: string;
  source_section?: string | null;
  anchor_text: string;
  target_path: string;
  reason?: string | null;
  status: string;
};
export type ExternalRef = {
  id: string;
  url: string | null;
  anchor_suggestion: string;
  reason?: string | null;
  source_type: string;
  requires_verification: boolean;
  status: string;
};
export type MediaSuggestion = {
  id: string;
  content_id: string;
  media_type: string;
  placement?: string | null;
  purpose?: string | null;
  description?: string | null;
  generation_prompt?: string | null;
  alt_text?: string | null;
  caption?: string | null;
  suggested_filename?: string | null;
  status: string;
  embed_url?: string | null;
};

export async function analyzeSeo(contentId: string) {
  return apiMutateData<SeoReport>(`/api/v1/content/${contentId}/seo/analyze`, "POST");
}

export async function getSeo(contentId: string) {
  return apiGetData<SeoReport>(`/api/v1/content/${contentId}/seo`);
}

export async function runKeywordAnalysis(contentId: string) {
  return apiMutateData<Record<string, unknown>>(`/api/v1/content/${contentId}/keyword-analysis`, "POST");
}

export async function getKeywordAnalysis(contentId: string) {
  return apiGetData<Record<string, unknown>>(`/api/v1/content/${contentId}/keyword-analysis`);
}

export async function generateMetadata(contentId: string) {
  return apiMutateData<{ metadata: MetadataPackage; ai_run_id: string }>(
    `/api/v1/content/${contentId}/seo/generate-metadata`,
    "POST",
  );
}

export async function selectMetadata(
  contentId: string,
  payload: {
    seo_title?: string;
    meta_description?: string;
    slug?: string;
    canonical_url?: string | null;
    og_title?: string | null;
    og_description?: string | null;
  },
) {
  return apiMutateData<Record<string, unknown>>(`/api/v1/content/${contentId}/seo/select-metadata`, "POST", payload);
}

export async function generateTags(contentId: string) {
  return apiMutateData<{ tags: TagRow[]; categories: TagRow[]; ai_run_id: string }>(
    `/api/v1/content/${contentId}/seo/generate-tags`,
    "POST",
  );
}

export async function listTags(contentId: string) {
  return apiGetData<TagRow[]>(`/api/v1/content/${contentId}/tags`);
}

export async function decideTag(contentId: string, tagId: string, status: "approved" | "rejected") {
  return apiMutateData(`/api/v1/content/${contentId}/tags/${tagId}/decision`, "POST", { status });
}

export async function listCategories(contentId: string) {
  return apiGetData<TagRow[]>(`/api/v1/content/${contentId}/categories`);
}

export async function decideCategory(contentId: string, categoryId: string, status: "approved" | "rejected") {
  return apiMutateData(`/api/v1/content/${contentId}/categories/${categoryId}/decision`, "POST", { status });
}

export async function suggestInternalLinks(contentId: string) {
  return apiMutateData<{ suggestions: LinkSuggestion[]; created: number }>(
    `/api/v1/content/${contentId}/internal-link-suggestions`,
    "POST",
  );
}

export async function listInternalLinks(contentId: string) {
  return apiGetData<LinkSuggestion[]>(`/api/v1/content/${contentId}/internal-link-suggestions`);
}

export async function decideInternalLink(contentId: string, id: string, status: "approved" | "rejected") {
  return apiMutateData(`/api/v1/content/${contentId}/internal-link-suggestions/${id}/decision`, "POST", { status });
}

export async function suggestExternalRefs(contentId: string) {
  return apiMutateData<{ references: ExternalRef[] }>(`/api/v1/content/${contentId}/external-references`, "POST");
}

export async function listExternalRefs(contentId: string) {
  return apiGetData<ExternalRef[]>(`/api/v1/content/${contentId}/external-references`);
}

export async function decideExternalRef(
  contentId: string,
  id: string,
  status: "approved" | "rejected",
  url?: string,
) {
  return apiMutateData(`/api/v1/content/${contentId}/external-references/${id}/decision`, "POST", {
    status,
    url: url ?? null,
  });
}

export async function analyzeLinks(contentId: string) {
  return apiMutateData<Record<string, unknown>>(`/api/v1/content/${contentId}/links/analyze`, "POST");
}

export async function suggestTargetLink(
  contentId: string,
  payload: { target_url: string; anchor_text: string; link_attribute?: string },
) {
  return apiMutateData<{
    target_url: string;
    anchor_text: string;
    link_attribute: string;
    suggested_phrase: string;
    note: string;
  }>(`/api/v1/content/${contentId}/links/suggest`, "POST", payload);
}

export async function insertTargetLink(
  contentId: string,
  payload: {
    target_url: string;
    anchor_text: string;
    link_attribute?: string;
    placement_phrase?: string;
  },
) {
  return apiMutateData<{ link: Record<string, string>; content: string }>(
    `/api/v1/content/${contentId}/links/insert`,
    "POST",
    payload,
  );
}

export async function generateMediaPlan(contentId: string) {
  return apiMutateData<{ media: MediaSuggestion[]; ai_run_id: string; created: number }>(
    `/api/v1/content/${contentId}/seo/generate-media-plan`,
    "POST",
  );
}

export async function listMediaSuggestions(contentId: string) {
  return apiGetData<MediaSuggestion[]>(`/api/v1/content/${contentId}/media`);
}

export async function decideMedia(contentId: string, id: string, status: "approved" | "rejected") {
  return apiMutateData(`/api/v1/content/${contentId}/media/${id}/decision`, "POST", { status });
}

export async function generateAllSeoAssets(contentId: string) {
  return apiMutateData<Record<string, unknown>>(`/api/v1/content/${contentId}/seo/generate-all`, "POST");
}

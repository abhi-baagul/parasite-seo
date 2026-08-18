import { apiGetData, apiGetList, apiMutateData } from "@/services/api-client";
import type { ContentDto } from "@/services/types";

export type StudioOutlineItem = { level: number; text: string; anchor: string };
export type CompletenessItem = { key: string; label: string; status: "complete" | "warning" | "missing" | string };

export type StudioPayload = {
  content: ContentDto;
  metadata: {
    seo_title: string | null;
    meta_description: string | null;
    slug: string | null;
    canonical_url: string | null;
    og_title: string | null;
    og_description: string | null;
    og_image: string | null;
    twitter_title: string | null;
    twitter_description: string | null;
    title_options: string[];
    meta_options: string[];
  };
  keywords: Record<string, unknown> | null;
  tags: Array<{ id: string; name: string; is_accepted: boolean }>;
  categories: Array<{ id: string; name: string; is_accepted: boolean }>;
  links: Array<{
    id: string;
    target_url: string;
    anchor_text: string;
    placement_description: string | null;
    link_attribute: string;
    status: string;
  }>;
  media: Array<{
    id: string;
    media_type: string;
    url: string | null;
    alt_text: string | null;
    caption: string | null;
    source: string | null;
    license_information: string | null;
    status: string;
    storage_key: string | null;
  }>;
  media_suggestions: Array<Record<string, unknown>>;
  quality: Array<{
    id: string;
    check_type: string;
    status: string;
    score: number | null;
    issues: unknown;
    recommendations: unknown;
    created_at: string | null;
  }>;
  seo_analysis: Record<string, unknown> | null;
  research: { exists: boolean; version_number: number | null; payload: Record<string, unknown> | null };
  references: Array<{
    id: string;
    title: string;
    url: string | null;
    source_type: string;
    status: string;
    notes: string | null;
    requires_verification?: boolean;
  }>;
  ai_runs: Array<{
    id: string;
    agent_type: string;
    status: string;
    model: string | null;
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    estimated_cost: number | null;
    duration_ms: number | null;
    started_at: string | null;
    completed_at: string | null;
    input_summary: string | null;
  }>;
  versions: Array<{
    id: string;
    version_number: number;
    change_summary: string | null;
    source: string;
    created_by: string | null;
    created_at: string | null;
    content_length: number;
  }>;
  outline: StudioOutlineItem[];
  stats: {
    word_count: number;
    character_count: number;
    reading_time_minutes: number;
    reading_speed_wpm: number;
  };
  completeness: CompletenessItem[];
  status: string;
};

export async function getStudio(contentId: string) {
  return apiGetData<StudioPayload>(`/api/v1/content/${contentId}/studio`);
}

export async function duplicateContent(contentId: string) {
  return apiMutateData<ContentDto>(`/api/v1/content/${contentId}/duplicate`, "POST");
}

export async function restoreVersion(contentId: string, versionId: string) {
  return apiMutateData<{
    content: ContentDto;
    restored_from: number;
    new_version: { id: string; version_number: number; source: string };
  }>(`/api/v1/content/${contentId}/versions/${versionId}/restore`, "POST");
}

export async function compareVersions(contentId: string, leftVersionId: string, rightVersionId: string) {
  return apiMutateData<{
    left: { id: string; version_number: number; content: string };
    right: { id: string; version_number: number; content: string };
    unified_diff: string[];
    ratio: number;
  }>(`/api/v1/content/${contentId}/versions/compare`, "POST", {
    left_version_id: leftVersionId,
    right_version_id: rightVersionId,
  });
}

export async function sectionEdit(
  contentId: string,
  payload: {
    selected_html: string;
    action: string;
    tone?: string;
    instruction?: string;
    accept?: boolean;
    full_html?: string;
  },
) {
  return apiMutateData<{
    rewritten_html: string;
    notes: string | null;
    accepted: boolean;
    content?: ContentDto;
  }>(`/api/v1/content/${contentId}/ai/section-edit`, "POST", payload);
}

export function exportUrl(contentId: string, format: "html" | "markdown" | "txt" | "pdf" | "doc" | "csv") {
  const base = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "";
  return `${base}/api/v1/content/${contentId}/export/${format}`;
}

export async function downloadExport(
  contentId: string,
  format: "html" | "markdown" | "txt" | "pdf" | "doc" | "csv",
) {
  const headers: HeadersInit = { Accept: "*/*" };
  if (typeof window !== "undefined") {
    const token = window.localStorage.getItem("ps_access_token");
    if (token) headers.Authorization = `Bearer ${token}`;
  }
  const response = await fetch(exportUrl(contentId, format), { cache: "no-store", headers });
  if (!response.ok) {
    throw new Error(`Export failed (${response.status})`);
  }
  const blob = await response.blob();
  const disposition = response.headers.get("content-disposition") || "";
  const match = /filename="?([^"]+)"?/i.exec(disposition);
  const ext = format === "markdown" ? "md" : format;
  const filename = match?.[1] || `export.${ext}`;
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export async function listAssetLibrary(projectId?: string, page = 1, q?: string) {
  return apiGetList<{
    id: string;
    name: string;
    type: string;
    subtype: string;
    project_id: string;
    status: string;
    href: string;
    url?: string | null;
    updated_at: string | null;
  }>("/api/v1/assets/library", { page, page_size: 50, project_id: projectId, q });
}

export async function approveContent(contentId: string) {
  return apiMutateData<ContentDto>(`/api/v1/content/${contentId}`, "PATCH", { status: "approved" });
}

export async function archiveContent(contentId: string) {
  return apiMutateData<ContentDto>(`/api/v1/content/${contentId}`, "PATCH", { status: "archived" });
}

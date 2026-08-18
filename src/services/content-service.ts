import { apiGetData, apiGetList, apiMutateData, apiRequest } from "@/services/api-client";
import type { ContentDto, ContentVersionDto } from "@/services/types";

export type ContentInput = {
  project_id: string;
  campaign_id?: string | null;
  prompt_id?: string | null;
  title: string;
  slug: string;
  content?: string;
  content_type?: string;
  status?: string;
  word_count?: number;
  seo_score?: number | null;
  quality_score?: number | null;
  seo_title?: string | null;
  meta_description?: string | null;
};

export async function listContent(
  projectId?: string,
  page = 1,
  pageSize = 50,
  filters?: { q?: string; status?: string; campaign_id?: string; content_type?: string },
) {
  return apiGetList<ContentDto>("/api/v1/content", {
    page,
    page_size: pageSize,
    project_id: projectId,
    q: filters?.q,
    status: filters?.status,
    campaign_id: filters?.campaign_id,
    content_type: filters?.content_type,
  });
}

export async function getContent(id: string) {
  return apiGetData<ContentDto>(`/api/v1/content/${id}`);
}

export async function createContent(payload: ContentInput) {
  return apiMutateData<ContentDto>("/api/v1/content", "POST", payload);
}

export async function updateContent(id: string, payload: Partial<Omit<ContentInput, "project_id">>) {
  return apiMutateData<ContentDto>(`/api/v1/content/${id}`, "PATCH", payload);
}

export async function deleteContent(id: string) {
  return apiRequest<void>(`/api/v1/content/${id}`, { method: "DELETE" });
}

export async function listContentVersions(contentId: string, page = 1, pageSize = 50) {
  return apiGetList<ContentVersionDto>(`/api/v1/content/${contentId}/versions`, {
    page,
    page_size: pageSize,
  });
}

export async function createContentVersion(
  contentId: string,
  payload: { content: string; change_summary?: string | null },
) {
  return apiMutateData<ContentVersionDto>(`/api/v1/content/${contentId}/versions`, "POST", payload);
}

export async function getContentVersion(contentId: string, versionId: string) {
  return apiGetData<ContentVersionDto>(`/api/v1/content/${contentId}/versions/${versionId}`);
}

import { apiGetData, apiGetList, apiMutateData, apiRequest } from "@/services/api-client";
import type { KeywordDto } from "@/services/types";

export async function listKeywords(projectId?: string, page = 1) {
  return apiGetList<KeywordDto>("/api/v1/keywords", { page, page_size: 50, project_id: projectId });
}

export async function createKeyword(payload: {
  project_id: string;
  keyword: string;
  keyword_type?: string;
  content_asset_id?: string | null;
}) {
  return apiMutateData<KeywordDto>("/api/v1/keywords", "POST", payload);
}

export async function getKeyword(id: string) {
  return apiGetData<KeywordDto>(`/api/v1/keywords/${id}`);
}

export async function updateKeyword(id: string, payload: Partial<{ keyword: string; keyword_type: string }>) {
  return apiMutateData<KeywordDto>(`/api/v1/keywords/${id}`, "PATCH", payload);
}

export async function deleteKeyword(id: string) {
  return apiRequest<void>(`/api/v1/keywords/${id}`, { method: "DELETE" });
}

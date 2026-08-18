import { apiGetData, apiGetList, apiMutateData, apiRequest } from "@/services/api-client";
import type { LinkDto } from "@/services/types";

export type LinkInput = {
  content_asset_id: string;
  target_url: string;
  anchor_text: string;
  placement_description?: string | null;
  link_attribute?: string;
  status?: string;
};

export async function listLinks(opts?: { projectId?: string; contentAssetId?: string; page?: number }) {
  return apiGetList<LinkDto>("/api/v1/links", {
    page: opts?.page ?? 1,
    page_size: 50,
    project_id: opts?.projectId,
    content_asset_id: opts?.contentAssetId,
  });
}

export async function getLink(id: string) {
  return apiGetData<LinkDto>(`/api/v1/links/${id}`);
}

export async function createLink(payload: LinkInput) {
  return apiMutateData<LinkDto>("/api/v1/links", "POST", payload);
}

export async function updateLink(id: string, payload: Partial<Omit<LinkInput, "content_asset_id">>) {
  return apiMutateData<LinkDto>(`/api/v1/links/${id}`, "PATCH", payload);
}

export async function deleteLink(id: string) {
  return apiRequest<void>(`/api/v1/links/${id}`, { method: "DELETE" });
}

import { apiGetData, apiGetList, apiMutateData, apiRequest } from "@/services/api-client";
import type { MediaDto } from "@/services/types";

export type MediaInput = {
  project_id: string;
  content_asset_id?: string | null;
  media_type?: string;
  url?: string | null;
  storage_key?: string | null;
  prompt?: string | null;
  alt_text?: string | null;
  caption?: string | null;
  source?: string | null;
  license_information?: string | null;
  status?: string;
};

export async function listMedia(
  projectId?: string,
  page = 1,
  opts?: { contentAssetId?: string; mediaType?: string },
) {
  return apiGetList<MediaDto>("/api/v1/media", {
    page,
    page_size: 50,
    project_id: projectId,
    content_asset_id: opts?.contentAssetId,
    media_type: opts?.mediaType,
  });
}

export async function getMedia(id: string) {
  return apiGetData<MediaDto>(`/api/v1/media/${id}`);
}

export async function createMedia(payload: MediaInput) {
  return apiMutateData<MediaDto>("/api/v1/media", "POST", payload);
}

export async function updateMedia(id: string, payload: Partial<Omit<MediaInput, "project_id">>) {
  return apiMutateData<MediaDto>(`/api/v1/media/${id}`, "PATCH", payload);
}

export async function deleteMedia(id: string) {
  return apiRequest<void>(`/api/v1/media/${id}`, { method: "DELETE" });
}

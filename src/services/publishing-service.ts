import { apiGetData, apiGetList, apiMutateData, apiRequest } from "@/services/api-client";
import type { PublishedAssetDto, PublishingChannelDto } from "@/services/types";

export type ChannelInput = {
  project_id: string;
  name: string;
  channel_type?: string;
  configuration?: Record<string, unknown>;
  is_active?: boolean;
};

export async function listPublishingChannels(projectId?: string, page = 1) {
  return apiGetList<PublishingChannelDto>("/api/v1/publishing/channels", {
    page,
    page_size: 50,
    project_id: projectId,
  });
}

export async function createPublishingChannel(payload: ChannelInput) {
  return apiMutateData<PublishingChannelDto>("/api/v1/publishing/channels", "POST", payload);
}

export async function getPublishingChannel(id: string) {
  return apiGetData<PublishingChannelDto>(`/api/v1/publishing/channels/${id}`);
}

export async function updatePublishingChannel(id: string, payload: Partial<Omit<ChannelInput, "project_id">>) {
  return apiMutateData<PublishingChannelDto>(`/api/v1/publishing/channels/${id}`, "PATCH", payload);
}

export async function deletePublishingChannel(id: string) {
  return apiRequest<void>(`/api/v1/publishing/channels/${id}`, { method: "DELETE" });
}

export async function listPublishingHistory(projectId?: string, page = 1) {
  return apiGetList<PublishedAssetDto>("/api/v1/publishing/history", {
    page,
    page_size: 50,
    project_id: projectId,
  });
}

export async function getPublishedAsset(id: string) {
  return apiGetData<PublishedAssetDto>(`/api/v1/publishing/${id}`);
}

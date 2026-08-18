import { apiGetData, apiGetList, apiMutateData, apiRequest } from "@/services/api-client";
import type { CampaignDto } from "@/services/types";

export type CampaignInput = {
  name: string;
  description?: string | null;
  status?: string;
  target_country?: string | null;
  language?: string | null;
  default_content_type?: string;
  default_word_count?: number;
};

export async function listCampaigns(projectId: string, page = 1, pageSize = 50) {
  return apiGetList<CampaignDto>(`/api/v1/projects/${projectId}/campaigns`, {
    page,
    page_size: pageSize,
  });
}

export async function getCampaign(id: string) {
  return apiGetData<CampaignDto>(`/api/v1/campaigns/${id}`);
}

export async function createCampaign(projectId: string, payload: CampaignInput) {
  return apiMutateData<CampaignDto>(`/api/v1/projects/${projectId}/campaigns`, "POST", payload);
}

export async function updateCampaign(id: string, payload: Partial<CampaignInput>) {
  return apiMutateData<CampaignDto>(`/api/v1/campaigns/${id}`, "PATCH", payload);
}

export async function deleteCampaign(id: string) {
  return apiRequest<void>(`/api/v1/campaigns/${id}`, { method: "DELETE" });
}

import { apiGetData, apiGetList, apiMutateData } from "@/services/api-client";
import type { AiRunDto } from "@/services/types";

export type ResearchPayload = {
  research: Record<string, unknown> | null;
  version_number: number | null;
  source_note?: string | null;
  exists?: boolean;
  ai_run_id?: string;
  status?: string;
  message?: string;
};

export type StrategyPayload = {
  strategy: Record<string, unknown> | null;
  version_number: number | null;
  exists?: boolean;
  ai_run_id?: string;
  status?: string;
  message?: string;
};

export type OutlineSection = {
  heading: string;
  level: number;
  purpose?: string | null;
  notes?: string | null;
};

export type OutlinePayload = {
  outline: { h1: string; sections: OutlineSection[] } | null;
  version_number: number | null;
  is_approved?: boolean;
  exists?: boolean;
  ai_run_id?: string;
  status?: string;
  message?: string;
};

export type GenerateResult = {
  content_id: string;
  title: string;
  seo_title: string | null;
  meta_description: string | null;
  slug: string;
  content: string;
  word_count: number;
  generation_status: string;
  ai_run_id: string;
};

export async function listAiRuns(projectId?: string, page = 1) {
  return apiGetList<AiRunDto>("/api/v1/ai/runs", { page, page_size: 50, project_id: projectId });
}

export async function getAiRun(id: string) {
  return apiGetData<AiRunDto>(`/api/v1/ai/runs/${id}`);
}

export async function runResearch(contentId: string) {
  return apiMutateData<ResearchPayload>(`/api/v1/content/${contentId}/research`, "POST");
}

export async function getResearch(contentId: string) {
  return apiGetData<ResearchPayload>(`/api/v1/content/${contentId}/research`);
}

export async function runStrategy(contentId: string) {
  return apiMutateData<StrategyPayload>(`/api/v1/content/${contentId}/strategy`, "POST");
}

export async function getStrategy(contentId: string) {
  return apiGetData<StrategyPayload>(`/api/v1/content/${contentId}/strategy`);
}

export async function runOutline(contentId: string) {
  return apiMutateData<OutlinePayload>(`/api/v1/content/${contentId}/outline`, "POST");
}

export async function getOutline(contentId: string) {
  return apiGetData<OutlinePayload>(`/api/v1/content/${contentId}/outline`);
}

export async function approveOutline(
  contentId: string,
  outline?: { h1: string; sections: OutlineSection[] } | null,
) {
  return apiMutateData<OutlinePayload>(`/api/v1/content/${contentId}/outline/approve`, "POST", {
    outline: outline ?? null,
  });
}

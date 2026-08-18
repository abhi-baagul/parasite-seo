import { apiGetData, apiGetList, apiMutateData } from "@/services/api-client";
import type { PromptDto } from "@/services/types";

export type PromptRequirements = {
  topic: string | null;
  main_keyword: string | null;
  secondary_keywords: string[];
  word_count: number | null;
  content_type: string | null;
  intent: string | null;
  tone: string | null;
  audience: string | null;
  country: string | null;
  language: string | null;
  required_headings: string[];
  required_elements: string[];
  cta_requirement: boolean | null;
  offer_information: string | null;
  promotional_information: string | null;
  target_url_if_present: string | null;
  anchor_text_if_present: string | null;
  media_requirements: string[];
  special_instructions: string | null;
  uncertain_fields: string[];
};

export type AnalyzePromptResult = {
  prompt_id: string;
  analysis_id: string;
  ai_run_id: string;
  requirements: PromptRequirements;
  uncertain_fields: string[];
};

export type ConfirmRequirementsResult = {
  prompt_id: string;
  content_id: string;
  requirements: PromptRequirements;
};

export async function listPrompts(projectId?: string, page = 1, pageSize = 50) {
  return apiGetList<PromptDto>("/api/v1/prompts", {
    page,
    page_size: pageSize,
    project_id: projectId,
  });
}

export async function createPrompt(payload: {
  project_id: string;
  campaign_id?: string | null;
  raw_prompt: string;
  status?: string;
}) {
  return apiMutateData<PromptDto>("/api/v1/prompts", "POST", payload);
}

export async function getPrompt(id: string) {
  return apiGetData<PromptDto>(`/api/v1/prompts/${id}`);
}

export async function analyzePrompt(payload: {
  project_id: string;
  campaign_id?: string | null;
  prompt: string;
}) {
  return apiMutateData<AnalyzePromptResult>("/api/v1/content/analyze-prompt", "POST", payload);
}

export async function confirmRequirements(promptId: string, requirements: PromptRequirements) {
  return apiMutateData<ConfirmRequirementsResult>(
    `/api/v1/content/prompts/${promptId}/confirm-requirements`,
    "POST",
    { requirements },
  );
}

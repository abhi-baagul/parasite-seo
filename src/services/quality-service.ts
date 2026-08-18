import { apiGetData, apiMutateData } from "@/services/api-client";

export type SeoCheckResult = {
  report: {
    overall_score: number;
    structure_score: number;
    keyword_coverage_score: number;
    readability_score: number;
    intent_score: number;
    issues: string[];
    recommendations: string[];
  };
  quality_check_id: string;
  ai_run_id: string;
};

export type QualityCheckResult = {
  report: {
    score: number;
    status: "passed" | "needs_review" | "failed";
    issues: string[];
    recommendations: string[];
  };
  quality_check_id: string;
  ai_run_id: string;
};

export type QualityCheckRow = {
  id: string;
  check_type: string;
  score: number | null;
  status: string;
  issues: string[];
  recommendations: string[];
  created_at: string;
};

export type OptimizeResult = {
  suggestions: Array<{ before: string; after: string; reason: string }>;
  ai_run_id: string;
};

export async function runSeoCheck(contentId: string) {
  return apiMutateData<SeoCheckResult>(`/api/v1/content/${contentId}/seo-check`, "POST");
}

export async function runQualityCheck(contentId: string) {
  return apiMutateData<QualityCheckResult>(`/api/v1/content/${contentId}/quality-check`, "POST");
}

export async function listQualityChecks(contentId: string) {
  return apiGetData<QualityCheckRow[]>(`/api/v1/content/${contentId}/quality-checks`);
}

export async function optimizeContent(contentId: string, instructions?: string) {
  return apiMutateData<OptimizeResult>(`/api/v1/content/${contentId}/optimize`, "POST", {
    instructions: instructions ?? null,
  });
}

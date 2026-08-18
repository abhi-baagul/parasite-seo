import { apiGetData, apiGetList } from "@/services/api-client";
import type { AnalyticsOverviewDto } from "@/services/types";

export async function getAnalyticsOverview(projectId?: string) {
  return apiGetData<AnalyticsOverviewDto>("/api/v1/analytics/overview", { project_id: projectId });
}

export async function listAnalytics(projectId?: string, page = 1) {
  return apiGetList("/api/v1/analytics", { page, page_size: 50, project_id: projectId });
}

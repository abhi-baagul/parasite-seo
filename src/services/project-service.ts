import { apiGetData, apiGetList, apiMutateData, apiRequest } from "@/services/api-client";
import type { ProjectDto } from "@/services/types";

export type ProjectInput = {
  name: string;
  description?: string | null;
  niche?: string | null;
  country?: string | null;
  language?: string | null;
  target_audience?: string | null;
  monetization_model?: string | null;
  status?: string;
};

export async function listProjects(page = 1, pageSize = 50) {
  return apiGetList<ProjectDto>("/api/v1/projects", { page, page_size: pageSize });
}

export async function getProject(id: string) {
  return apiGetData<ProjectDto>(`/api/v1/projects/${id}`);
}

export async function createProject(payload: ProjectInput) {
  return apiMutateData<ProjectDto>("/api/v1/projects", "POST", payload);
}

export async function updateProject(id: string, payload: Partial<ProjectInput>) {
  return apiMutateData<ProjectDto>(`/api/v1/projects/${id}`, "PATCH", payload);
}

export async function deleteProject(id: string) {
  return apiRequest<void>(`/api/v1/projects/${id}`, { method: "DELETE" });
}

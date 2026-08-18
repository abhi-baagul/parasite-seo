import { apiMutateData } from "@/services/api-client";
import type { GenerateResult } from "@/services/ai-service";

export async function generateContent(payload: {
  content_id: string;
  temperature?: number;
  max_tokens?: number;
}) {
  return apiMutateData<GenerateResult>("/api/v1/content/generate", "POST", payload);
}

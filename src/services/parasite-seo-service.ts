import { apiGetData, apiMutateData } from "@/services/api-client";

export type ParasiteJob = {
  id: string;
  project_id: string;
  prompt_id: string | null;
  content_id: string | null;
  original_prompt: string;
  advanced_settings: Record<string, unknown>;
  target_link: {
    target_url?: string;
    anchor_text?: string | null;
    link_attribute?: string;
  } | null;
  requirements: Record<string, unknown> | null;
  step_state: Record<string, string>;
  status: string;
  current_step: string;
  error_message: string | null;
  public_slug: string | null;
  public_url: string | null;
  is_public: boolean;
  published_at: string | null;
  optimize_before: string | null;
  optimize_after: string | null;
  web_page?: WebPageSummary | null;
  content: {
    id: string;
    title: string;
    slug: string;
    content: string;
    seo_title: string | null;
    meta_description: string | null;
    word_count: number;
    seo_score: number | null;
    quality_score: number | null;
    status: string;
  } | null;
  media: Array<{
    id: string;
    media_type: string;
    url: string | null;
    alt_text: string | null;
    caption: string | null;
    status: string;
  }>;
  seo_analysis?: Record<string, unknown> | null;
  created_at: string | null;
  updated_at: string | null;
};

export type WebPageSummary = {
  id: string;
  job_id: string;
  content_id: string;
  project_id: string;
  slug: string;
  title: string;
  status: string;
  visibility: string;
  public_url: string | null;
  canonical_url: string | null;
  published_at: string | null;
  content_version_id: string | null;
  published_version_id: string | null;
  has_newer_content: boolean;
  error_message: string | null;
  seo_score: number | null;
  quality_score: number | null;
  created_at: string | null;
  updated_at: string | null;
  preview?: PublicPagePayload;
};

export type PublicPagePayload = {
  slug: string;
  title: string;
  seo_title: string;
  meta_description: string | null;
  canonical_url: string;
  content_html: string;
  published_at: string | null;
  word_count: number;
  category?: string | null;
  tags?: string[];
  featured_image?: {
    id: string;
    media_type: string;
    url: string | null;
    alt_text: string | null;
    caption: string | null;
  } | null;
  images?: Array<{
    id: string;
    media_type: string;
    url: string | null;
    alt_text: string | null;
    caption: string | null;
  }>;
  videos?: Array<{
    id: string;
    media_type: string;
    url: string | null;
    alt_text: string | null;
    caption: string | null;
  }>;
  links: Array<{
    anchor_text: string;
    target_url: string;
    link_attribute: string;
    is_internal?: boolean;
  }>;
  references?: Array<{ title: string; url: string; source_type: string }>;
  related_pages?: Array<{ title: string; slug: string; public_url: string }>;
  target_link?: {
    target_url: string;
    anchor_text: string;
    link_attribute: string;
  } | null;
  faq?: Array<{ question: string; answer: string }>;
  metadata: {
    title: string;
    description: string;
    canonical: string;
    og: {
      title: string;
      description: string;
      image: string | null;
      url: string;
      type: string;
    };
    twitter: {
      card: string;
      title: string;
      description: string;
      image: string | null;
    };
  };
  structured_data: Array<Record<string, unknown>>;
  public_url: string | null;
  status?: string;
  visibility?: string;
};

export async function listParasiteJobs(projectId?: string) {
  return apiGetData<{ items: ParasiteJob[]; stats: Record<string, number> }>("/api/v1/parasite-seo", {
    project_id: projectId,
  });
}

export async function createParasiteJob(payload: {
  project_id: string;
  prompt: string;
  advanced_settings?: Record<string, unknown>;
  target_link?: Record<string, unknown> | null;
}) {
  return apiMutateData<ParasiteJob>("/api/v1/parasite-seo/jobs", "POST", payload);
}

export async function getParasiteJobByContent(contentId: string) {
  return apiGetData<ParasiteJob>(`/api/v1/parasite-seo/jobs/by-content/${contentId}`);
}

export async function getParasiteJob(jobId: string) {
  return apiGetData<ParasiteJob>(`/api/v1/parasite-seo/jobs/${jobId}`);
}

export async function analyzeParasiteJob(jobId: string) {
  return apiMutateData<ParasiteJob>(`/api/v1/parasite-seo/jobs/${jobId}/analyze`, "POST");
}

export async function updateParasiteRequirements(jobId: string, requirements: Record<string, unknown>) {
  return apiMutateData<ParasiteJob>(`/api/v1/parasite-seo/jobs/${jobId}/requirements`, "PATCH", {
    requirements,
  });
}

export async function generateParasiteJob(jobId: string, stage?: string) {
  const qs = stage ? `?stage=${encodeURIComponent(stage)}` : "";
  return apiMutateData<ParasiteJob & { generation_complete?: boolean; generation_stage?: string }>(
    `/api/v1/parasite-seo/jobs/${jobId}/generate${qs}`,
    "POST",
  );
}

export async function runParasiteGenerationPipeline(
  jobId: string,
  onStage?: (label: string) => void,
) {
  const stages: Array<{ stage: string; label: string }> = [
    { stage: "confirm", label: "Creating content draft…" },
    { stage: "research", label: "Research brief…" },
    { stage: "strategy", label: "Content strategy…" },
    { stage: "outline", label: "Outline…" },
    { stage: "write", label: "Writing article…" },
  ];
  let latest: ParasiteJob & { generation_complete?: boolean } | null = null;
  for (const item of stages) {
    onStage?.(item.label);
    latest = await generateParasiteJob(jobId, item.stage);
  }
  return latest!;
}

export async function seoAnalyzeParasiteJob(jobId: string) {
  return apiMutateData<ParasiteJob>(`/api/v1/parasite-seo/jobs/${jobId}/seo-analyze`, "POST");
}

export async function optimizeParasiteJob(jobId: string) {
  return apiMutateData<ParasiteJob>(`/api/v1/parasite-seo/jobs/${jobId}/optimize`, "POST");
}

export async function decideOptimizeParasiteJob(jobId: string, accept: boolean) {
  return apiMutateData<ParasiteJob>(`/api/v1/parasite-seo/jobs/${jobId}/optimize/decision`, "POST", {
    accept,
  });
}

export async function linkAnalyzeParasiteJob(jobId: string) {
  return apiMutateData<ParasiteJob>(`/api/v1/parasite-seo/jobs/${jobId}/link-analysis`, "POST");
}

export async function mediaAnalyzeParasiteJob(jobId: string) {
  return apiMutateData<ParasiteJob>(`/api/v1/parasite-seo/jobs/${jobId}/media-analysis`, "POST");
}

export async function publishParasiteJob(jobId: string) {
  return apiMutateData<ParasiteJob>(`/api/v1/parasite-seo/jobs/${jobId}/publish`, "POST");
}

export async function createWebPage(jobId: string, slug?: string) {
  return apiMutateData<WebPageSummary>(`/api/v1/parasite-seo/jobs/${jobId}/web-page`, "POST", {
    slug: slug || null,
  });
}

export async function getWebPage(jobId: string, preview = false) {
  return apiGetData<WebPageSummary>(
    `/api/v1/parasite-seo/jobs/${jobId}/web-page${preview ? "?preview=true" : ""}`,
  );
}

export async function updateWebPage(
  jobId: string,
  payload: { slug?: string; visibility?: string; title?: string },
) {
  return apiMutateData<WebPageSummary>(`/api/v1/parasite-seo/jobs/${jobId}/web-page`, "PATCH", payload);
}

export async function publishWebPage(jobId: string) {
  return apiMutateData<WebPageSummary>(`/api/v1/parasite-seo/jobs/${jobId}/web-page/publish`, "POST");
}

export async function unpublishWebPage(jobId: string) {
  return apiMutateData<WebPageSummary>(`/api/v1/parasite-seo/jobs/${jobId}/web-page/unpublish`, "POST");
}

export async function archiveWebPage(jobId: string) {
  return apiMutateData<WebPageSummary>(`/api/v1/parasite-seo/jobs/${jobId}/web-page/archive`, "POST");
}

export async function updatePublishedWebPage(jobId: string) {
  return apiMutateData<WebPageSummary>(
    `/api/v1/parasite-seo/jobs/${jobId}/web-page/update-published`,
    "POST",
  );
}

export async function deleteWebPage(jobId: string, keepContent = true) {
  return apiMutateData<{ deleted: boolean; content_preserved: boolean }>(
    `/api/v1/parasite-seo/jobs/${jobId}/web-page?keep_content=${keepContent}`,
    "DELETE",
  );
}

export async function listPublicPages(projectId?: string) {
  return apiGetData<{ items: WebPageSummary[] }>("/api/v1/parasite-seo/public-pages", {
    project_id: projectId,
  });
}

export async function uploadParasiteMedia(jobId: string, file: File) {
  const base = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "";
  const body = new FormData();
  body.append("file", file);
  const response = await fetch(`${base}/api/v1/parasite-seo/jobs/${jobId}/media`, {
    method: "POST",
    body,
  });
  const json = await response.json();
  if (!response.ok) {
    throw new Error(json?.error?.message || `Upload failed (${response.status})`);
  }
  return json.data as {
    id: string;
    url: string;
    filename: string;
    size_bytes: number;
    content_type: string;
    media_type: string;
  };
}

export async function getPublicPage(slug: string) {
  return apiGetData<PublicPagePayload>(`/api/v1/public-pages/${slug}`);
}

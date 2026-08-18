export type ProjectDto = {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  niche: string | null;
  country: string | null;
  language: string | null;
  target_audience: string | null;
  monetization_model: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  campaign_count: number;
  content_count: number;
};

export type CampaignDto = {
  id: string;
  project_id: string;
  name: string;
  description: string | null;
  status: string;
  target_country: string | null;
  language: string | null;
  default_content_type: string;
  default_word_count: number;
  created_at: string;
  updated_at: string;
};

export type PromptDto = {
  id: string;
  project_id: string;
  campaign_id: string | null;
  raw_prompt: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type ContentDto = {
  id: string;
  project_id: string;
  campaign_id: string | null;
  prompt_id: string | null;
  title: string;
  slug: string;
  content: string;
  seo_title?: string | null;
  meta_description?: string | null;
  structured_body?: Record<string, unknown> | null;
  content_type: string;
  status: string;
  word_count: number;
  seo_score: number | null;
  quality_score: number | null;
  created_at: string;
  updated_at: string;
};

export type ContentVersionDto = {
  id: string;
  content_asset_id: string;
  version_number: number;
  content: string;
  change_summary: string | null;
  source?: string;
  created_by: string | null;
  created_at: string;
};

export type LinkDto = {
  id: string;
  content_asset_id: string;
  target_url: string;
  anchor_text: string;
  placement_description: string | null;
  link_attribute: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type MediaDto = {
  id: string;
  project_id: string;
  content_asset_id: string | null;
  media_type: string;
  url: string | null;
  storage_key: string | null;
  prompt: string | null;
  alt_text: string | null;
  caption: string | null;
  source: string | null;
  license_information: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type PublishingChannelDto = {
  id: string;
  project_id: string;
  name: string;
  channel_type: string;
  configuration: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type PublishedAssetDto = {
  id: string;
  content_asset_id: string;
  publishing_channel_id: string;
  published_url: string | null;
  external_id: string | null;
  status: string;
  published_at: string | null;
  last_checked_at: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

export type AiRunDto = {
  id: string;
  project_id: string | null;
  content_asset_id: string | null;
  agent_type: string;
  model: string | null;
  status: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  estimated_cost: number;
  execution_time_ms: number | null;
  input_summary: string | null;
  output_summary: string | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
};

export type KeywordDto = {
  id: string;
  project_id: string;
  content_asset_id: string | null;
  keyword: string;
  keyword_type: string;
  search_volume: number | null;
  difficulty: number | null;
  cpc: number | null;
  intent: string | null;
  country: string | null;
  language: string | null;
  opportunity_score: number | null;
  created_at: string;
  updated_at: string;
};

export type AnalyticsOverviewDto = {
  impressions: number;
  clicks: number;
  ctr: number;
  traffic: number;
  average_position: number;
  conversions: number;
  revenue: number;
  metric_count: number;
};

export type ProjectStatus = "active" | "paused" | "archived";

export type ContentType =
  | "article"
  | "listicle"
  | "comparison"
  | "guide"
  | "review"
  | "resource_page";

export type ContentStatus =
  | "draft"
  | "analyzing"
  | "generated"
  | "in_review"
  | "approved"
  | "published"
  | "failed";

export type LinkAttribute = "standard" | "sponsored" | "ugc" | "nofollow";

export type LinkStatus = "planned" | "inserted" | "verified" | "broken" | "removed";

export type CampaignStatus = "active" | "inactive";

export type PublishStatus =
  | "draft"
  | "queued"
  | "scheduled"
  | "publishing"
  | "published"
  | "failed";

export type MediaKind = "generated_image" | "uploaded_image" | "video_embed";

export type AgentStatus = "idle" | "running" | "success" | "warning" | "error";

export type NotificationKind = "info" | "success" | "warning" | "error";

export interface Project {
  id: string;
  name: string;
  niche: string;
  domain: string;
  status: ProjectStatus;
  assets: number;
  campaigns: number;
  updatedAt: string;
}

export interface DashboardKpis {
  totalProjects: number;
  totalContentAssets: number;
  generatedArticles: number;
  publishedAssets: number;
  activeCampaigns: number;
  managedLinks: number;
  indexedUrls: number;
  organicTraffic: number;
  clicks: number;
  conversions: number;
  revenue: number;
}

export interface TimeSeriesPoint {
  label: string;
  value: number;
}

export interface ContentAsset {
  id: string;
  projectId: string;
  title: string;
  seoTitle: string;
  metaDescription: string;
  slug: string;
  h1: string;
  headings: { level: 2 | 3; text: string }[];
  bodyHtml: string;
  contentType: ContentType;
  wordCount: number;
  primaryKeyword: string;
  secondaryKeywords: string[];
  tone: string;
  audience: string;
  country: string;
  language: string;
  status: ContentStatus;
  seoScore: number;
  qualityScore: number;
  keywordCoverage: number;
  linkStatus: string;
  mediaStatus: string;
  metadataStatus: string;
  targetUrl: string;
  anchorText: string;
  updatedAt: string;
  createdAt: string;
}

export interface PromptBrief {
  prompt: string;
  targetUrl: string;
  anchorText: string;
  contentType: ContentType;
  wordCount: number;
  primaryKeyword: string;
  secondaryKeywords: string;
  tone: string;
  audience: string;
  country: string;
  language: string;
  ctaRequired: boolean;
  imageRequired: boolean;
  videoRequired: boolean;
}

export interface PromptAnalysis {
  intent: string;
  topics: string[];
  keywords: { term: string; intent: string; volume: string; difficulty: string }[];
  requirements: string[];
  recommendedType: ContentType;
  outline: string[];
  risks: string[];
}

export interface MediaAsset {
  id: string;
  projectId: string;
  kind: MediaKind;
  title: string;
  prompt?: string;
  altText: string;
  caption: string;
  source: string;
  license: string;
  url: string;
  usedIn: string;
  createdAt: string;
}

export interface ManagedLink {
  id: string;
  projectId: string;
  targetUrl: string;
  anchorText: string;
  sourceContent: string;
  sourceContentId: string;
  placement: string;
  attribute: LinkAttribute;
  status: LinkStatus;
  createdAt: string;
}

export interface Campaign {
  id: string;
  projectId: string;
  name: string;
  niche: string;
  description: string;
  assets: number;
  generated: number;
  approved: number;
  published: number;
  failed: number;
  status: CampaignStatus;
  updatedAt: string;
}

export interface PublishingJob {
  id: string;
  projectId: string;
  destinationId: string;
  destination: string;
  contentId: string;
  contentTitle: string;
  title: string;
  slug: string;
  category: string;
  tags: string[];
  featuredImage: string;
  status: PublishStatus;
  scheduledAt?: string;
  publishedUrl?: string;
  logs: { at: string; level: "info" | "success" | "error"; message: string }[];
  authorized: boolean;
}

export interface PublishedAsset {
  id: string;
  projectId: string;
  title: string;
  destination: string;
  url: string;
  targetLink: string;
  status: "live" | "indexing" | "indexed" | "needs_review" | "removed";
  publishedAt: string;
  lastChecked: string;
}

export interface RankRow {
  id: string;
  projectId: string;
  keyword: string;
  targetUrl: string;
  currentPosition: number | null;
  previousPosition: number | null;
  lastChecked: string;
}

export interface KeywordIdea {
  term: string;
  volume: string;
  difficulty: string;
  intent: string;
  opportunity: string;
}

export interface SerpResult {
  position: number;
  title: string;
  url: string;
  type: string;
}

export interface CompetitorRow {
  domain: string;
  overlappingKeywords: number;
  estimatedTraffic: string;
  contentGap: string;
}

export interface ContentGap {
  topic: string;
  competitorCoverage: string;
  ourCoverage: string;
  priority: "high" | "medium" | "low";
}

export interface AnalyticsSummary {
  impressions: number;
  clicks: number;
  ctr: number;
  traffic: number;
  averagePosition: number;
}

export interface TopContentRow {
  title: string;
  url: string;
  clicks: number;
  impressions: number;
  ctr: number;
  position: number;
}

export interface RevenueSummary {
  affiliateClicks: number;
  conversions: number;
  revenue: number;
  expenses: number;
  profit: number;
  roi: number;
}

export interface RevenueStream {
  source: string;
  clicks: number;
  conversions: number;
  revenue: number;
}

export interface AiAgent {
  id: string;
  name: string;
  description: string;
  status: AgentStatus;
  lastRun: string;
  durationMs: number;
  tokens: number;
  costUsd: number;
  result: string;
}

export interface AppNotification {
  id: string;
  kind: NotificationKind;
  title: string;
  body: string;
  at: string;
  read: boolean;
}

export interface PublishingChannel {
  id: string;
  name: string;
  type: "wordpress" | "ghost" | "webflow" | "custom";
  authorized: boolean;
  account: string;
  lastSync: string;
}

export interface UserProfile {
  name: string;
  email: string;
  role: string;
  timezone: string;
  organization: string;
}

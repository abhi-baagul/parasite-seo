import type {
  AiAgent,
  AnalyticsSummary,
  AppNotification,
  Campaign,
  CompetitorRow,
  ContentAsset,
  ContentGap,
  DashboardKpis,
  KeywordIdea,
  ManagedLink,
  MediaAsset,
  Project,
  PromptAnalysis,
  PublishedAsset,
  PublishingChannel,
  PublishingJob,
  RankRow,
  RevenueStream,
  RevenueSummary,
  SerpResult,
  TimeSeriesPoint,
  TopContentRow,
  UserProfile,
} from "@/types";

export const userProfile: UserProfile = {
  name: "Ashish Rao",
  email: "ashish@parasiteseo.ai",
  role: "Workspace owner",
  timezone: "Asia/Kolkata",
  organization: "Northstar Content Lab",
};

export const projects: Project[] = [
  {
    id: "prj_home_solar",
    name: "Home Solar Buyer's Guides",
    niche: "Residential solar",
    domain: "fieldnotes.energyreview.co",
    status: "active",
    assets: 28,
    campaigns: 3,
    updatedAt: "2026-08-16T09:20:00.000Z",
  },
  {
    id: "prj_saas_payroll",
    name: "SaaS Payroll Comparisons",
    niche: "HR tech",
    domain: "opsdesk.workstack.io",
    status: "active",
    assets: 17,
    campaigns: 2,
    updatedAt: "2026-08-15T14:05:00.000Z",
  },
  {
    id: "prj_pet_insurance",
    name: "Pet Insurance Explainers",
    niche: "Pet finance",
    domain: "carebrief.pawcover.com",
    status: "paused",
    assets: 9,
    campaigns: 1,
    updatedAt: "2026-08-10T11:40:00.000Z",
  },
];

export const dashboardKpis: DashboardKpis = {
  totalProjects: 3,
  totalContentAssets: 54,
  generatedArticles: 41,
  publishedAssets: 22,
  activeCampaigns: 5,
  managedLinks: 38,
  indexedUrls: 19,
  organicTraffic: 48260,
  clicks: 6134,
  conversions: 187,
  revenue: 18420,
};

export const contentPerformance: TimeSeriesPoint[] = [
  { label: "Mar", value: 2100 },
  { label: "Apr", value: 2680 },
  { label: "May", value: 3120 },
  { label: "Jun", value: 2980 },
  { label: "Jul", value: 4010 },
  { label: "Aug", value: 4560 },
];

export const publishingActivity: TimeSeriesPoint[] = [
  { label: "Mon", value: 2 },
  { label: "Tue", value: 4 },
  { label: "Wed", value: 1 },
  { label: "Thu", value: 5 },
  { label: "Fri", value: 3 },
  { label: "Sat", value: 0 },
  { label: "Sun", value: 1 },
];

export const campaignStatusMix = [
  { label: "Active", value: 5 },
  { label: "Inactive", value: 2 },
];

export const aiRecommendations = [
  {
    id: "rec_1",
    title: "Refresh the solar inverter comparison",
    detail: "Average position slipped from 8.4 to 12.1. Add a 2026 pricing table and a new H2 on hybrid inverters.",
  },
  {
    id: "rec_2",
    title: "Authorize Ghost before the payroll campaign ships",
    detail: "Four approved drafts are waiting. The Workstack Ghost channel is connected but missing a featured-image mapping.",
  },
  {
    id: "rec_3",
    title: "Repair one sponsored placement",
    detail: "The Pawcover resource page still uses a standard attribute on an affiliate URL. Switch it to sponsored before the next crawl.",
  },
];

export const contentAssets: ContentAsset[] = [
  {
    id: "cnt_solar_inverters",
    projectId: "prj_home_solar",
    title: "Best Hybrid Solar Inverters for Homeowners in 2026",
    seoTitle: "Best Hybrid Solar Inverters 2026 | Homeowner Comparison",
    metaDescription:
      "Compare hybrid solar inverters for residential installs in 2026, including efficiency, backup, warranties, and who each model is for.",
    slug: "best-hybrid-solar-inverters-2026",
    h1: "Best Hybrid Solar Inverters for Homeowners in 2026",
    headings: [
      { level: 2, text: "How we evaluated hybrid inverters" },
      { level: 2, text: "Top picks by household type" },
      { level: 3, text: "Small homes and apartments" },
      { level: 2, text: "Cost, warranties, and install notes" },
      { level: 2, text: "Who should wait" },
    ],
    bodyHtml: `<p>Hybrid inverters sit between rooftop panels, a home battery, and the grid. For most homeowners the buying decision is no longer “string vs micro” — it is whether backup, export limiting, and future battery expansion are worth the extra hardware.</p>
<ul>
<li>Round-trip efficiency above 94%</li>
<li>Certified backup transfer under 30ms</li>
<li>Installer coverage in the target metro</li>
</ul>
<h2>How we evaluated hybrid inverters</h2>
<p>We scored products on usable backup, monitoring quality, and documented installer support rather than peak wattage claims.</p>
<table>
<thead><tr><th>Model</th><th>Backup</th><th>Best for</th></tr></thead>
<tbody>
<tr><td>Helios H8</td><td>Whole-home</td><td>Large detached homes</td></tr>
<tr><td>Nimbus 5</td><td>Essential loads</td><td>Townhouses</td></tr>
</tbody>
</table>
<div class="cta-block"><strong>Next step:</strong> Request a site assessment from an authorized installer before you lock inverter size. <a href="https://partners.energyreview.co/solar-assessment" rel="sponsored">Book a qualified assessment</a></div>`,
    contentType: "comparison",
    wordCount: 1840,
    primaryKeyword: "best hybrid solar inverters 2026",
    secondaryKeywords: ["hybrid inverter vs string", "home battery backup inverter"],
    tone: "Expert, practical",
    audience: "Homeowners evaluating a first solar + battery system",
    country: "United States",
    language: "English",
    status: "approved",
    seoScore: 86,
    qualityScore: 82,
    keywordCoverage: 78,
    linkStatus: "1 sponsored link inserted",
    mediaStatus: "2 images attached",
    metadataStatus: "Complete",
    targetUrl: "https://partners.energyreview.co/solar-assessment",
    anchorText: "Book a qualified assessment",
    updatedAt: "2026-08-16T08:12:00.000Z",
    createdAt: "2026-08-12T10:00:00.000Z",
  },
  {
    id: "cnt_payroll_guide",
    projectId: "prj_saas_payroll",
    title: "How Mid-Market Teams Should Compare Payroll Platforms",
    seoTitle: "Payroll Platform Comparison for Mid-Market Teams",
    metaDescription:
      "A practical framework for comparing payroll platforms: multi-state filings, contractor payments, GL export, and implementation risk.",
    slug: "compare-payroll-platforms-mid-market",
    h1: "How Mid-Market Teams Should Compare Payroll Platforms",
    headings: [
      { level: 2, text: "Start with filing complexity, not feature lists" },
      { level: 2, text: "Implementation risk checklist" },
    ],
    bodyHtml:
      "<p>Most payroll RFPs overweight UI screenshots. The expensive failures happen in multi-state filings, off-cycle corrections, and year-end amendments.</p>",
    contentType: "guide",
    wordCount: 1260,
    primaryKeyword: "compare payroll platforms",
    secondaryKeywords: ["mid market payroll software"],
    tone: "Operator, concise",
    audience: "Finance and People ops leads",
    country: "United States",
    language: "English",
    status: "generated",
    seoScore: 71,
    qualityScore: 74,
    keywordCoverage: 64,
    linkStatus: "Link planned",
    mediaStatus: "Needs featured image",
    metadataStatus: "Slug ready",
    targetUrl: "https://workstack.io/payroll-demo",
    anchorText: "See the payroll implementation checklist",
    updatedAt: "2026-08-15T16:40:00.000Z",
    createdAt: "2026-08-15T09:20:00.000Z",
  },
  {
    id: "cnt_pet_wait",
    projectId: "prj_pet_insurance",
    title: "Waiting Periods in Pet Insurance, Explained",
    seoTitle: "Pet Insurance Waiting Periods: What Owners Miss",
    metaDescription:
      "Understand accident, illness, and cruciate waiting periods so you do not buy a policy that cannot pay when you need it.",
    slug: "pet-insurance-waiting-periods",
    h1: "Waiting Periods in Pet Insurance, Explained",
    headings: [{ level: 2, text: "Accident vs illness clocks" }],
    bodyHtml: "<p>Waiting periods are the most common reason a first claim is denied. Read the clock before you compare reimbursement percentages.</p>",
    contentType: "article",
    wordCount: 980,
    primaryKeyword: "pet insurance waiting periods",
    secondaryKeywords: ["cruciate waiting period"],
    tone: "Clear, reassuring",
    audience: "New pet owners",
    country: "United States",
    language: "English",
    status: "published",
    seoScore: 80,
    qualityScore: 77,
    keywordCoverage: 72,
    linkStatus: "Verified",
    mediaStatus: "Complete",
    metadataStatus: "Complete",
    targetUrl: "https://pawcover.com/quote",
    anchorText: "Compare waiting periods before you enroll",
    updatedAt: "2026-08-09T12:00:00.000Z",
    createdAt: "2026-08-02T08:00:00.000Z",
  },
];

export const promptAnalysisSample: PromptAnalysis = {
  intent: "Commercial investigation — help a homeowner choose a hybrid inverter and route to an authorized assessment.",
  topics: [
    "Hybrid vs string inverters",
    "Battery-ready hardware",
    "Backup transfer speed",
    "Installer coverage",
  ],
  keywords: [
    { term: "best hybrid solar inverters 2026", intent: "Commercial", volume: "4.4k", difficulty: "Medium" },
    { term: "hybrid inverter for home battery", intent: "Informational", volume: "1.8k", difficulty: "Low" },
    { term: "whole home backup inverter", intent: "Commercial", volume: "2.1k", difficulty: "Medium" },
  ],
  requirements: [
    "Comparison table with backup type",
    "One sponsored CTA to the assessment partner",
    "Featured image plus in-article diagram",
    "US English, homeowner reading level",
  ],
  recommendedType: "comparison",
  outline: [
    "What a hybrid inverter actually does",
    "Evaluation criteria",
    "Picks by household type",
    "Cost and warranty notes",
    "Authorized next step",
  ],
  risks: [
    "Avoid ranking unsourced efficiency claims.",
    "Do not insert links on properties you do not control.",
  ],
};

export const mediaAssets: MediaAsset[] = [
  {
    id: "med_1",
    projectId: "prj_home_solar",
    kind: "generated_image",
    title: "Hybrid inverter diagram",
    prompt: "Editorial diagram of rooftop panels, hybrid inverter, battery, and home loads. Neutral charcoal and amber, no logos.",
    altText: "Diagram showing solar panels connected to a hybrid inverter, battery, and household circuits.",
    caption: "A hybrid inverter manages generation, storage, and backup in one enclosure.",
    source: "Generated in Media Agent",
    license: "Workspace original",
    url: "/media/hybrid-inverter.svg",
    usedIn: "Best Hybrid Solar Inverters for Homeowners in 2026",
    createdAt: "2026-08-12T11:10:00.000Z",
  },
  {
    id: "med_2",
    projectId: "prj_home_solar",
    kind: "uploaded_image",
    title: "Installer on a residential roof",
    altText: "Installer securing a solar rail on a shingle roof.",
    caption: "Site conditions still decide inverter size more than brochure wattage.",
    source: "Studio upload",
    license: "Licensed editorial, royalty-free",
    url: "/media/roof-install.svg",
    usedIn: "Best Hybrid Solar Inverters for Homeowners in 2026",
    createdAt: "2026-08-12T11:40:00.000Z",
  },
  {
    id: "med_3",
    projectId: "prj_saas_payroll",
    kind: "video_embed",
    title: "Payroll implementation walkthrough",
    prompt: undefined,
    altText: "Embedded walkthrough of a mid-market payroll implementation timeline.",
    caption: "Use this only after the client has authorized the destination.",
    source: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    license: "Partner-owned, embed permitted",
    url: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    usedIn: "How Mid-Market Teams Should Compare Payroll Platforms",
    createdAt: "2026-08-15T10:00:00.000Z",
  },
];

export const managedLinks: ManagedLink[] = [
  {
    id: "lnk_1",
    projectId: "prj_home_solar",
    targetUrl: "https://partners.energyreview.co/solar-assessment",
    anchorText: "Book a qualified assessment",
    sourceContent: "Best Hybrid Solar Inverters for Homeowners in 2026",
    sourceContentId: "cnt_solar_inverters",
    placement: "Closing CTA",
    attribute: "sponsored",
    status: "inserted",
    createdAt: "2026-08-12T12:00:00.000Z",
  },
  {
    id: "lnk_2",
    projectId: "prj_saas_payroll",
    targetUrl: "https://workstack.io/payroll-demo",
    anchorText: "See the payroll implementation checklist",
    sourceContent: "How Mid-Market Teams Should Compare Payroll Platforms",
    sourceContentId: "cnt_payroll_guide",
    placement: "Mid-article callout",
    attribute: "standard",
    status: "planned",
    createdAt: "2026-08-15T10:30:00.000Z",
  },
  {
    id: "lnk_3",
    projectId: "prj_pet_insurance",
    targetUrl: "https://pawcover.com/quote",
    anchorText: "Compare waiting periods before you enroll",
    sourceContent: "Waiting Periods in Pet Insurance, Explained",
    sourceContentId: "cnt_pet_wait",
    placement: "After definition list",
    attribute: "sponsored",
    status: "verified",
    createdAt: "2026-08-03T09:00:00.000Z",
  },
  {
    id: "lnk_4",
    projectId: "prj_pet_insurance",
    targetUrl: "https://pawcover.com/affiliates",
    anchorText: "partner program overview",
    sourceContent: "Waiting Periods in Pet Insurance, Explained",
    sourceContentId: "cnt_pet_wait",
    placement: "Footer note",
    attribute: "ugc",
    status: "broken",
    createdAt: "2026-08-03T09:20:00.000Z",
  },
];

export const campaigns: Campaign[] = [
  {
    id: "cmp_1",
    projectId: "prj_home_solar",
    name: "Q3 Hybrid Inverter Cluster",
    niche: "Residential solar",
    description: "Comparison and supporting explainers pointing to authorized installer assessments.",
    assets: 12,
    generated: 10,
    approved: 7,
    published: 5,
    failed: 1,
    status: "active",
    updatedAt: "2026-08-16T09:20:00.000Z",
  },
  {
    id: "cmp_2",
    projectId: "prj_saas_payroll",
    name: "Mid-market payroll series",
    niche: "HR tech",
    description: "Guides for finance leads evaluating payroll platforms on authorized Workstack properties.",
    assets: 8,
    generated: 6,
    approved: 4,
    published: 2,
    failed: 0,
    status: "active",
    updatedAt: "2026-08-15T14:05:00.000Z",
  },
  {
    id: "cmp_3",
    projectId: "prj_pet_insurance",
    name: "Waiting-period education",
    niche: "Pet finance",
    description: "Paused while the Ghost channel token is rotated.",
    assets: 6,
    generated: 5,
    approved: 4,
    published: 3,
    failed: 1,
    status: "inactive",
    updatedAt: "2026-08-10T11:40:00.000Z",
  },
];

export const publishingChannels: PublishingChannel[] = [
  {
    id: "ch_wordpress",
    name: "Energy Review WordPress",
    type: "wordpress",
    authorized: true,
    account: "fieldnotes.energyreview.co",
    lastSync: "2026-08-16T07:50:00.000Z",
  },
  {
    id: "ch_ghost",
    name: "Workstack Ghost",
    type: "ghost",
    authorized: true,
    account: "opsdesk.workstack.io",
    lastSync: "2026-08-15T18:12:00.000Z",
  },
  {
    id: "ch_webflow",
    name: "Pawcover Webflow",
    type: "webflow",
    authorized: false,
    account: "Disconnected — reconnect OAuth",
    lastSync: "2026-08-01T12:00:00.000Z",
  },
];

export const publishingJobs: PublishingJob[] = [
  {
    id: "job_1",
    projectId: "prj_home_solar",
    destinationId: "ch_wordpress",
    destination: "Energy Review WordPress",
    contentId: "cnt_solar_inverters",
    contentTitle: "Best Hybrid Solar Inverters for Homeowners in 2026",
    title: "Best Hybrid Solar Inverters for Homeowners in 2026",
    slug: "best-hybrid-solar-inverters-2026",
    category: "Equipment",
    tags: ["solar", "inverters", "home battery"],
    featuredImage: "Hybrid inverter diagram",
    status: "scheduled",
    scheduledAt: "2026-08-18T14:00:00.000Z",
    logs: [
      { at: "2026-08-16T08:20:00.000Z", level: "info", message: "Draft synced to WordPress." },
      { at: "2026-08-16T08:21:00.000Z", level: "success", message: "Featured image mapped." },
    ],
    authorized: true,
  },
  {
    id: "job_2",
    projectId: "prj_saas_payroll",
    destinationId: "ch_ghost",
    destination: "Workstack Ghost",
    contentId: "cnt_payroll_guide",
    contentTitle: "How Mid-Market Teams Should Compare Payroll Platforms",
    title: "How Mid-Market Teams Should Compare Payroll Platforms",
    slug: "compare-payroll-platforms-mid-market",
    category: "Operations",
    tags: ["payroll", "implementation"],
    featuredImage: "Needs featured image",
    status: "queued",
    logs: [{ at: "2026-08-15T16:45:00.000Z", level: "info", message: "Queued after quality pass." }],
    authorized: true,
  },
  {
    id: "job_3",
    projectId: "prj_pet_insurance",
    destinationId: "ch_webflow",
    destination: "Pawcover Webflow",
    contentId: "cnt_pet_wait",
    contentTitle: "Waiting Periods in Pet Insurance, Explained",
    title: "Waiting Periods in Pet Insurance, Explained",
    slug: "pet-insurance-waiting-periods",
    category: "Education",
    tags: ["pet insurance"],
    featuredImage: "Policy timeline",
    status: "failed",
    logs: [
      { at: "2026-08-10T11:41:00.000Z", level: "error", message: "Publish blocked: channel is not authorized." },
    ],
    authorized: false,
  },
];

export const publishedAssets: PublishedAsset[] = [
  {
    id: "pub_1",
    projectId: "prj_home_solar",
    title: "String vs Hybrid Inverters for First-Time Buyers",
    destination: "Energy Review WordPress",
    url: "https://fieldnotes.energyreview.co/string-vs-hybrid-inverters",
    targetLink: "https://partners.energyreview.co/solar-assessment",
    status: "indexed",
    publishedAt: "2026-07-22T13:00:00.000Z",
    lastChecked: "2026-08-16T06:00:00.000Z",
  },
  {
    id: "pub_2",
    projectId: "prj_saas_payroll",
    title: "Contractor Payments Inside Payroll Suites",
    destination: "Workstack Ghost",
    url: "https://opsdesk.workstack.io/contractor-payments-payroll",
    targetLink: "https://workstack.io/payroll-demo",
    status: "live",
    publishedAt: "2026-08-04T15:10:00.000Z",
    lastChecked: "2026-08-16T06:00:00.000Z",
  },
  {
    id: "pub_3",
    projectId: "prj_pet_insurance",
    title: "Waiting Periods in Pet Insurance, Explained",
    destination: "Pawcover Webflow",
    url: "https://carebrief.pawcover.com/pet-insurance-waiting-periods",
    targetLink: "https://pawcover.com/quote",
    status: "needs_review",
    publishedAt: "2026-08-09T12:20:00.000Z",
    lastChecked: "2026-08-16T06:00:00.000Z",
  },
];

export const keywordIdeas: KeywordIdea[] = [
  { term: "best hybrid solar inverters 2026", volume: "4.4k", difficulty: "42", intent: "Commercial", opportunity: "Primary cluster" },
  { term: "hybrid inverter with battery backup", volume: "2.9k", difficulty: "38", intent: "Commercial", opportunity: "Supporting article" },
  { term: "solar inverter efficiency rating", volume: "1.2k", difficulty: "27", intent: "Informational", opportunity: "Glossary" },
];

export const serpResults: SerpResult[] = [
  { position: 1, title: "Hybrid Inverter Buying Guide", url: "https://example-energy.com/hybrid-guide", type: "Article" },
  { position: 2, title: "Top 8 Hybrid Inverters", url: "https://reviews.example.com/hybrid-inverters", type: "List" },
  { position: 3, title: "Inverter types explained", url: "https://doe.example.gov/inverters", type: "Gov" },
];

export const competitors: CompetitorRow[] = [
  { domain: "reviews.example.com", overlappingKeywords: 64, estimatedTraffic: "91k", contentGap: "Pricing tables by state incentive" },
  { domain: "installco.example.com", overlappingKeywords: 28, estimatedTraffic: "40k", contentGap: "Installer coverage maps" },
];

export const contentGaps: ContentGap[] = [
  { topic: "State incentive stacking with hybrid systems", competitorCoverage: "Strong", ourCoverage: "None", priority: "high" },
  { topic: "Microinverter vs hybrid for townhomes", competitorCoverage: "Medium", ourCoverage: "Thin", priority: "medium" },
  { topic: "Monitoring app comparison", competitorCoverage: "Strong", ourCoverage: "Planned", priority: "low" },
];

export const rankRows: RankRow[] = [
  {
    id: "rk_1",
    projectId: "prj_home_solar",
    keyword: "string vs hybrid inverter",
    targetUrl: "https://fieldnotes.energyreview.co/string-vs-hybrid-inverters",
    currentPosition: 7,
    previousPosition: 11,
    lastChecked: "2026-08-16T06:00:00.000Z",
  },
  {
    id: "rk_2",
    projectId: "prj_home_solar",
    keyword: "best hybrid solar inverters 2026",
    targetUrl: "https://fieldnotes.energyreview.co/best-hybrid-solar-inverters-2026",
    currentPosition: 18,
    previousPosition: 14,
    lastChecked: "2026-08-16T06:00:00.000Z",
  },
  {
    id: "rk_3",
    projectId: "prj_saas_payroll",
    keyword: "compare payroll platforms",
    targetUrl: "https://opsdesk.workstack.io/compare-payroll-platforms-mid-market",
    currentPosition: null,
    previousPosition: null,
    lastChecked: "2026-08-16T06:00:00.000Z",
  },
  {
    id: "rk_4",
    projectId: "prj_pet_insurance",
    keyword: "pet insurance waiting periods",
    targetUrl: "https://carebrief.pawcover.com/pet-insurance-waiting-periods",
    currentPosition: 9,
    previousPosition: 9,
    lastChecked: "2026-08-16T06:00:00.000Z",
  },
];

export const analyticsSummary: AnalyticsSummary = {
  impressions: 312400,
  clicks: 6134,
  ctr: 1.96,
  traffic: 48260,
  averagePosition: 14.2,
};

export const trafficTrend: TimeSeriesPoint[] = [
  { label: "W1", value: 6200 },
  { label: "W2", value: 7100 },
  { label: "W3", value: 6800 },
  { label: "W4", value: 8020 },
  { label: "W5", value: 8640 },
  { label: "W6", value: 9100 },
];

export const topContent: TopContentRow[] = [
  {
    title: "String vs Hybrid Inverters for First-Time Buyers",
    url: "https://fieldnotes.energyreview.co/string-vs-hybrid-inverters",
    clicks: 1840,
    impressions: 61200,
    ctr: 3.01,
    position: 7.2,
  },
  {
    title: "Contractor Payments Inside Payroll Suites",
    url: "https://opsdesk.workstack.io/contractor-payments-payroll",
    clicks: 960,
    impressions: 40110,
    ctr: 2.39,
    position: 11.4,
  },
  {
    title: "Waiting Periods in Pet Insurance, Explained",
    url: "https://carebrief.pawcover.com/pet-insurance-waiting-periods",
    clicks: 720,
    impressions: 28840,
    ctr: 2.5,
    position: 9.1,
  },
];

export const revenueSummary: RevenueSummary = {
  affiliateClicks: 2410,
  conversions: 187,
  revenue: 18420,
  expenses: 6310,
  profit: 12110,
  roi: 191.9,
};

export const revenueStreams: RevenueStream[] = [
  { source: "Solar assessments", clicks: 1280, conversions: 96, revenue: 11200 },
  { source: "Payroll demos", clicks: 740, conversions: 54, revenue: 4860 },
  { source: "Pet quotes", clicks: 390, conversions: 37, revenue: 2360 },
];

export const expenseTrend: TimeSeriesPoint[] = [
  { label: "Mar", value: 820 },
  { label: "Apr", value: 910 },
  { label: "May", value: 880 },
  { label: "Jun", value: 1040 },
  { label: "Jul", value: 1260 },
  { label: "Aug", value: 1400 },
];

export const aiAgents: AiAgent[] = [
  { id: "prompt-analyzer", name: "Prompt Analyzer", description: "Extracts intent, entities, and hard requirements from the brief.", status: "success", lastRun: "2026-08-16T08:01:00.000Z", durationMs: 4200, tokens: 3180, costUsd: 0.11, result: "Commercial comparison brief with one sponsored CTA." },
  { id: "research-agent", name: "Research Agent", description: "Collects topic facts, SERP notes, and source constraints.", status: "success", lastRun: "2026-08-16T08:03:00.000Z", durationMs: 18100, tokens: 12440, costUsd: 0.42, result: "12 source notes, 3 comparison axes." },
  { id: "strategy-agent", name: "Strategy Agent", description: "Chooses format, outline, and internal linking plan.", status: "success", lastRun: "2026-08-16T08:04:00.000Z", durationMs: 6300, tokens: 5400, costUsd: 0.19, result: "Comparison + CTA close, 5 H2 outline." },
  { id: "content-agent", name: "Content Agent", description: "Writes the draft to the approved outline and tone.", status: "success", lastRun: "2026-08-16T08:08:00.000Z", durationMs: 27400, tokens: 18620, costUsd: 0.67, result: "1,840-word draft generated." },
  { id: "seo-agent", name: "SEO Agent", description: "Titles, slug, meta, headings, and keyword coverage.", status: "warning", lastRun: "2026-08-16T08:09:00.000Z", durationMs: 5100, tokens: 4020, costUsd: 0.14, result: "Secondary keyword underused in H3s." },
  { id: "media-agent", name: "Media Agent", description: "Creates image prompts, alt text, and embed slots.", status: "success", lastRun: "2026-08-16T08:10:00.000Z", durationMs: 9200, tokens: 2100, costUsd: 0.22, result: "2 images, 1 diagram prompt." },
  { id: "quality-agent", name: "Quality Agent", description: "Checks claims, structure, CTA, and policy constraints.", status: "success", lastRun: "2026-08-16T08:11:00.000Z", durationMs: 7400, tokens: 6880, costUsd: 0.24, result: "Passed with 2 editorial notes." },
  { id: "publishing-agent", name: "Publishing Agent", description: "Pushes to authorized channels only.", status: "idle", lastRun: "2026-08-15T18:12:00.000Z", durationMs: 2100, tokens: 860, costUsd: 0.03, result: "Waiting on scheduled WordPress slot." },
  { id: "monitoring-agent", name: "Monitoring Agent", description: "Rechecks published URLs, links, and index signals.", status: "running", lastRun: "2026-08-17T06:40:00.000Z", durationMs: 0, tokens: 0, costUsd: 0, result: "Checking 22 live URLs…" },
  { id: "analytics-agent", name: "Analytics Agent", description: "Rolls up Search Console-style metrics for the workspace.", status: "success", lastRun: "2026-08-17T06:00:00.000Z", durationMs: 3300, tokens: 1200, costUsd: 0.05, result: "CTR up 0.2pts week over week." },
  { id: "optimization-agent", name: "Optimization Agent", description: "Suggests refreshes from rank and revenue movement.", status: "error", lastRun: "2026-08-16T21:00:00.000Z", durationMs: 800, tokens: 240, costUsd: 0.01, result: "Provider timeout — retry queued." },
];

export const notifications: AppNotification[] = [
  {
    id: "n1",
    kind: "warning",
    title: "Webflow channel unauthorized",
    body: "Pawcover publish jobs are blocked until OAuth is restored.",
    at: "2026-08-16T11:40:00.000Z",
    read: false,
  },
  {
    id: "n2",
    kind: "success",
    title: "Inverter draft approved",
    body: "Quality Agent passed the hybrid inverter comparison.",
    at: "2026-08-16T08:12:00.000Z",
    read: false,
  },
  {
    id: "n3",
    kind: "info",
    title: "Rank check complete",
    body: "4 tracked keywords updated at 06:00 UTC.",
    at: "2026-08-16T06:01:00.000Z",
    read: true,
  },
];

export const recentPublishing = publishedAssets.map((asset) => ({
  id: asset.id,
  title: asset.title,
  destination: asset.destination,
  status: asset.status,
  at: asset.publishedAt,
}));

export function getContentById(id: string) {
  return contentAssets.find((item) => item.id === id);
}

export function filterByProject<T extends { projectId: string }>(items: T[], projectId: string | "all") {
  if (projectId === "all") return items;
  return items.filter((item) => item.projectId === projectId);
}

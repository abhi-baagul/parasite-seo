export interface NavItem {
  href: string;
  label: string;
  icon: string;
}

export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Dashboard", icon: "bi-grid-1x2" },
  { href: "/projects", label: "Projects", icon: "bi-folder2" },
  { href: "/create-content", label: "Create Content", icon: "bi-plus-square" },
  { href: "/parasite-seo", label: "Parasite SEO AI", icon: "bi-lightning-charge" },
  { href: "/parasite-seo/campaigns", label: "Backlink Campaigns", icon: "bi-diagram-3" },
  { href: "/parasite-seo/campaigns/backlinks", label: "Project Backlinks", icon: "bi-link-45deg" },
  { href: "/content-studio", label: "Content Studio", icon: "bi-pencil-square" },
  { href: "/assets", label: "Asset Library", icon: "bi-archive" },
  { href: "/media", label: "Media", icon: "bi-images" },
  { href: "/links", label: "Links", icon: "bi-link-45deg" },
  { href: "/campaigns", label: "Campaigns", icon: "bi-flag" },
  { href: "/publishing", label: "Publishing", icon: "bi-send" },
  { href: "/published-assets", label: "Published Assets", icon: "bi-check2-square" },
  { href: "/seo-intelligence", label: "SEO Intelligence", icon: "bi-search" },
  { href: "/rank-tracker", label: "Rank Tracker", icon: "bi-graph-up-arrow" },
  { href: "/analytics", label: "Analytics", icon: "bi-bar-chart" },
  { href: "/revenue", label: "Revenue", icon: "bi-currency-dollar" },
  { href: "/ai-agents", label: "AI Agents", icon: "bi-cpu" },
  { href: "/settings", label: "Settings", icon: "bi-gear" },
];

export const PAGE_META: Record<
  string,
  { title: string; description: string; crumbs: { href?: string; label: string }[] }
> = {
  "/": {
    title: "Dashboard",
    description: "Operational snapshot across content, publishing, traffic, and revenue.",
    crumbs: [{ label: "Dashboard" }],
  },
  "/projects": {
    title: "Projects",
    description: "Organize parasite SEO workstreams by niche, domain, and campaign set.",
    crumbs: [{ href: "/", label: "Home" }, { label: "Projects" }],
  },
  "/create-content": {
    title: "Create Content",
    description: "Capture the brief, analyze the prompt, and generate a production-ready draft.",
    crumbs: [{ href: "/", label: "Home" }, { label: "Create Content" }],
  },
  "/parasite-seo": {
    title: "Parasite SEO AI",
    description: "Create AI-powered web content, optimize SEO, add media and links, and publish a public page.",
    crumbs: [{ href: "/", label: "Home" }, { label: "Parasite SEO AI" }],
  },
  "/content-studio": {
    title: "Content Studio",
    description: "Edit structure, SEO fields, media, links, and quality signals in one workspace.",
    crumbs: [{ href: "/", label: "Home" }, { label: "Content Studio" }],
  },
  "/assets": {
    title: "Asset Library",
    description: "Browse content and media assets across projects.",
    crumbs: [{ href: "/", label: "Home" }, { label: "Asset Library" }],
  },
  "/media": {
    title: "Media",
    description: "Manage generated images, uploads, embeds, alt text, and licensing.",
    crumbs: [{ href: "/", label: "Home" }, { label: "Media" }],
  },
  "/links": {
    title: "Links",
    description: "Configure authorized placements, anchors, and link attributes.",
    crumbs: [{ href: "/", label: "Home" }, { label: "Links" }],
  },
  "/campaigns": {
    title: "Campaigns",
    description: "Track asset volume from generation through approval and publication.",
    crumbs: [{ href: "/", label: "Home" }, { label: "Campaigns" }],
  },
  "/publishing": {
    title: "Publishing",
    description: "Queue authorized destinations, schedules, metadata, and publish logs.",
    crumbs: [{ href: "/", label: "Home" }, { label: "Publishing" }],
  },
  "/published-assets": {
    title: "Published Assets",
    description: "Monitor live URLs, target links, index status, and last health checks.",
    crumbs: [{ href: "/", label: "Home" }, { label: "Published Assets" }],
  },
  "/seo-intelligence": {
    title: "SEO Intelligence",
    description: "Keyword research, SERP snapshots, competitor overlap, and content gaps.",
    crumbs: [{ href: "/", label: "Home" }, { label: "SEO Intelligence" }],
  },
  "/rank-tracker": {
    title: "Rank Tracker",
    description: "Follow keyword positions for published URLs over time.",
    crumbs: [{ href: "/", label: "Home" }, { label: "Rank Tracker" }],
  },
  "/analytics": {
    title: "Analytics",
    description: "Impressions, clicks, CTR, traffic, and top performing assets.",
    crumbs: [{ href: "/", label: "Home" }, { label: "Analytics" }],
  },
  "/revenue": {
    title: "Revenue",
    description: "Affiliate clicks, conversions, expenses, profit, and campaign ROI.",
    crumbs: [{ href: "/", label: "Home" }, { label: "Revenue" }],
  },
  "/ai-agents": {
    title: "AI Agents",
    description: "Monitor pipeline agents, last runs, token use, cost, and outcomes.",
    crumbs: [{ href: "/", label: "Home" }, { label: "AI Agents" }],
  },
  "/settings": {
    title: "Settings",
    description: "Profile, providers, publishing channels, storage, and security.",
    crumbs: [{ href: "/", label: "Home" }, { label: "Settings" }],
  },
};

export function matchPageMeta(pathname: string) {
  if (pathname.startsWith("/projects/") && pathname !== "/projects") {
    return {
      title: "Project",
      description: "Project profile, generated content, and workspace actions.",
      crumbs: [
        { href: "/", label: "Home" },
        { href: "/projects", label: "Projects" },
        { label: "Profile" },
      ],
    };
  }
  if (pathname.startsWith("/content-studio/")) {
    return {
      title: "Article editor",
      description: "Refine the draft, SEO metadata, and supporting assets before publishing.",
      crumbs: [
        { href: "/", label: "Home" },
        { href: "/content-studio", label: "Content Studio" },
        { label: "Editor" },
      ],
    };
  }
  if (pathname.startsWith("/parasite-seo/campaigns")) {
    return {
      title: "Backlink campaigns",
      description: "Build authorized tiered link networks, verify backlinks, and monitor referring domains.",
      crumbs: [
        { href: "/", label: "Home" },
        { href: "/parasite-seo", label: "Parasite SEO AI" },
        { label: "Backlink campaigns" },
      ],
    };
  }
  if (pathname.startsWith("/parasite-seo/network")) {
    return {
      title: "Content network",
      description: "Internal link relationships, orphan pages, and link health across published pages.",
      crumbs: [
        { href: "/", label: "Home" },
        { href: "/parasite-seo", label: "Parasite SEO AI" },
        { label: "Content network" },
      ],
    };
  }
  if (pathname.startsWith("/parasite-seo/")) {
    return {
      title: "Parasite SEO AI",
      description: "Guided AI workflow from prompt to public page.",
      crumbs: [
        { href: "/", label: "Home" },
        { href: "/parasite-seo", label: "Parasite SEO AI" },
        { label: "Workflow" },
      ],
    };
  }
  return PAGE_META[pathname] ?? {
    title: "Parasite SEO",
    description: "",
    crumbs: [{ label: "Workspace" }],
  };
}

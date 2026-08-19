import type { Metadata } from "next";
import type { PublicPagePayload } from "@/services/parasite-seo-service";
import { apiProxyTarget } from "@/lib/api-proxy-target";

/** First-path-segment workspace routes — must stay in sync with backend RESERVED_PUBLIC_SLUGS. */
export const APP_FIRST_SEGMENTS = new Set([
  "account",
  "admin",
  "ai-agents",
  "analytics",
  "api",
  "app",
  "assets",
  "auth",
  "c",
  "campaigns",
  "content-studio",
  "create-content",
  "dashboard",
  "docs",
  "edit",
  "export",
  "health",
  "home",
  "jobs",
  "links",
  "login",
  "logout",
  "media",
  "network",
  "new",
  "notifications",
  "p",
  "page",
  "pages",
  "parasite-seo",
  "preview",
  "projects",
  "public",
  "published-assets",
  "publishing",
  "rank-tracker",
  "register",
  "revenue",
  "seo-intelligence",
  "settings",
  "sign-in",
  "signin",
  "signup",
  "static",
  "studio",
  "users",
]);

export const CLOUD_MIRROR_PROVIDERS = new Set([
  "vercel",
  "netlify",
  "aws",
  "gcp",
  "azure",
  "cloudflare",
  "github",
  "render",
]);

export function isPublicArticlePathname(pathname: string | null | undefined): boolean {
  if (!pathname) return false;
  if (pathname.startsWith("/p/") || pathname.startsWith("/c/")) return true;
  const parts = pathname.split("/").filter(Boolean);
  return parts.length === 1 && !APP_FIRST_SEGMENTS.has(parts[0]);
}

export async function fetchPublicPage(slug: string): Promise<PublicPagePayload | null> {
  try {
    const res = await fetch(`${apiProxyTarget()}/api/v1/public-pages/${encodeURIComponent(slug)}`, {
      next: { revalidate: 30 },
    });
    if (res.status === 404) return null;
    if (!res.ok) return null;
    const json = await res.json();
    if (!json?.success || !json.data) return null;
    return json.data as PublicPagePayload;
  } catch {
    return null;
  }
}

export function publicArticleMetadata(page: PublicPagePayload | null): Metadata {
  if (!page) {
    return { title: "Page not found" };
  }
  const meta = page.metadata;
  return {
    title: meta.title || page.seo_title || page.title,
    description: meta.description || page.meta_description || undefined,
    alternates: { canonical: meta.canonical },
    openGraph: {
      title: meta.og.title,
      description: meta.og.description,
      url: meta.og.url,
      type: "article",
      images: meta.og.image ? [{ url: meta.og.image }] : undefined,
    },
    twitter: {
      card: "summary_large_image",
      title: meta.twitter.title,
      description: meta.twitter.description,
      images: meta.twitter.image ? [meta.twitter.image] : undefined,
    },
  };
}

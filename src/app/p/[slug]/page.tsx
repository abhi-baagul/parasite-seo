import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { PublicArticleView } from "@/features/parasite-seo/PublicArticleView";
import { apiProxyTarget } from "@/lib/api-proxy-target";
import type { PublicPagePayload } from "@/services/parasite-seo-service";

const backendOrigin = apiProxyTarget();

async function fetchPublicPage(slug: string): Promise<PublicPagePayload | null> {
  try {
    const res = await fetch(`${backendOrigin}/api/v1/public-pages/${encodeURIComponent(slug)}`, {
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

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const page = await fetchPublicPage(slug);
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

export default async function PublicArticlePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const page = await fetchPublicPage(slug);
  if (!page) notFound();
  return <PublicArticleView page={page} />;
}

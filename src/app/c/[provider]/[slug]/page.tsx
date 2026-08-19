import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { PublicArticleView } from "@/features/parasite-seo/PublicArticleView";
import {
  CLOUD_MIRROR_PROVIDERS,
  fetchPublicPage,
  publicArticleMetadata,
} from "@/lib/public-article";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ provider: string; slug: string }>;
}): Promise<Metadata> {
  const { provider, slug } = await params;
  if (!CLOUD_MIRROR_PROVIDERS.has(provider)) {
    return { title: "Page not found" };
  }
  return publicArticleMetadata(await fetchPublicPage(slug));
}

export default async function CloudMirrorArticlePage({
  params,
}: {
  params: Promise<{ provider: string; slug: string }>;
}) {
  const { provider, slug } = await params;
  if (!CLOUD_MIRROR_PROVIDERS.has(provider)) notFound();
  const page = await fetchPublicPage(slug);
  if (!page) notFound();
  return <PublicArticleView page={page} />;
}

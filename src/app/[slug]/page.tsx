import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { PublicArticleView } from "@/features/parasite-seo/PublicArticleView";
import { APP_FIRST_SEGMENTS, fetchPublicPage, publicArticleMetadata } from "@/lib/public-article";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  if (APP_FIRST_SEGMENTS.has(slug)) {
    return { title: "Page not found" };
  }
  return publicArticleMetadata(await fetchPublicPage(slug));
}

export default async function VanityPublicArticlePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  if (APP_FIRST_SEGMENTS.has(slug)) notFound();
  const page = await fetchPublicPage(slug);
  if (!page) notFound();
  return <PublicArticleView page={page} />;
}

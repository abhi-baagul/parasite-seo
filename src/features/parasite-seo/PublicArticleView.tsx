import type { PublicPagePayload } from "@/services/parasite-seo-service";

function relFor(attr: string | undefined): string {
  if (attr === "sponsored") return "sponsored noopener noreferrer";
  if (attr === "ugc") return "ugc noopener noreferrer";
  if (attr === "nofollow") return "nofollow noopener noreferrer";
  return "noopener noreferrer";
}

function youtubeEmbed(url: string): string | null {
  try {
    const u = new URL(url);
    if (u.hostname.includes("youtu.be")) {
      const id = u.pathname.replace("/", "");
      return id ? `https://www.youtube.com/embed/${id}` : null;
    }
    if (u.hostname.includes("youtube.com")) {
      const id = u.searchParams.get("v");
      return id ? `https://www.youtube.com/embed/${id}` : null;
    }
  } catch {
    return null;
  }
  return null;
}

function vimeoEmbed(url: string): string | null {
  try {
    const u = new URL(url);
    if (!u.hostname.includes("vimeo.com")) return null;
    const id = u.pathname.split("/").filter(Boolean).pop();
    return id ? `https://player.vimeo.com/video/${id}` : null;
  } catch {
    return null;
  }
}

export function PublicArticleView({
  page,
  preview = false,
}: {
  page: PublicPagePayload;
  preview?: boolean;
}) {
  const featured = page.featured_image;
  const publishedLabel = page.published_at
    ? new Date(page.published_at).toLocaleDateString(undefined, {
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    : null;

  return (
    <div className={`public-article${preview ? " public-article-preview" : ""}`}>
      <header className="public-article-header">
        <div className="public-article-inner public-header-row">
          <div className="public-brand">Parasite SEO AI</div>
          {preview ? <span className="public-preview-pill">Preview</span> : null}
        </div>
      </header>

      <article className="public-article-inner">
        {page.category ? <p className="public-kicker">{page.category}</p> : null}
        <h1>{page.title}</h1>
        <div className="public-meta-row">
          {publishedLabel ? <span>Published {publishedLabel}</span> : null}
          {page.word_count ? <span>{page.word_count} words</span> : null}
        </div>

        {featured?.url ? (
          <figure className="public-featured-wrap">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              className="public-featured"
              src={featured.url}
              alt={featured.alt_text || page.title}
              loading="eager"
            />
            {featured.caption ? <figcaption>{featured.caption}</figcaption> : null}
          </figure>
        ) : null}

        <div className="public-body" dangerouslySetInnerHTML={{ __html: page.content_html }} />

        {page.videos?.length ? (
          <section className="public-media-block">
            <h2>Videos</h2>
            {page.videos.map((video) => {
              const yt = youtubeEmbed(video.url || "");
              const vm = vimeoEmbed(video.url || "");
              const embed = yt || vm;
              return (
                <div key={video.id} className="public-video">
                  {embed ? (
                    <iframe
                      src={embed}
                      title={video.alt_text || "Video"}
                      loading="lazy"
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                      allowFullScreen
                    />
                  ) : video.url?.startsWith("/api/") ? (
                    <video controls preload="metadata" src={video.url}>
                      <track kind="captions" />
                    </video>
                  ) : (
                    <p className="text-muted">Video unavailable</p>
                  )}
                  {video.caption ? <p className="public-caption">{video.caption}</p> : null}
                </div>
              );
            })}
          </section>
        ) : null}

        {page.target_link?.target_url ? (
          <aside className="public-cta">
            <h2>Ready to get started?</h2>
            <p>Learn more and explore the available options.</p>
            <a
              className="public-cta-btn"
              href={page.target_link.target_url}
              target="_blank"
              rel={relFor(page.target_link.link_attribute)}
            >
              {page.target_link.anchor_text || "Get Started"}
            </a>
          </aside>
        ) : null}

        {page.faq?.length ? (
          <section className="public-faq">
            <h2>FAQ</h2>
            {page.faq.map((item) => (
              <details key={item.question} className="public-faq-item">
                <summary>{item.question}</summary>
                <p>{item.answer}</p>
              </details>
            ))}
          </section>
        ) : null}

        {page.references?.length ? (
          <section className="public-refs">
            <h2>References</h2>
            <ol>
              {page.references.map((ref) => (
                <li key={`${ref.url}-${ref.title}`}>
                  <a href={ref.url} target="_blank" rel="noopener noreferrer">
                    {ref.title}
                  </a>
                </li>
              ))}
            </ol>
          </section>
        ) : null}

        {page.related_pages?.length ? (
          <section className="public-related">
            <h2>Related articles</h2>
            <ul className="public-related-list">
              {page.related_pages.map((rel) => (
                <li key={rel.slug}>
                  <a href={`/p/${rel.slug}`}>{rel.title}</a>
                </li>
              ))}
            </ul>
          </section>
        ) : null}
      </article>

      <footer className="public-article-footer">
        <div className="public-article-inner">
          <div>Parasite SEO AI</div>
          <div className="small">© {new Date().getFullYear()} · Public content page</div>
        </div>
      </footer>

      {page.structured_data?.length ? (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(page.structured_data) }}
        />
      ) : null}
    </div>
  );
}

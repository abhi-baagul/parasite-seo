/** FastAPI origin for Next.js rewrites and server-side fetches. */
export function apiProxyTarget(): string {
  const configured = process.env.API_PROXY_TARGET?.trim();
  if (configured) {
    return configured.replace(/\/$/, "");
  }
  if (process.env.VERCEL) {
    return "https://parasite-seo.onrender.com";
  }
  return "http://127.0.0.1:8000";
}

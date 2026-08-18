import type { NextConfig } from "next";
import { apiProxyTarget } from "./src/lib/api-proxy-target";

const backendOrigin = apiProxyTarget();

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendOrigin.replace(/\/$/, "")}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;

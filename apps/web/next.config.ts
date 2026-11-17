import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // "standalone" output is strictly for self-hosted Docker builds (apps/web/Dockerfile).
  // On Vercel, Vercel natively bundles serverless functions; forcing standalone mode
  // causes Vercel's onBuildComplete hook to fail looking for next-server.js.nft.json.
  output: process.env.VERCEL ? undefined : "standalone",
  allowedDevOrigins: ["10.61.156.221", "localhost", "127.0.0.1"],
};

export default nextConfig;

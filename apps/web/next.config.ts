import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // "standalone" output bundles only the files needed to run `next start`,
  // enabling a lean Docker runtime stage that copies just .next/standalone/
  // rather than the full node_modules tree.
  output: "standalone",
  allowedDevOrigins: ["10.61.156.221", "localhost", "127.0.0.1"],
};

export default nextConfig;

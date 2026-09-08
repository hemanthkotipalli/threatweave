import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // "standalone" output bundles only the files needed to run `next start`,
  // enabling a lean Docker runtime stage that copies just .next/standalone/
  // rather than the full node_modules tree.
  output: "standalone",
};

export default nextConfig;

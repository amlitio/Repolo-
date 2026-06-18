import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Enables the Dockerfile's minimal-copy multi-stage runtime image.
  output: "standalone",
  typescript: {
    // Type-checking is run separately via `npm run typecheck`; don't double-run during build.
    ignoreBuildErrors: true,
  },
};

export default nextConfig;

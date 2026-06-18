import type { Config } from "tailwindcss";

/**
 * Tailwind v4 reads most design tokens from the `@theme` block in
 * app/globals.css. This config file exists for editor tooling / IDE
 * IntelliSense and to scope the content globs explicitly.
 */
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
};

export default config;

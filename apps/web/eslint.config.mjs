import nextCoreWebVitals from "eslint-config-next/core-web-vitals";
import nextTypescript from "eslint-config-next/typescript";

/**
 * eslint-config-next ships native ESLint 9 flat configs (arrays of config
 * objects) as of the Next 16 line - no `FlatCompat`/`extends("next/...")`
 * shimming needed (that legacy `.eslintrc`-style pattern triggers a
 * circular-JSON crash in this version combination because the underlying
 * plugin objects aren't meant to be re-serialized through
 * @eslint/eslintrc's config validator). Spread the flat config arrays
 * directly instead.
 */
const eslintConfig = [
  ...nextCoreWebVitals,
  ...nextTypescript,
  {
    ignores: [
      ".next/**",
      "node_modules/**",
      "playwright-report/**",
      "test-results/**",
      "e2e/**",
    ],
  },
  {
    rules: {
      // Mapbox GL + Clerk SSR boundaries occasionally need explicit `any` at
      // the integration edge (e.g. GeoJSON source typing); keep this a warning
      // rather than an error so it surfaces in review without blocking CI.
      "@typescript-eslint/no-explicit-any": "warn",
    },
  },
];

export default eslintConfig;

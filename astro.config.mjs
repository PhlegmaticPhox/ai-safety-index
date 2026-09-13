// @ts-check
import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";

// SITE_URL is set by CI; falls back to the Pages preview domain locally.
const site = process.env.SITE_URL ?? "https://ai-safety-index.pages.dev";

export default defineConfig({
  site,
  integrations: [mdx(), sitemap()],
  build: {
    // Charts render to SVG at build time, so most pages ship zero client JS.
    inlineStylesheets: "auto",
  },
});

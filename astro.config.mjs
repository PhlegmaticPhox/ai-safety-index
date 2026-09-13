// @ts-check
import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";
import icon from "astro-icon";

/**
 * The site's own origin. Every canonical link, every og:url and every sitemap
 * entry is built from it.
 *
 * Hardcoded, and deliberately not read from the environment. It was an env var
 * for exactly one day, and in that day it was wrong twice: first defaulting to a
 * pages.dev domain that does not resolve, then set in the Cloudflare build
 * variables to a value carrying the scheme twice, which made every canonical on
 * the live site read `https://https/`. Nothing in the page looks wrong when that
 * happens, and the deployed sitemap listed thirty-two URLs on a host that does
 * not exist.
 *
 * This site has one domain. A value that never changes does not need a
 * configuration mechanism, and the mechanism is what allowed it to be wrong
 * unnoticed. scripts/check-internal-links.mjs now fails the build if what is
 * rendered here is not a plausible hostname.
 */
const site = "https://aisafetytracker.org";

export default defineConfig({
  site,
  // Phosphor only, one family for the whole project, inlined as SVG at build time
  // so icons cost no client JS and no network request.
  integrations: [mdx(), sitemap(), icon({ include: { ph: ["*"] } })],
  build: {
    // Charts render to SVG at build time, so most pages ship zero client JS.
    inlineStylesheets: "auto",
  },
});

// @ts-check
import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";
import icon from "astro-icon";

/**
 * The site's own origin, which every canonical link and every sitemap entry is
 * built from.
 *
 * This briefly threw when SITE_URL was unset in CI. That was added on a wrong
 * diagnosis: the deploy pipeline was believed to be disconnected, when in fact
 * Cloudflare Workers Builds had been building every push all along. Turning a
 * working pipeline into a failing one to fix a dormant problem is the wrong
 * trade, so it warns instead.
 *
 * The problem it warns about is real but not yet live: with the noindex meta
 * still in place nothing is crawled, so a wrong canonical costs nothing until
 * launch. The old default was a pages.dev domain that does not resolve, which is
 * worse than useless because it looks plausible; localhost is at least obviously
 * not a claim about a public origin.
 *
 * The fix is to hardcode the real origin here. A static site with one domain does
 * not need this to be an environment variable, and the indirection is what let it
 * be wrong unnoticed in the first place.
 */
const site = process.env.SITE_URL ?? (() => {
  if (process.env.CI ?? process.env.WORKERS_CI ?? process.env.CF_PAGES) {
    console.warn(
      "WARNING: SITE_URL is not set, so canonical links and the sitemap will " +
        "point at localhost. Set it in the Cloudflare build variables, or " +
        "hardcode the origin in astro.config.mjs.",
    );
  }
  return "http://localhost:4321";
})();

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

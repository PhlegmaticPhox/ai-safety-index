// @ts-check
import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";
import icon from "astro-icon";

/**
 * The site's own origin, which every canonical link and every sitemap entry is
 * built from. There is no sensible default for it, so there is not one.
 *
 * The previous default was a pages.dev domain that does not resolve, which meant
 * a build with SITE_URL unset shipped canonical links pointing at nothing. That
 * is worse than no canonical link at all, and nothing about the built page looks
 * wrong, so a real build now refuses to start without it.
 *
 * Local development gets localhost, because a dev server is not a deployment and
 * failing there would help nobody.
 */
const CI = process.env.CI ?? process.env.WORKERS_CI ?? process.env.CF_PAGES;
const site = process.env.SITE_URL ?? (() => {
  if (CI) {
    throw new Error(
      "SITE_URL is not set. Set it to the site's own origin, with no trailing " +
        "path, in the Cloudflare build environment (Settings > Variables and " +
        "Secrets > add SITE_URL), or the deployed pages will declare canonical " +
        "links and a sitemap pointing at a domain that is not this one.",
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

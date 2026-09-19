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
  /* sitemap() runs with no options, and the absent one is `serialize`, which is
     how a <lastmod> would be emitted. There is no honest value to put in it.
     Build time is false: the daily refresh rebuilds all 34 pages whether or not
     one record moved, so every URL would claim to have changed most days, which
     is the pattern Google cites for ignoring lastmod entirely. A git commit date
     for the route's source file is wrong for a data page and unreliable in the
     shallow clone Workers Builds checks out. A dataset's `generated` stamp is
     right about the data, but a data page renders two to five datasets and the
     map from route to dataset would have to be hand-maintained here, out of
     reach of the page's own imports and of any check. The honest version of this
     fact already ships: each data page's masthead carries a <time datetime> built
     from oldestRetrieved() over the datasets that page actually imports.

     Phosphor only, one family for the whole project, inlined as SVG at build time
     so icons cost no client JS and no network request. */
  integrations: [mdx(), sitemap(), icon({ include: { ph: ["*"] } })],
  build: {
    // Charts render to SVG at build time, so most pages ship zero client JS.
    inlineStylesheets: "auto",
  },
});

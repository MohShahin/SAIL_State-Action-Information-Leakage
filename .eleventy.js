// Single source of truth for the site's deployed subpath. GitHub Pages project sites are
// served at /<repo-name>/, not domain root -- if this repo is ever renamed again, this is
// the ONLY line that needs to change. Every page's internal links use the __PATHPREFIX__
// marker (see the addTransform below) instead of a hardcoded string, specifically so a
// rename doesn't require touching every one of the ~100 link occurrences across 11 pages
// by hand again.
const PATH_PREFIX = "/SAIL_State-Action-Information-Leakage/";

module.exports = function (eleventyConfig) {
  // Static assets, copied through as-is
  eleventyConfig.addPassthroughCopy({ "src/assets": "assets" });

  // Non-page repo files that pages link out to directly — must be served at the
  // same absolute paths the HTML uses (/paper/..., /notebook/..., /queries/..., etc.)
  eleventyConfig.addPassthroughCopy("paper");
  eleventyConfig.addPassthroughCopy("notebook/*.ipynb");
  eleventyConfig.addPassthroughCopy("queries");
  eleventyConfig.addPassthroughCopy("scripts");
  // results/ -- explicit allowlist matching .gitignore's curated-only policy exactly.
  // A blind directory copy would defeat that policy the same way the earlier
  // notebook/ passthrough did: passthrough copy doesn't know about .gitignore, so
  // any uncommitted extra file sitting in a local results/ folder at build time
  // would ship straight into _site/ regardless of what's actually meant to be public.
  eleventyConfig.addPassthroughCopy("results/README.md");
  eleventyConfig.addPassthroughCopy("results/experiment1_sofa_decomposition_summary.json");
  eleventyConfig.addPassthroughCopy("results/experiment2_action_recoverability_best_probe.csv");
  eleventyConfig.addPassthroughCopy("results/experiment3_summary.json");
  eleventyConfig.addPassthroughCopy("ROADMAP.md");
  eleventyConfig.addPassthroughCopy("DATA_ACCESS.md");
  eleventyConfig.addPassthroughCopy("FORMAL_ANALYSIS.md");
  eleventyConfig.addPassthroughCopy("CITATION.cff");
  eleventyConfig.addPassthroughCopy("LICENSE");
  eleventyConfig.addPassthroughCopy({ ".nojekyll": ".nojekyll" });

  // Single-source-of-truth path prefixing. Every page (including the 10 content files
  // that run with templateEngineOverride: false, which rules out using Nunjucks's own
  // `| url` filter there -- that flag exists specifically to stop Nunjucks from
  // misparsing the literal { and } characters in those pages' inline CSS/JS, and
  // re-enabling template processing just to get `| url` would reopen that exact risk)
  // writes __PATHPREFIX__ instead of a hardcoded path. This transform runs on every
  // page's final rendered HTML, after all templating, and does a plain string
  // replacement -- so it can't be affected by curly braces in CSS/JS either.
  eleventyConfig.addTransform("pathprefix", (content, outputPath) => {
    if (outputPath && outputPath.endsWith(".html")) {
      const bare = PATH_PREFIX.replace(/\/$/, ""); // strip trailing slash for mid-path use
      return content.split("__PATHPREFIX__").join(bare);
    }
    return content;
  });

  return {
    dir: {
      input: "src",
      includes: "_includes",
      output: "_site",
    },
    pathPrefix: PATH_PREFIX,
    htmlTemplateEngine: "njk",
  };
};

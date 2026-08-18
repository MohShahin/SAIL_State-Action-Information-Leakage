module.exports = function (eleventyConfig) {
  // Static assets, copied through as-is
  eleventyConfig.addPassthroughCopy({ "src/assets": "assets" });

  // Non-page repo files that pages link out to directly — must be served at the
  // same absolute paths the HTML uses (/paper/..., /notebook/..., /queries/..., etc.)
  //
  // notebook/ and results/ are passed through as explicit allowlists, not whole-directory
  // copies: notebook/results/ (row-level, gitignored) and any non-curated file under results/
  // must never end up in _site/, even if a future git-add mistake ever committed one. Relying
  // on .gitignore alone would only protect the CI build (checkout never contains those files);
  // a local build run directly against a dev machine's working directory -- e.g. this one, which
  // has real notebook/results/ output on disk -- would otherwise copy patient-level data into
  // _site/ regardless of git history.
  eleventyConfig.addPassthroughCopy("paper");
  eleventyConfig.addPassthroughCopy("notebook/*.ipynb");
  eleventyConfig.addPassthroughCopy("queries");
  eleventyConfig.addPassthroughCopy("scripts");
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

  return {
    dir: {
      input: "src",
      includes: "_includes",
      output: "_site",
    },
    htmlTemplateEngine: "njk",
  };
};

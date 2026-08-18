module.exports = function (eleventyConfig) {
  // Static assets, copied through as-is
  eleventyConfig.addPassthroughCopy({ "src/assets": "assets" });

  // Non-page repo files that pages link out to directly — must be served at the
  // same absolute paths the HTML uses (/paper/..., /notebook/..., /queries/..., etc.)
  eleventyConfig.addPassthroughCopy("paper");
  eleventyConfig.addPassthroughCopy("notebook");
  eleventyConfig.addPassthroughCopy("queries");
  eleventyConfig.addPassthroughCopy("scripts");
  eleventyConfig.addPassthroughCopy("results");
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

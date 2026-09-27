# Website rebuild — phase status

Tracks what's actually shipped versus planned for the website rebuild (`.claude/commands/website-phase-*.md`).
Supersedes `docs/WEBSITE_RESTRUCTURE_PLAN.md`'s two-track `/package/`+`/research/` IA per Phase 0's
standing rule — that file is kept for its historical reasoning, not as the current plan.

| Phase | Status | What it covers |
|---|---|---|
| 0 — Submission infrastructure | **Shipped** (`6ae6dd2`, `921f2b0`) | Three GitHub Issue Form templates, `config.yml` disabling blank issues, `docs/giscus_snippet.html` saved for Phase 4. |
| 1 — Homepage | **Shipped** (`ea7bae3`) | `index.html` rebuilt as a product landing page around the real extension demo GIF. New footer nav (About, Detectors, Papers, Datasets & Models, Privacy, Understanding Leakage) added, but only on the homepage — see the open item below. |
| 2 — About page | Not started | |
| 3 — Detectors page | Not started | The homepage's "Detectors" footer link currently points at the existing `/package/` page as an honest interim target, not a stub. |
| 4 — Comments | Not started | Will embed `docs/giscus_snippet.html`, prepared in Phase 0. |

## Open item: the site-wide top nav still isn't migrated

`src/_includes/base.njk`'s top nav is still the old flat 10-item list (Home, Mechanisms, Visualizer,
Evidence, Showcase, Proof, Reproducibility, Papers, About, Status) on every page **except** the new
homepage footer. This was a deliberate, flagged decision in Phase 1 — migrating all 10 existing pages
to the new 6-item IA in the same phase as "rebuild the homepage" would have been the same kind of
scope creep that has broken this site's links twice before, done under time pressure instead of as
its own reviewed step.

**This needs to happen as its own explicit phase, before or alongside Phase 3** — not bundled
silently into Phase 2, Phase 3, or any other work. Until then, the top nav and the homepage's own
footer nav intentionally disagree, and that's a known, accepted seam, not an oversight.

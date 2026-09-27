# Website rebuild — phase status

Tracks what's actually shipped versus planned for the website rebuild (`.claude/commands/website-phase-*.md`).
Supersedes `docs/WEBSITE_RESTRUCTURE_PLAN.md`'s two-track `/package/`+`/research/` IA per Phase 0's
standing rule — that file is kept for its historical reasoning, not as the current plan.

| Phase | Status | What it covers |
|---|---|---|
| 0 — Submission infrastructure | **Shipped** (`6ae6dd2`, `921f2b0`) | Three GitHub Issue Form templates, `config.yml` disabling blank issues, `docs/giscus_snippet.html` saved for Phase 4. |
| 1 — Homepage | **Shipped** (`ea7bae3`) | `index.html` rebuilt as a product landing page around the real extension demo GIF. Introduced the `.landing-dark` visual system and the new 6-item footer nav, homepage-only at the time. |
| 2 — About page | **Shipped** (`21f4215`) | `about.html` converted to `.landing-dark`. Team and Community sections use explicit, obviously-marked placeholders (dashed border, "Placeholder" tag) — no fabricated names, bios, photos, or projects. One real Team card (Mohammad Shahin, from `CITATION.cff`). |
| 3 — Header/nav unification | **Shipped** (`ef6742b`) | `base.njk`'s shared header re-themed to `.landing-dark` with the logo, applied identically across all 15 pages. Nav trimmed to the 5 pages that actually exist today (Home, About, Papers, Datasets & Models, Privacy) — Detectors and Understanding Leakage deliberately left out, since those pages don't exist yet (see the new open item below). Closes the "site-wide top nav still isn't migrated" item this doc previously tracked. |
| 4 — Comments | Not started | Will embed `docs/giscus_snippet.html`, prepared in Phase 0. |
| Detectors page | Not started | The "Detectors" nav item doesn't exist yet — `/package/` (which already documents the five detectors in depth) is the honest interim target used wherever a link needs to point somewhere real, e.g. the homepage's "What it checks" teaser. |
| Understanding Leakage | Not started | No nav entry yet. `/research/` already serves this role as the existing research hub page and is linked from the homepage's own footer. |

## Open item: eight pages still carry the old light-theme content

Phase 3 unified the *header* only, exactly as scoped. The content area of these 8 pages is still the
original light theme, not yet converted to `.landing-dark`: `proof.html`, `mechanisms.html`,
`evidence.html`, `visualizer.html`, `reproducibility.html`, `status.html`, `demo.html`,
`showcase.html`. The dark-header-over-light-content seam on these pages is a known, accepted interim
state (verified by screenshot to read as a deliberate two-tone transition, not a rendering error),
not an oversight.

**This needs to happen as its own explicit, tracked phase** — reskinning eight pages' worth of
content is real work (tables, math, callout blocks, the interactive visualizer) and doing it
piecemeal inside another phase risks the same kind of undertested change that Phase 3 itself had to
catch and fix once already (a real mobile nav-wrapping bug, found and fixed before shipping — see the
Phase 3 commit message).

## Open item: no nav entry yet for Detectors or Understanding Leakage

Both concepts have a real, existing page they can point to today (`/package/`, `/research/`) but
neither has a dedicated nav slot, because giving them one before their purpose-built pages exist would
either be misleading (a "Detectors" link that's really the package's install/quickstart page) or
require deciding page-existence questions ahead of the phase meant to answer them. Add these once
their real pages ship.

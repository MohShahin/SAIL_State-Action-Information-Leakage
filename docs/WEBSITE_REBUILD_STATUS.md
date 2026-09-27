# Website rebuild — phase status

Tracks what's actually shipped versus planned for the website rebuild (`.claude/commands/website-phase-*.md`).
Supersedes `docs/WEBSITE_RESTRUCTURE_PLAN.md`'s two-track `/package/`+`/research/` IA per Phase 0's
standing rule — that file is kept for its historical reasoning, not as the current plan.

| Phase | Status | What it covers |
|---|---|---|
| 0 — Submission infrastructure | **Shipped** (`6ae6dd2`, `921f2b0`) | Three GitHub Issue Form templates, `config.yml` disabling blank issues, `docs/giscus_snippet.html` saved for Phase 4. |
| 1 — Homepage | **Shipped** (`ea7bae3`) | `index.html` rebuilt as a product landing page around the real extension demo GIF. Introduced the `.landing-dark` visual system and the new 6-item footer nav, homepage-only at the time. |
| 2 — About page | **Shipped** (`21f4215`) | `about.html` converted to `.landing-dark`. Team and Community sections use explicit, obviously-marked placeholders (dashed border, "Placeholder" tag) — no fabricated names, bios, photos, or projects. One real Team card (Mohammad Shahin, from `CITATION.cff`). |
| 3 — Header/nav unification | **Shipped** (`ef6742b`) | `base.njk`'s shared header re-themed to `.landing-dark` with the logo, applied identically across all 15 pages. Nav trimmed to the 5 pages that actually exist today (Home, About, Papers, Datasets & Models, Privacy) — Detectors deliberately left out, since that page didn't exist yet. Closes the "site-wide top nav still isn't migrated" item this doc previously tracked. |
| 4 — Detectors | **Shipped** (`afa9260`) | New `/detectors/` page, five cards reusing `SAIL_PACKAGE_README.md`'s table and the detectors' own docstring/explanation text verbatim. Each "See the math" link deep-links to the exact proof/evidence anchor (verified to land on the right heading, not just a non-404 URL) — including one, construction leakage's Proposition 3 shape, that has no in-site anchor and links to the live GitHub-rendered `FORMAL_ANALYSIS.md` instead, and one, persistence dominance, for which a `evidence.html#variant-f` anchor was added since none existed. "Detectors" added to the shared nav; the homepage's "What it checks" teaser now points here instead of `/package/`. |
| 5 — Libraries | **Shipped** (`77ed43a`) | `papers.html` re-skinned into a card grid (the real 8 citations, tag-filter and self-check tool reused as-is, not rewritten); `datasets-and-models.html` given a genuine empty-state design instead of prose, since it has zero real entries. Giscus embedded on both pages from Phase 0's `docs/giscus_snippet.html`; confirmed with real evidence (each page's injected iframe URL, not assumed) that `data-mapping: pathname` gives them separate comment threads. "Suggest a paper" / "Submit a dataset or model" now use the same live `?template=` URL pattern as Phase 4's "Suggest a new detector." |
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

## Open item: no nav entry yet for Understanding Leakage

`/research/`, the existing research hub page, already serves this role and is linked from the
homepage's own footer, but has no dedicated nav slot yet — add one once a purpose-built page exists,
same reasoning Phase 4 just resolved for Detectors.

## Open item: none of the three `?template=` submission links' exact rendering was visually verified

The Detectors, Papers and Datasets & Models pages' submission buttons all point to
`.../issues/new?template=<filename>.yml` (GitHub's standard, documented query-string format for issue
forms). Confirming any of them actually opens with the right template pre-selected requires a
signed-in GitHub session — the same `issues/new*` sign-in wall Phase 0 hit, with no workaround found
there either. Each filename and path is confirmed correct (verified live in Phase 0); only the
query-string behavior itself is unverified, for all three identically.

# Website rebuild — phase status

Tracks what's actually shipped versus planned for the website rebuild (`.claude/commands/website-phase-*.md`).
Supersedes `docs/WEBSITE_RESTRUCTURE_PLAN.md`'s two-track `/package/`+`/research/` IA per Phase 0's
standing rule — that file is kept for its historical reasoning, not as the current plan.

| Phase | Status | What it covers |
|---|---|---|
| 0 — Submission infrastructure | **Shipped** (`6ae6dd2`, `921f2b0`) | Three GitHub Issue Form templates, `config.yml` disabling blank issues, `docs/giscus_snippet.html` saved for Phase 4. |
| 1 — Homepage | **Shipped** (`ea7bae3`) | `index.html` rebuilt as a product landing page around the real extension demo GIF. Introduced the `.landing-dark` visual system and the new 6-item footer nav, homepage-only at the time. |
| 2 — About page | **Shipped** (`21f4215`, updated `4ae3c11`) | `about.html` converted to `.landing-dark`, placeholder pattern established (dashed border, "Placeholder" tag) — no fabricated names, bios, photos, or projects. Updated later with DOJO's real team framing (verified live) and two real Team cards (Leo Anthony Celi, PI, LinkedIn confirmed live; Mohammad Shahin, Project Lead, from `CITATION.cff`), plus two real Community cards (Bodhi, DOJO — both confirmed live). One placeholder card kept in each grid for remaining slots. |
| 3 — Header/nav unification | **Shipped** (`ef6742b`) | `base.njk`'s shared header re-themed to `.landing-dark` with the logo, applied identically across all 15 pages. Nav trimmed to the 5 pages that actually exist today (Home, About, Papers, Datasets & Models, Privacy) — Detectors deliberately left out, since that page didn't exist yet. Closes the "site-wide top nav still isn't migrated" item this doc previously tracked. |
| 4 — Detectors | **Shipped** (`afa9260`) | New `/detectors/` page, five cards reusing `SAIL_PACKAGE_README.md`'s table and the detectors' own docstring/explanation text verbatim. Each "See the math" link deep-links to the exact proof/evidence anchor (verified to land on the right heading, not just a non-404 URL) — including one, construction leakage's Proposition 3 shape, that has no in-site anchor and links to the live GitHub-rendered `FORMAL_ANALYSIS.md` instead, and one, persistence dominance, for which a `evidence.html#variant-f` anchor was added since none existed. "Detectors" added to the shared nav; the homepage's "What it checks" teaser now points here instead of `/package/`. |
| 5 — Libraries | **Shipped** (`77ed43a`) | `papers.html` re-skinned into a card grid (the real 8 citations, tag-filter and self-check tool reused as-is, not rewritten); `datasets-and-models.html` given a genuine empty-state design instead of prose, since it has zero real entries. Giscus embedded on both pages from Phase 0's `docs/giscus_snippet.html`; confirmed with real evidence (each page's injected iframe URL, not assumed) that `data-mapping: pathname` gives them separate comment threads. "Suggest a paper" / "Submit a dataset or model" now use the same live `?template=` URL pattern as Phase 4's "Suggest a new detector." |
| 6 — AI-agent readability | **Shipped** (`2bb65c3`) | `/llms.txt` (real spec structure: H1, blockquote, four H2 file-list sections, verified programmatically), `/robots.txt` (explicit `Allow: /` for named AI crawlers — see the open item below on where this file actually sits), and a `SoftwareApplication`/`SoftwareSourceCode` JSON-LD block on the homepage, validated against the real `validator.schema.org` (0 errors, 0 warnings, driven live, not just checked as syntactically-valid JSON). `SAIL_PACKAGE_README.md` is now passthrough-copied and served for the first time, since `llms.txt` needed a real URL for it. Audited `showcase.html`'s six-variant chart for a text-reading agent: the key finding is already stated in prose right after the chart (verified, not assumed) — no fix needed. |
| 7 — Privacy & HIPAA | **Shipped** (`d838b9d`) | `privacy.html` converted to `.landing-dark` (was still Phase 1's light-theme placeholder). Sourced entirely from `extension/docs/PHASE_5_DATA_SHARING.md`, the canonical source — its Tier 1/2/3 table reproduced and diffed cell-by-cell against the source after the build (byte-identical wording, confirmed programmatically). New HIPAA section, explicitly framed as architecture-not-certification, hedged in `DATA_ACCESS.md`'s own already-established style rather than new phrasing. |
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

## Note: `robots.txt` sits at a non-authoritative path, by necessity of GitHub Pages project sites

`/robots.txt` is served at `/SAIL_State-Action-Information-Leakage/robots.txt`, not at the site's
true origin root (`mohshahin.github.io/robots.txt`) — which we cannot publish to at all under this
hosting setup (that would require a separate `mohshahin/mohshahin.github.io` user-site repo, which
doesn't exist). Standard crawlers, per the Robots Exclusion Protocol, only check the origin root.
Checked live: `mohshahin.github.io/robots.txt` returns GitHub's "Site not found" — there is no
origin-root site at all, which itself already means every well-behaved crawler treats this whole
origin, including this project's path, as fully open by default. This project's `robots.txt` is
still worth having (self-documenting, and some tools do check nested paths), but its explicit
`Allow:` directives are not the thing actually granting access — the absence of any origin-root file
already does that.

## Note: two small discrepancies found and corrected during the About-page team/community update

The update instructions quoted Bodhi's and DOJO's meta-descriptions slightly short (missing "BODHI
is an"/"DOJO is an" and, for Bodhi, its trailing "The courage to ask before answering." tagline).
Fetched both pages live and used their actual, complete text instead of the quoted paraphrase.
Separately, the Leo Anthony Celi LinkedIn sanity check confirmed MIT, Massachusetts Institute of
Technology, an explicit "MIT Critical Data" mention, and Cambridge, MA from the page's public
(unauthenticated) content — but did not find "Beth Israel Deaconess" specifically, likely because
detailed employment history is gated behind a LinkedIn login. Published anyway on the strength of the
other matches, but that one specific detail is not independently confirmed — worth a manual check by
someone with LinkedIn access if full certainty matters.

## Open item: none of the three `?template=` submission links' exact rendering was visually verified

The Detectors, Papers and Datasets & Models pages' submission buttons all point to
`.../issues/new?template=<filename>.yml` (GitHub's standard, documented query-string format for issue
forms). Confirming any of them actually opens with the right template pre-selected requires a
signed-in GitHub session — the same `issues/new*` sign-in wall Phase 0 hit, with no workaround found
there either. Each filename and path is confirmed correct (verified live in Phase 0); only the
query-string behavior itself is unverified, for all three identically.

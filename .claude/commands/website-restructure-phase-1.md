---
description: Website restructuring Phase 1 — Swiss design tokens, drop the homepage's Tailwind CDN dependency, build the two-track gateway homepage + real /package/ page + /research/ hub, without moving any existing page's URL
---

# Website restructure, Phase 1

**Scope discipline for this phase specifically:** this phase creates new pages and new tokens. It
does not move, rename, or restructure any of the 11 existing pages' URLs — that's Phase 3, with its
own dedicated link-crawl verification. If Phase 1 is done correctly, a full link crawl afterward
should show the exact same set of existing internal links working as before, plus new ones for the
two new pages.

## Step 0 — Fix the stale repo URL (quick, isolated, already found)

The README badge and `CITATION.cff` reference a pre-`__PATHPREFIX__`-era repository URL. Grep both
files, confirm the actual current repo URL (check `.eleventy.js`'s `PATH_PREFIX` and the working
`git remote -v` for ground truth, don't assume), fix both, verify the corrected URLs actually
resolve with a `curl` check. Commit this alone, separate from everything else in this phase — it's
an unrelated bug that happened to surface during verification, not part of the redesign itself.

## Step 1 — Define the design tokens in `assets/style.css`

Add, as CSS custom properties, documented with a comment explaining the *rule* for each, not just
the value:
- The modular type scale: `--text-xs: 12px` through `--text-5xl: 49px` (the 8-step scale from
  `docs/WEBSITE_RESTRUCTURE_PLAN.md`).
- The 8px spacing scale: `--space-1: 8px` through at least `--space-8: 64px`, plus a `--space-half:
  4px` for the tightest cases.
- A comment block directly above the existing `--accent`/`--treat`/`--physio` (cyan/red/teal)
  definitions stating the discipline explicitly: cyan is the only brand/navigation accent; red and
  teal are reserved for semantic status (flagged/clean) and must never be used decoratively. This
  comment is what Phase 4's audit will check pages against later — write it precisely enough to be
  a real rule, not a vague aspiration.

Do not yet retrofit these tokens onto the 11 existing pages — that's Phase 3. This step only
defines them and uses them in what Step 2–4 build new.

## Step 2 — Rebuild `index.html` as the two-track gateway

Remove the `<script src="https://cdn.tailwindcss.com">` tag and every Tailwind utility class
entirely. Rebuild using `assets/style.css` and the new tokens from Step 1, matching how every other
page on the site already works — this page should no longer be a structural outlier.

Content, using the 12-column grid from the plan:
1. A hero: the project's one-sentence finding (reuse the exact wording already established
   elsewhere on the site — check `about.html`'s novelty framing for the precise language, don't
   redraft it from scratch and risk drifting from the already-reviewed version).
2. The install command, shown prominently — `pip install sail-leakage`, verified working.
3. Two clearly distinct paths, visually equal weight, not one primary and one afterthought:
   **"Use the package →"** linking to `/package/`, and **"Read the research →"** linking to
   `/research/`.
4. Keep it short. This is a gateway page, not a full explanation of either track — the temptation
   to over-explain here should be resisted; that's what the two tracks are for.

## Step 3 — Build `/package/` (real content, not a stub)

Since the package is fully built, tested, and published, this page can be complete now, not a
placeholder for Phase 2 to finish:
- The install command.
- The exact Quickstart code block from `SAIL_PACKAGE_README.md` — re-extract and re-run it as part
  of this phase's verification (Step 5), the same discipline used every time this code block has
  been touched before.
- The five-category table, reusing the exact content from `SAIL_PACKAGE_README.md`'s table —
  don't rewrite the category descriptions a second time and risk two slightly different versions
  existing.
- Links to the PyPI project page and the GitHub repository.
- A closing link to `/research/` for anyone who wants the underlying proofs.

## Step 4 — Build `/research/` (a hub, not a migration)

A single new page that:
1. States plainly what this track is: the formal proofs, the empirical audit, and the honest
   account of what's still open.
2. Links out to all 8 existing research pages **at their current, unchanged URLs**
   (`/mechanisms/`, `/proof/`, `/evidence/`, `/demo/`, `/visualizer/`, `/showcase/`, `/status/`,
   `/reproducibility/`) — do not move or rename any of them in this phase.
3. A closing link back to `/package/` for anyone who arrived here first but actually wants the tool.

## Step 5 — Verify

1. Full clean build, zero errors.
2. Full internal link crawl — confirm the exact same existing links still work (nothing broken by
   this phase) plus the new links from the homepage, `/package/`, and `/research/`.
3. Grep confirms the Tailwind CDN script tag is completely gone from `index.html`.
4. Re-extract and re-run `/package/`'s Quickstart code block from a real install, confirming output
   matches what's already verified.
5. Render all three new/changed pages at both desktop and mobile widths — confirm no overflow,
   confirm the two-path homepage layout reads clearly at both sizes.
6. `git diff --stat` against `main` before committing — confirm only the expected files changed
   (`assets/style.css`, `index.html`, `README.md`, `CITATION.cff`, plus two new page files). If
   anything else shows as modified, stop and explain why before committing.

## Reporting

Report Step 0's fix separately. Report the final homepage/`/package/`/`/research/` structure, the
link-crawl result, and the `git diff --stat` output before this gets committed.

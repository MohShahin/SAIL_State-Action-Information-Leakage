# SAIL Website Restructuring — Plan

## The real problem to solve first, before any visual decision

The site currently has one flat, ten-item nav trying to serve two genuinely different visitors:
someone who wants to `pip install` a tool and start using it in five minutes, and someone who wants
to verify a mathematical proof before trusting it. Mashing both into one navigation flow is the
actual thing standing between this site and "Verily-level" — not the typeface.

**Decision: split into two clearly labeled tracks from the homepage, not one long nav.**

```
/                    — the gateway: one sentence, one install command, two paths
/package/            — install, quickstart, the five categories as reference, changelog
  /package/install/
  /package/categories/
/research/           — everything that exists today, reorganized under one banner
  /research/mechanisms/  (was /mechanisms/)
  /research/proof/       (was /proof/)
  /research/evidence/    (was /evidence/)
  /research/demo/        (was /demo/)
  /research/visualizer/  (was /visualizer/)
  /research/showcase/    (was /showcase/)
  /research/status/      (was /status/)
/papers/             — stays as-is, arguably belongs equally to both tracks, keep at top level
/about/              — stays at top level
```

This is a real information-architecture decision, not cosmetic — it lets a package-only visitor
never see a proof page unless they choose to, and lets a reviewer skip the install instructions
entirely, without either group scrolling past content meant for the other.

**A URL-restructuring caution, given this project's own history:** the site has already been bitten
once by GitHub Pages subpath issues and once by a hardcoded-vs-`__PATHPREFIX__` maintainability
regression. Moving pages under `/research/` means every internal link site-wide needs updating, the
`__PATHPREFIX__` transform still needs to resolve correctly, and every external link anyone's
already shared (the PyPI README's "Homepage" link, `about.html`, `CITATION.cff`) needs checking. This
is exactly the kind of change that needs the same link-crawl discipline as the Eleventy migration,
not assumed to "just work" because the transform pattern exists.

---

## The Swiss design system — concrete tokens, not a vibe

Swiss (International Typographic Style) design is about **discipline and restraint that make
information easier to trust**, not decoration. Every token below is chosen because it serves that,
not because it looks clean in isolation.

### Typography

- **One typeface family, no exceptions:** Inter, already in use — a legitimate neo-grotesque in the
  Helvetica/Akzidenz-Grotesk lineage, so no font change needed. What changes is discipline: remove
  any lingering serif usage, commit fully.
- **A real modular scale**, not per-page arbitrary sizing: `12 / 14 / 16 / 20 / 25 / 31 / 39 / 49px`
  (roughly 1.25 ratio). Every heading and body size site-wide maps to one of these — no more, no
  fewer.
- **Three weights only:** 400 (body), 600 (emphasis, subheads), 800 (display — hero and page titles
  only, used sparingly). Cut whatever weight sprawl has accumulated across the many separate build
  sessions this site has had.
- **Tight tracking on large display type**, generous line-height on body text — the classic Swiss
  contrast between headline density and reading comfort.

### Grid and spacing

- **A strict 12-column grid**, fixed max-width, consistent gutter — replacing the current somewhat
  ad hoc `wide-w`/`prose-w` containers with an actual grid system content aligns to.
- **An 8px base spacing unit.** Every margin, padding, and gap is a multiple of 8 (or 4 for the
  tightest cases). This is the single change most responsible for a site suddenly looking
  "considered" rather than "assembled over many sessions" — inconsistent spacing is the most common
  tell of exactly that.

### Color — discipline, not a new palette

The existing palette is already close to right; the fix is *rules for when each color is allowed*,
not new colors:
- White dominant, near-black ink (`#0F172A`, unchanged) for text — this is already correct.
- **Cyan (`#0891B2`) is the one brand/navigation accent** — links, active states, primary CTAs.
  Nothing else uses it.
- **Red and teal are reserved strictly for semantic status** (flagged / clean, established
  site-wide including in the published PyPI README) — never used decoratively, never as general UI
  chrome. Right now they occasionally drift into that use; the fix is auditing and tightening, not
  changing what they mean — the meanings are load-bearing across pages that already shipped.
- Everything structural (borders, dividers, backgrounds) is grayscale.

### Diagrams — one visual language, not five

The DAGs and charts across `proof.html`, `mechanisms.html`, `visualizer.html`, and `showcase.html`
were built in different sessions and likely have small inconsistencies (stroke width, corner
radius, arrow style, node sizing). Swiss design's diagram tradition (think Otl Aicher's pictogram
systems) is about exactly this kind of unification — one precise visual grammar reused everywhere,
never reinvented per-page. This is a real audit-and-normalize task, not a redraw.

---

## Phased execution

**Phase 1 (highest leverage, do first):** Define the actual design tokens as CSS custom properties
and utility classes in `assets/style.css`, then rebuild the homepage as the two-track gateway. This
is what Verily sees first, and it's the one page that most directly proves the new system works
before it's applied everywhere else.

**Phase 2:** Build the `/package/` track's new content — install, quickstart, categories reference
— using Phase 1's tokens from the start, no retrofit needed since it's new.

**Phase 3:** Reskin the `/research/` track's existing pages to the new tokens (typography, grid,
spacing) without touching their actual content — this is lower-risk than it sounds, since the
underlying proofs and evidence are already verified; only the visual layer changes. Includes the
URL restructuring and the full link-crawl re-verification that requires.

**Phase 4:** The diagram-unification audit and normalization pass across all SVGs.

**Phase 5:** Full-site verification — reuse the `/verify-site` and `/status-check` patterns already
built this session, extended to cover the new `/package/` and `/research/` structure.

Given Oct 7, Phases 1–2 are the ones that most need to land; Phases 3–5 can extend past the
deadline if needed without leaving the site in a broken state, since Phase 1's homepage works
correctly even before the research pages are reskinned — they'd just look like an older, still
fully functional design until their turn comes.

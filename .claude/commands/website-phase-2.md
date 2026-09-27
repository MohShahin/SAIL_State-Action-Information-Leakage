---
description: Phase 2 — About page structure, with clearly marked placeholders for team and related lab content the user will supply
---

# Website rebuild, Phase 2 — About

**Do not invent any team member, bio, photo, or lab project.** Every placeholder in this phase must
be visually and textually obvious as a placeholder — not styled to look like finished content — so
nothing fabricated could be mistaken for real information if this ships before the real content
arrives.

## Step 1 — Read before writing

Read `src/about.html` (the existing About page) for the already-reviewed novelty framing and
project description — reuse that content, don't redraft it. Read `CITATION.cff` for the one
confirmed-real author name already in the repo.

## Step 2 — Build the page structure

Sections, in order:
1. **Project summary** — reuse the existing, already-correct novelty/project framing from the
   current `about.html`, adapted to the new dark product-page visual system from Phase 1.
2. **Team** — a card grid. For each card, a clearly labeled placeholder state: a generic silhouette
   icon (not a fabricated photo), "Name" / "Role" as literal placeholder text in a visually distinct
   style (e.g., dashed border, muted color, a small "placeholder" tag), and an HTML comment
   explaining exactly what real content goes here (name, role, one-line bio, photo path). Include at
   least one real card if `CITATION.cff` gives enough to populate one accurately — otherwise all
   placeholders.
3. **Community & related work** — same placeholder treatment: a card grid for "other lab projects
   worth seeing," each a dashed-border placeholder card, with a comment describing the expected
   shape (project name, one-line description, link, optional screenshot).
4. Both sections should be trivially easy to fill in later — comment each placeholder card with the
   exact fields expected, so replacing them doesn't require re-reading this command's spec.

## Step 3 — Verify

Full clean build, link crawl (reuse the same crawler as Phase 1), screenshots at desktop and mobile
widths confirming the placeholder cards are visually obvious as placeholders, not mistakable for
finished content.

## Reporting

Report the final page structure and confirm explicitly: no fabricated names, bios, photos, or lab
projects exist anywhere in this phase's output.

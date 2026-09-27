---
description: Phase 6 — AI-agent readability (llms.txt, robots.txt for AI crawlers, structured data), so an agent pointed at this site can correctly integrate sail-leakage rather than guess or hallucinate its API
---

# Website rebuild, Phase 6 — AI-agent readability

**Explicitly out of scope, and worth stating plainly rather than leaving ambiguous:** this is not
about letting agents perform actions on the site (booking, purchasing, form submission via an
API) — that's a different, much larger standard (WebMCP) this project has no use case for. This
phase is about making the site's *content* efficiently and correctly readable by an agent that's
trying to help someone integrate `sail-leakage` or the VS Code extension into their own project.

## Step 1 — `llms.txt`, following the real published spec exactly

Read `https://llmstxt.org/` for the actual current spec before writing this — structure matters:
H1 title first, a blockquote 1–3 sentence summary, then H2 sections with markdown link lists (each
link optionally annotated with a short description).

Content, sourced from what's already real — do not draft new descriptions:
1. H1: `SAIL`
2. Blockquote: reuse the project's existing one-sentence framing, not a new one.
3. H2 "Package" — links to: the exact `sail.check()` signature and parameters (point at
   `SAIL_PACKAGE_README.md`'s Quickstart, which is the verified-working version, not the earlier
   draft that had a bug), the install command, the five detector categories with their real names.
4. H2 "VS Code extension" — install path, what it does, linking to `extension/README.md`.
5. H2 "Research" — links to `FORMAL_ANALYSIS.md` and the site's proof/evidence pages, for an agent
   that needs to justify *why* a check exists, not just *how* to call it.
6. H2 "Optional" — lower-priority links (About, community pages) an agent can skip under context
   pressure, per the spec's own convention for this section.

Place at the site root so it resolves at `/llms.txt`.

## Step 2 — `robots.txt`

Check whether one currently exists (GitHub Pages doesn't add one by default — confirm rather than
assume). Create or update one that explicitly does not block known AI-agent crawlers (GPTBot,
ClaudeBot, PerplexityBot, and others) — the goal is readability, so this should be permissive by
default for content-reading crawlers, not restrictive.

## Step 3 — Structured data (JSON-LD)

Add a `SoftwareApplication` (or `SoftwareSourceCode`, whichever fits better — check schema.org's
actual definitions rather than guessing) JSON-LD block to the homepage: real package name, real
PyPI URL, real repository URL, real license, real description reused from the README. This is a
well-established, low-risk addition — inline `<script type="application/ld+json">` in the page
head, no build-system changes needed.

## Step 4 — Audit for content that's invisible to a text-reading agent

Check whether any page's key finding exists *only* as an image or interactive chart with no plain-
text equivalent nearby — the six-variant purity/recoverability chart on `showcase.html` is the most
likely candidate (an agent fetching raw HTML may not extract meaning from an SVG the way a human
sees it visually). Where this is true, confirm there's already a text sentence stating the finding
plainly nearby (Phase reports suggest there is — verify, don't assume) — add one if genuinely
missing, but don't rewrite content that already states the finding in words.

## Step 5 — Verify

1. Fetch the real, deployed `/llms.txt` and confirm it renders as valid, parseable Markdown matching
   the spec's required structure (H1 first, blockquote present).
2. Confirm `robots.txt` doesn't accidentally block anything important — check it against the actual
   site's URL structure.
3. Validate the JSON-LD block with a real schema validator, not just checking it's syntactically
   valid JSON.
4. Full clean build, link-crawl, confirm nothing else broke.

## Reporting

Report the final `llms.txt` content in full (it should be short enough to review at a glance — if
it isn't, it's probably including too much), confirm the JSON-LD validated, and report Step 4's
audit findings explicitly.

---
description: Remove a leaked internal-reasoning comment from the About page, and sweep the whole site for similar artifacts
---

# Fix: leaked internal comment

## Step 1 — Remove the specific instance

Find and remove the visible text "Two real projects from the same MIT Critical Data lab family,
both confirmed live before listing here." (or any close variant) from the About page. This reads
as an internal verification note meant to justify a decision during the build, not user-facing
copy — it should not be rendered on the page at all. If the surrounding content needs a transition
sentence in its place, keep it minimal and factual (e.g. nothing, or just the section heading) —
don't invent replacement marketing copy.

## Step 2 — Sweep for the same class of bug elsewhere

Grep the entire built site for other phrases that read like internal build notes rather than
content meant for a visitor — patterns like "confirmed," "verified live," "checked before," "per
the phase brief," "as instructed" appearing in rendered page text (not code comments, not this
project's own docs/ files, which are fine as they are). Report every hit found, with enough context
to judge whether it's a genuine leak or a legitimate use of that word in real content (e.g., "we
verified this on 11,354 real ICU stays" is legitimate; "confirmed live before listing here" is not).

## Step 3 — Verify

Full clean build, confirm the removed text is gone from the built output, screenshot the affected
section to confirm it reads cleanly without it.

## Reporting

Report what was removed, and report Step 2's sweep results in full — including anything judged a
false positive, so the judgment call is visible, not silent.

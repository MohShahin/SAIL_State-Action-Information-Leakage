---
description: Prepare and verify a synthetic demo dataset and full click-through flow for a live Verily presentation
---

# Verily demo preparation

**Every result shown in the demo must be genuinely computed, not staged.** The goal is a synthetic
dataset structured realistically enough that the real detectors produce real flagged/not-flagged
results — not a fabricated report dressed up to look like one.

## Step 1 — Build a synthetic dataset that exercises multiple real categories

Design a synthetic CSV, clearly labeled as synthetic in a header comment, shaped like the SOFA
cardiovascular structure (so it triggers the wizard's real construction-leakage preset detection —
`map`, plus at least one of `dopamine`/`dobutamine`/`epi`/`norepi`), with enough rows and enough
treatment-active variation to produce a genuine, non-trivial `construction_leakage_1a` flag. Include
columns that support setting up a real reconstruction-leakage check (a total column, a target
component, remaining components) so that category can be configured and flagged live during the
demo, not skipped. Document exactly how this file was constructed and why it's expected to flag,
so the presenter (not just the tool) understands what's about to happen and why, before presenting
it to anyone.

## Step 2 — Full dry run, end to end, exactly as it will be presented

Using the real extension (not a shortcut), walk the entire flow: open the wizard, browse to the
synthetic file (not "Try with example data" — the point is showing it work on a file someone picked
themselves), confirm auto-detected columns, accept the construction-leakage preset, set up the
reconstruction check via column picks, enter two illustrative persistence-check numbers, run, and
confirm the results view shows a real, multi-category result — some flagged, some not, some
correctly reported as not-run where the setup genuinely doesn't support them (this honesty is
itself worth keeping visible in the demo, not hidden).

## Step 3 — Demonstrate the plain-language error path deliberately

As part of the same dry run, also try pointing the wizard at a nonexistent or malformed file once,
and confirm the plain-language error banner (with the raw exception preserved underneath) renders
correctly — this becomes a deliberate beat in the demo script, not something to avoid.

## Step 4 — Confirm the export-to-HTML report works from this real run

Export the report from this actual run, open the resulting HTML file in a real browser, confirm it
renders correctly standalone.

## Step 5 — Reliability check for a live presentation specifically

1. Time the full flow from a cold VS Code launch — this determines how much of the demo happens
   live versus how much should be pre-warmed before Verily arrives.
2. Confirm the flow works with no internet connection active (the package and extension are local-
   only — verify this claim holds under an actual disconnected test, not assumed from architecture
   alone, given a venue's network is a realistic point of failure).
3. Take clean screenshots of every step of this successful run, as a fallback if anything about the
   live environment misbehaves in the room.

## Reporting

Report the synthetic dataset's exact structure and why it produces the results it does, confirm
the full dry run's actual results (not idealized ones), and report the offline-reliability check's
outcome explicitly.

---
description: Full-site audit against all team feedback (Ryohei, clinical reviewer, Dimitris), close any gaps, then build the honest showcase-demo pieces
---

# Site consistency audit and showcase readiness

This has two parts. **Do Part 1 completely, and report its findings in full, before touching any
file in Part 2 or Part 3.** The temptation on a task like this is to fix things as they're found —
resist it. A single reported gap-list is what lets a human sanity-check the scope before edits
start, the same discipline every phase in this project has used before making changes.

---

## Part 1 — Audit (read-only, no edits yet)

Grep and read every page in `src/`, `FORMAL_ANALYSIS.md`, `papers.html`, and `ROADMAP.md` against
this checklist. For each item, report **present / stale / absent**, with the exact file and line —
not a summary judgment.

### 1a. Terminology consistency (Ryohei's critique — Phase 0)

- Search every page in `src/` for standalone uses of "leakage," "contamination," or "corrupted"
  that describe Mechanisms 1/2 or the SOFA-cardio/respiratory findings *without* the corrected
  framing (treatment-confounded severity construction / treatment overlap). The word "leakage" is
  fine in the project's own name and in genuinely reserved uses (true target/future-action
  leakage, H3's open question) — flag only where it's used loosely for what are now known to be
  ordinary treatment-history mechanisms.
- Search for "physiology-only" (the old Variant E name) anywhere it wasn't caught by the earlier
  rename — it should read "no explicit treatment features" everywhere, including chart labels,
  table headers, and any inline JS strings (not just prose — the earlier terminology pass may have
  missed JS-embedded variant labels the same way the `__PATHPREFIX__` fix once missed
  JS-embedded paths).
- Confirm `visualizer.html`'s captions specifically distinguish past/current treatment information
  from target/future-action information, per Ryohei's explicit critique of that page. Quote its
  current caption text.
- Confirm `mechanisms.html` (the main mechanism explainer) reflects the corrected terminology
  throughout, not just in whichever section was edited first.

### 1b. Findings completeness — is everything actually on the site?

For each of the following, report whether it appears on `evidence.html`, `mechanisms.html`, and
`status.html` (the three natural homes), not just in `FORMAL_ANALYSIS.md`:
- Proposition 3 / Experiment 7 (respiratory SOFA, the score-shift collision)
- Experiment 6 (mortality-predictive validity per variant, the 0.109-vs-0.011 gap finding)
- Experiment 8 / Variant F (the falsified disentanglement hypothesis, and its connection to the
  persistence/Ryohei discussion per the last follow-up round)
- The corrected Theorem 1 (nonzero-dose domain, not "crosses a threshold")

### 1c. Literature and citations

- Check `papers.html` for Daoud, Jerzak & Johansson (2022/2026, treatment leakage in text-based
  causal inference) and Tang, Yao, Wiens & Parbhoo (2026, "Off by a Beat") — both were identified
  as necessary additions in `docs/PI_DEFENSE_PREP.md` §2.2. Report whether they're present.
- Check whether the Robins g-methods / treatment-confounder-feedback citation (also flagged as a
  required addition in `docs/PI_DEFENSE_PREP.md` §6, Reviewer 2's table) was ever added anywhere —
  `FORMAL_ANALYSIS.md`, `papers.html`, or `about.html`.

### 1d. Novelty framing (Phase 1)

Check `papers.html`, `about.html`, and `index.html`'s novelty-adjacent language against the
specific framing from `docs/PI_DEFENSE_PREP.md` §2.3 and the clinical reviewer's point 1: the
novelty is that offline-RL pipelines use a therapy-dependent score as pre-decision state without
accounting for it, and Theorem 2 is the least clinician-known finding. Report whether this exact
framing is present or whether the pages still lean on a bare "leakage" claim to carry the novelty.

### 1e. Roadmap

Check `ROADMAP.md` for the two future-paper directions from the last follow-up round (vasopressor
weaning, and the duration/recency-predicts-treatment-persistence finding). Report present/absent.

**End of Part 1. Report the complete gap list now, organized by file, before proceeding.**

---

## Part 2 — Close the gaps (only after Part 1 is reported)

Fix each reported gap, as separate commits grouped by file or logical change — matching this
project's established one-focused-commit pattern. For the terminology sweep specifically, prefer a
scripted find-and-verify approach (like the earlier `__PATHPREFIX__` migration) over manual
per-file edits, since manual edits are exactly what produced the gaps being fixed now. Re-run the
full-site grep from 1a after fixing to confirm zero remaining stale instances, the same way the
`PATHPREFIX` fix was verified with a final sweep rather than assumed complete.

**Do not silently expand scope while fixing** — if closing a gap reveals a genuinely new question
(e.g., a page makes a claim that turns out to be wrong once corrected terminology is applied), stop
and report it rather than deciding how to resolve it unprompted.

---

## Part 3 — Showcase readiness (only after Part 2's fixes are committed and pushed)

Per `docs/PI_DEFENSE_PREP.md` §12–13, build only what can be shown honestly with real, already-
verified numbers. **No fabrication, and no exception for the showcase deadline** — a demo that
looks like it shows something it doesn't is worse than no demo.

### 3a. Signature visualization — updated with Variant F

Build the "State Purity vs. Action Recoverability" plane (spec in `docs/PI_DEFENSE_PREP.md` §13),
using the site's existing chart tooling. **Update the spec's original table to include Variant F**,
since it didn't exist when §13 was written:

| Variant | Purity | Action-recoverability AUROC |
|---|---|---|
| A — full state | low | 0.900 |
| B — total removed, subscore kept | low | 0.900 |
| C — subscore removed, total kept | low | 0.885 |
| D — MAP-only proxy, total recomputed | high | 0.792 |
| E — no explicit treatment features | highest | 0.791 |
| F — D + explicit treatment-history vector | high (by construction — no raw dose feature) | 0.914 |

F's position on this plane is the most interesting point to add: high purity by the same
construction logic as D/E, yet *the highest* action-recoverability of all six variants — visually
demonstrating that purity (freedom from raw treatment-derived features) and low recoverability are
not the same axis, which is a sharper visual argument than the original 5-variant plane made alone.
Write one caption sentence making this explicit, not just plotting the point.

### 3b. The honest three-act showcase page

Build `/showcase/` (or extend the homepage, whichever fits the existing site architecture better —
your call, state which and why) with:

- **Act 1:** embed or prominently link the existing live mechanism visualizer — genuinely
  interactive, already real.
- **Act 2:** the signature visualization from 3a.
- **Act 3:** a clearly-labeled "what we don't know yet" panel. State H3 as still open, and state
  Experiment 8 as corroborating-not-resolving evidence for the persistence explanation — matching
  the exact careful language already established in `FORMAL_ANALYSIS.md` §7 by the last follow-up
  round. Do not let showcase framing push this back toward sounding resolved.

**Explicitly do not build:** dual RL agents, Q-value comparisons, or any policy-level visualization.
No RL policy has been trained anywhere in this project — Experiment 8 used classifiers, not a
trained policy — and building a demo element implying otherwise would misrepresent the project's
actual state regardless of how compelling it would look.

### 3c. One-minute opening hook

Confirm the site's homepage or showcase page uses the hook already drafted in
`docs/PI_DEFENSE_PREP.md` §12.1 ("We gave a model a question and accidentally also gave it the
answer...") or an equivalent — check it's actually present somewhere prominent, not just in the
planning document.

---

## Reporting

After Part 1, stop and report the full gap list. After Part 2, report exactly what was fixed and
confirm the re-run sweep found zero remaining stale instances. After Part 3, report what was built,
with a screenshot or description of each of the three acts, and an explicit statement of what was
deliberately left out and why (the dual-agent/Q-value items) so that omission is a visible decision,
not a silent gap someone discovers later.

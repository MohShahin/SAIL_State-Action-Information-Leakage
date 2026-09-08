---
description: Phase 4 follow-up — sync the falsified-hypothesis result into the project's broader narrative, scope the next contribution honestly, and harden long-run infrastructure
---

# Phase 4 follow-up

Four scoped tasks, in priority order. Do them in order and as separate commits — do not combine
into one giant commit, matching this project's existing pattern of one focused commit per logical
change. Check `git status --short` before staging each one.

## 1. Connect Phase 4's result to the persistence/Ryohei discussion (documentation only, do first)

`docs/PHASE_PLAN_TERMINOLOGY_REVISION.md` §0 argues, from Ryohei's critique, that
`A_{t-1} → S_t → A_t` is legitimate treatment history, not leakage. Separately, Phase 4's result
(`results/experiment8_variant_f_summary.json`) shows an *explicit* treatment-history vector (F1/F2)
predicts `A_t` even better than the original state did. These are not two separate findings sitting
next to each other — the second is independent, sharper evidence for exactly what the first already
argued: the predictive power in this project was never really about SOFA's construction quirk
specifically, it's ordinary treatment persistence, and F just gave a cleaner instrument for
measuring it than the AUROC gap ever did.

Make this connection explicit in three places, not implicit:
- `docs/PHASE_PLAN_TERMINOLOGY_REVISION.md` §0 (or a short addendum right after it) — a paragraph
  stating this connection directly, citing Experiment 8's actual numbers.
- `FORMAL_ANALYSIS.md` §7 (the H3 pre-registration) — a note that Experiment 8's result is
  independent evidence bearing on the same Path 2 (persistence) vs. Path 1 (definitional) question
  H3 was designed to resolve, pointing toward persistence being large in this cohort — **without**
  claiming H3 is thereby resolved. H3's own paired-bootstrap test on the offset-decay curve remains
  the pre-registered instrument; Experiment 8 is corroborating, not substituting.
- `src/evidence.html`'s Experiment 8 section — one sentence making the same link for a site visitor
  who hasn't read the phase plan.

**Guardrail:** Experiment 8 is not a formal proof of anything and does not resolve H3 by itself —
state it as convergent empirical evidence, precisely, not as a new theorem or as closing H3 early.

## 2. Document the F′ deprioritization (documentation only)

In `docs/PHASE4_VARIANT_F_SPEC.md` §3.3 / §7, add a short note: given F already exceeds `A_full`'s
action-recoverability without the raw current-dose feature, running F′ (which adds *more* direct
treatment signal on top) is not expected to be informative and is deprioritized. State this as a
reasoned decision with the reasoning shown — not a silent deletion of the item from the spec.

## 3. Scope (do not implement) the duration/recency finding as its own contribution

**This is a scoping task — produce a short design note, not code or a new experiment.**

Assess honestly first: is there a clean, provable mathematical statement here, in the style of
Theorems 1–2 or Proposition 3, or is this fundamentally an empirical finding that should be
reported as such without forcing a proof where none is warranted? **Do not manufacture false
rigor.** If the honest answer is "this is empirical, not provable in that sense," say so plainly —
the same discipline that correctly upgraded Corollary 1.1 from Measured to Proven only because the
math actually supported it, not by default, applies here in the opposite direction if that's what's
true.

Write a short new section in `docs/PHASE_PLAN_TERMINOLOGY_REVISION.md` (a new phase, or an addendum
to Phase 4) sketching:
- What the claim would actually be, stated precisely.
- What would need to be true for it to generalize beyond this one cohort/dataset/algorithm choice.
- What empirical validation would look like if pursued as its own contribution (e.g., does this
  hold on a different action space, a different set of history features, a different cohort?).
- An honest recommendation: is this a section within the *current* paper, or does it belong in a
  follow-up paper of its own, given this project's stated goal of producing multiple papers?

## 4. Harden long-run infrastructure against sleep interruption

Four of six Phase 4 execution attempts were disrupted by the machine sleeping mid-run for 9–18 hour
stretches, silently killing the background kernel process — fixed manually via `powercfg` that
time, not fixed structurally. Add an automatic check at the start of any long-running notebook
execution (either in `scripts/check_setup.sh` or as a preamble in the crash-safe runner script
pattern already used for Phases 3–5) that:

1. Checks the current sleep/hibernate timeout settings via `powercfg /query`.
2. If any AC or DC standby/hibernate timeout is nonzero, warns loudly in the run's own log output
   and sets them to 0 for the run's duration.
3. Restores the **actual prior values** — captured before changing them, not a hardcoded "reasonable
   default" — once the run completes or fails, including on an exception path (this must not leave
   the machine with sleep permanently disabled if the run crashes).

**Guardrail:** do not silently change system power settings — the check, the values found, and the
change made must all appear in the run's log output, auditable the same way every other step in
this project is.

## Reporting

For each of the four tasks, report what was written or changed and exactly where, before moving to
the next task. If task 3's honest assessment concludes "this doesn't belong in the current paper,"
report that plainly rather than treating it as an unsatisfying outcome to soften.

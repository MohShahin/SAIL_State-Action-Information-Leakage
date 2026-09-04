---
description: Execute the Phase 4 Variant F spec (docs/PHASE4_VARIANT_F_SPEC.md) end to end
---

# Run Phase 4 — Variant F

Read `docs/PHASE4_VARIANT_F_SPEC.md` in full before starting. This command executes it; it does not
redesign it. If executing reveals the spec is wrong or ambiguous somewhere, stop and report rather
than silently improvising a fix — same standard as every other experiment in this project.

**Do not start this without confirming a clear, uninterrupted block of time is actually available
right now.** A half-finished extraction-and-training run is a worse stopping point than not
starting. If time is uncertain, say so and stop here instead of beginning §1 below.

## 1. Re-establish the live kernel state

Re-run notebook cells 0–14 (setup through SOFA computation) exactly as Phases 3 and 5 did — same
~15–20 minute cost, unavoidable since `sofa_4h` / `vaso_dose_clean` only exist in a live kernel.
Launch detached in the background with the same monitoring pattern used for Phases 3 and 5
(`nohup ... &`, `nbformat.write` after each cell, tail the log). Report each cell's key output
number against its already-known value (11,354 cohort, etc.) as it completes, same as before — a
match at every step is what makes the eventual new numbers trustworthy.

## 2. Factor out `merge_intervals`, and verify the refactor is a true no-op

Extract the interval-merging logic already inlined in `run_experiment3` into a standalone
`merge_intervals(pairs)` helper, per spec §6 step 2. **Before moving on:** re-run Experiment 3 using
the refactored helper and confirm its published numbers (mean/median window overlap, %>50%
overlap) are byte-identical to the currently-published figures. A pure refactor should be a
no-op — confirm it, don't assume it. If any number moves even slightly, stop and report before
proceeding; do not treat a refactor-induced change as acceptable collateral.

## 3. Implement F1 and F2, sanity-checked before cohort-wide

Implement `hours_on_vasopressor` (F1) and `hours_since_dose_tier_change` (F2) exactly per spec
§3.2. Before running cohort-wide, hand-check both features on 2–3 individual `stay_id`s — pick at
least one patient with a single continuous vasopressor course and one with multiple
starts/stops/tier changes, and manually verify the computed values against the raw dose events for
that patient. Report the hand-check before proceeding to the full cohort run.

## 4. Build Variant F

Extend `build_state_variants` (or add a sibling function, per spec §4) to produce `F`:
Variant D's severity term, unchanged, plus F1 and F2 appended as new columns. Confirm the resulting
feature matrix's shape and that F1/F2 contain no unexpected nulls (per spec §3.2 step 4, "stable
since admission" is a defined zero-equivalent, not a missing value — confirm it's being encoded
that way, not silently dropped by a `dropna`).

## 5. Run both evaluation axes

Extend the existing `variants` dict (Experiment 2's action-recoverability pipeline) and the
existing `mortality_variants` dict (Experiment 6's pipeline) with `F`, and run both — do not write
a new parallel pipeline. Use the same `PROBES` / `cv_predict` / `bootstrap_ci_metric_clustered` /
`GroupKFold` machinery already verified for A–E.

## 6. Report the primary comparison table — as it actually comes out

Fill in the table from spec §5:

| Variant | Action-recoverability AUROC | Mortality AUROC |
|---|---|---|
| A_full | 0.900 (known) | 0.793 (known) |
| D_treatment_decomposed | 0.792 (known) | 0.784 (known) |
| F (D + F1 + F2) | ? | ? |

Evaluate against the **pre-registered** success criterion from spec §5 exactly as written: F is a
useful disentanglement if its mortality AUROC moves meaningfully toward A's while its
action-recoverability stays close to D's. If F's action-recoverability instead rises toward A's,
that is evidence *against* the hypothesis and must be reported as such — do not reinterpret the
criterion after seeing the result.

## 7. F′ only after F is fully reported

Do not run the secondary variant F′ (adds raw current dose tier) until F's result above is
reported in full. If F's own result already answers the interesting question either way, treat
running F′ as optional rather than assumed.

## Write-up and commit

Follow the exact pattern used for Phases 3 and 5: a results JSON under `results/` (aggregate-only,
matching `DATA_ACCESS.md`), a `FORMAL_ANALYSIS.md` addition if the result rises to a
proposition-level claim, an `evidence.html` section, and a status update to
`docs/PHASE_PLAN_TERMINOLOGY_REVISION.md` marking Phase 4 done with the actual date. Check
`git status --short` before staging — confirm only the intended files changed. Use `git commit -F`
with a message file or heredoc for anything multi-line, to avoid the shell-quoting failures that
have bitten multi-line commit messages earlier in this project. Check for remote divergence
(`git fetch && git log HEAD..origin/main --oneline`) before pushing, same as every prior push.

## If the result doesn't confirm the hypothesis

Report it exactly as such — a null result here (F performs like D on both axes, or worse) is
itself informative, matching how this project has already handled H3 and Phase 3's small-gap
finding. Do not delay reporting to look for a more favorable framing.

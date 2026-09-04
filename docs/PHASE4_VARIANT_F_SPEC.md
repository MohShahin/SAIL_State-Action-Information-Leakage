# Phase 4 Specification: Variant F — Disentangled Severity + Explicit Treatment Vector

**Status: spec only, not implemented.** Per direct instruction, this document is the complete
design — feature definitions, computation algorithms, data-availability check, and evaluation plan
— ready for a future session to execute directly, without design decisions left open. No extraction
or training was run to produce this; every claim below is either a definition, a re-derivation from
already-extracted data, or an explicitly flagged design choice with its rationale stated.

**Dependency status:** Phase 3 (mortality-prediction infrastructure) is done — `results/experiment6_*`
and the reusable pattern in notebook cell 24. This spec is unblocked.

---

## 1. Why this exists (and the honest, revised motivation)

The clinical reviewer's point 4: reframe the fix around an explicit prior-treatment vector
*alongside* an untouched severity term, rather than stripping treatment out of a single composite
score — the same resolution the Robins g-methods literature uses for time-varying confounding
(keep the confounder and the treatment history as separate, explicit terms, not collapsed).

**Revised framing after Phase 3's actual result (2026-09-03):** the original motivation ("does F
recover the mortality-predictive validity variant D loses") assumed a large loss. The measured gap
was 0.011 AUROC — small. The honest question going in is now: **does explicit disentanglement
recover a small-but-real mortality-validity gap while still reducing action-recoverability**,
not "does it fix a large clinical problem." Report whichever way this comes out; a null result here
(F performs identically to D on both axes) is itself informative — it would suggest the individual-
patient failure mode documented in Phase 2 doesn't translate into anything a model can exploit
either way, on either task.

---

## 2. Data availability check (done — no new extraction needed)

Everything Variant F needs is already in `vaso_dose_clean` (built in notebook cell 9, no new
BigQuery query): `stay_id, itemid, drug, starttime, endtime, rate, rateuom, amount,
start_hours_from_admit, end_hours_from_admit`, filtered to the four dose-scored drugs (dopamine,
dobutamine, epinephrine, norepinephrine — the same set `sofa_cardio_decomposed` scores on).

---

## 3. Feature design

### 3.1 Component 1 — Severity term (physiology-based, deliberately untouched)

**Use exactly Variant D's severity term: no changes.** Recompute `sofa_total` from the MAP-only
cardiovascular proxy (`score_map = 1 if MAP < 70 else 0`), all five other subscores unchanged —
identical to the existing `build_state_variants`'s `D_treatment_decomposed` construction. This is a
deliberate choice, not an oversight: isolating the test to *one* change (adding explicit treatment
features) keeps the comparison to D clean. A continuous-MAP severity term (not thresholded at 70) is
a reasonable secondary sensitivity variant but is **not** part of the primary spec — flagged in §5.

### 3.2 Component 2 — Explicit treatment-vector features (new, appended, not fused into severity)

The plan's original phrasing ("current dose, duration on current dose, time since last dose
change") names three things that partially overlap once precisely defined. This spec resolves that
into **two** genuinely distinct, precisely-computable features, covering the same clinical intent
without redundancy — plus a third, explicitly *excluded from the primary spec* with its rationale
stated (§3.3), because including it risks defeating the experiment's own purpose.

**F1 — `hours_on_vasopressor` (treatment-course duration).** Consecutive hours of continuous
exposure to *any* dose-scored vasopressor (dopamine, dobutamine, epi, norepi; amount > 0), ending
at the decision boundary, capped at 0 if not currently on any.

*Computation:*
1. Per stay, take all `vaso_dose_clean` rows restricted to `dose_scored_drugs`.
2. Merge overlapping/adjacent intervals into non-overlapping runs — reuse the exact
   merge-overlapping-intervals logic already built and verified for the Experiment 3 fix (notebook,
   the corrected `run_experiment3`'s inline merge: sort by start, extend the last interval if the
   next one starts at or before its end, else start a new one). Factor it into a standalone
   `merge_intervals(pairs)` helper — it is currently inlined in `run_experiment3` only.
3. For decision bin `t`, let `τ = (t+1) · DECISION_INTERVAL_HOURS` (the same window-end convention
   the state features and action labels both already use). Find the merged interval `[a, b)`, if
   any, with `a ≤ τ < b`. If found, `hours_on_vasopressor = τ − a`. If none, `0`.

**F2 — `hours_since_dose_tier_change` (treatment-regimen recency/stability).** Hours since the
SOFA-relevant dose *tier* (not raw rate — see rationale below) last changed, ending at the decision
boundary.

*Rationale for using the tier, not the raw rate:* infusion rates are titrated continuously (nurses
adjust in small increments), so "time since the exact rate last changed" would reset almost every
bin and carry almost no signal. Tying "change" to the same thresholds `sofa_cardio_decomposed`
already scores on (0 / (0,5] / (5,15] / >15 for dopamine-equivalent dosing, mirrored for epi/norepi
at 0.1) ties the feature to clinically-meaningful regimen changes, not micro-titration noise.

*Computation:*
1. Per stay, at every raw dose-event timestamp (start and end of every `vaso_dose_clean` row,
   restricted to dose-scored drugs), compute the resulting `score_dose` tier using
   `sofa_cardio_decomposed`'s existing dose-only branch logic (reuse directly — same four
   thresholds, same max-across-drugs rule if more than one drug is active).
2. Build a stepwise tier timeline per stay (tier value between consecutive event timestamps).
3. Identify tier-*change* timestamps (where the tier differs from the immediately preceding value;
   0→0 is not a change, 0→2 is).
4. For decision bin `t`'s boundary `τ`, find the most recent tier-change timestamp `≤ τ`.
   `hours_since_dose_tier_change = τ − that_timestamp`. If no prior change exists (tier has been 0
   since admission through `τ`), set to `τ − intime` (elapsed stay time) — i.e., "stable since
   admission," not a missing value; document this convention explicitly wherever the feature is
   used, since it changes meaning at the cohort's early bins.

### 3.3 Explicitly excluded from the primary spec: raw current dose value

A third candidate — the instantaneous current infusion rate (or dose tier) as its own feature — is
**deliberately not included** in primary Variant F. Rationale: this is close to re-exposing what
Variant D removed (`score_dose`'s direct treatment signal), which would risk trivially recovering
action-recoverability toward Variant A/B's level and defeating the point of the comparison (F is
supposed to test whether *history/duration* features recover mortality validity without similarly
recovering action-recoverability — current dose value is exactly the kind of feature most likely to
recover both, uninformatively). If time allows, run it as a **secondary variant F′** (D's severity +
F1 + F2 + current dose tier) specifically to test this hypothesis empirically rather than assert it
— but report F (primary) first and separately from F′.

---

## 4. Variant F, assembled

`FEATURE_COLS_F = [all Variant D features] + ["hours_on_vasopressor", "hours_since_dose_tier_change"]`

Built the same way `build_state_variants` builds D today (recompute `sofa_total` from the MAP-only
proxy, all else unchanged), then `np.column_stack` the two new columns onto the resulting matrix.
Missing values (patients who are never on a vasopressor in view) are legitimate zeros for F1, and
"stable since admission" for F2 per §3.2 step 4 — not missing-data imputation candidates.

---

## 5. Evaluation plan (no new methodology — reuse existing infrastructure exactly)

Two axes, both already-built pipelines requiring only the new feature matrix as input:

1. **Action-recoverability** — same protocol as Experiment 2 (notebook cell 21): `PROBES`,
   `cv_predict`, `bootstrap_ci_metric_clustered`, `GroupKFold` on `y_action`/`groups` from
   `state_4h`. Add `F` (and optionally `F_prime`) to the existing `variants` dict; run alongside
   A–E, not as a separate experiment, so the comparison table extends naturally.
2. **Mortality-predictive validity** — same protocol as Experiment 6 (notebook cells 23–24):
   `build_mortality_table` at the fixed 24h decision point (bin 5), same self-contained
   `PROBES`/`cv_predict`/`bootstrap_ci_metric_clustered` definitions (cell 24 already has these
   without depending on cell 21 having run).

**Primary comparison (fill in when run):**

| Variant | Action-recoverability AUROC | Mortality AUROC |
|---|---|---|
| A_full | 0.900 (known) | 0.793 (known) |
| D_treatment_decomposed | 0.792 (known) | 0.784 (known) |
| **F (D + F1 + F2)** | ? | ? |
| F′ (D + F1 + F2 + current dose, secondary) | ? | ? |

**Success criterion, stated in advance (do not adjust after seeing the result):** F is a genuinely
useful disentanglement if its mortality AUROC moves meaningfully toward A's (recovering some of
D's small 0.011 gap) while its action-recoverability AUROC stays close to D's (0.792), not close to
A's (0.900). If F's action-recoverability also rises toward A, that is evidence *against* the
disentanglement hypothesis (F1/F2 are informative enough to reconstruct near-A predictability even
without the raw dose), and should be reported as such, not reframed.

---

## 6. Execution checklist for the next session

1. Re-run cells 0–14 (setup through SOFA computation) — same ~15–20 min cost as Phases 3 and 5,
   unavoidable since `sofa_4h`/`vaso_dose_clean` only exist in a live kernel.
2. Add a `merge_intervals(pairs)` helper (factor out of `run_experiment3`, don't duplicate).
3. Implement F1/F2 per §3.2 exactly as specified; sanity-check on 2–3 individual stay_ids by hand
   before running cohort-wide (same diligence pattern as every prior experiment this project has
   run).
4. Extend `build_state_variants` (or add a sibling function) to produce `F` per §4.
5. Run both evaluation axes per §5, extending the existing `variants`/`mortality_variants` dicts
   rather than writing a new parallel pipeline.
6. Report the primary comparison table (§5) as the actual result, including if it doesn't confirm
   the disentanglement hypothesis.
7. Only after F is reported: decide whether F′ (secondary, §3.3) is worth running.

**Do not start this mid-session without a clear block of time ahead** — same reasoning as every
other experiment this session: a half-finished run is a worse stopping point than not having
started.

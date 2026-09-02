# SAIL Phase Plan: Terminology Resolution and Clinical Strengthening

**Purpose:** A prioritized, dependency-aware implementation plan for the feedback from the August 28
meeting (Ryohei's terminology critique, Dimitris's task-specificity point) and a second reviewer's
7 clinical/methodological suggestions. Written for direct handoff to a VS Code Claude Code session.

**Status labels used throughout:** `[VERIFIED]` = checked directly against this repo's actual code
in this session. `[ASSESSED]` = my own judgment on whether a suggestion is correct/feasible, stated
plainly, not just relayed. `[NEEDS VERIFICATION]` = plausible but not yet checked — a task, not a fact.

---

## 0. The central issue, resolved first because everything else depends on it

**Ryohei's claim, restated precisely:** `A_{t-1} → S_t → A_t` — prior treatment shaping the current
state, which then informs the next decision — is ordinary sequential decision-making, not leakage.
True leakage would be `A_t → S_t → Â_t`: the state containing information about the *same* action
it's being used to predict, or information not yet available at decision time.

**My assessment: Ryohei is substantially correct, and this is not a minor wording issue.**
`[ASSESSED]` Here's the reasoning, checked against what SAIL's own documents already say versus
what SAIL's public framing implies:

- `FORMAL_ANALYSIS.md`'s Proposition 2 already cites Hernán & Robins on *conditioning on a variable
  affected by treatment* — this is a **post-treatment-bias / bad-control** concept from causal
  inference, not a **target/temporal leakage** concept from machine learning. These are genuinely
  different pathologies with different fixes. The math in Theorems 1–2 is unaffected by this
  distinction — it's real regardless of what we call it — but the project's *name*
  ("State–Action **Information Leakage**") and its public-facing language ("contamination,"
  "corrupted," "leaked") all evoke the ML sense, not the causal-inference sense.
- This matters concretely for Experiment 2's own interpretation: Variant A's state includes
  `sofa_cardio`, which is a function of `D_t` — and `D_t` (per `FORMAL_ANALYSIS.md`'s own notation)
  is the dose *active at t*, i.e., a consequence of `A_{t-1}`, not of `A_t` (the target being
  predicted, defined as the action *following* `t`). So Mechanism 1, as currently measured, is
  squarely in Ryohei's "not necessarily leakage" category by SAIL's own stated definitions — it's
  `A_{t-1}`-derived information in `S_t`, used to predict `A_t`. That's legitimate treatment
  history, not leakage, under the strict ML definition.
- **What genuine leakage would require:** the state window `[t-w, t)` actually extending into or
  past the boundary where `A_t` itself is decided/recorded — i.e., exactly the concern the "Off by
  a Beat" paper (already cited in this project, see prior session) raises about index alignment.
  **This has been flagged as an unverified action item once already** (in `PI_DEFENSE_PREP.md` §6)
  and is now the single most important thing to check, because the entire terminology question
  hinges on the answer.

**Resolution — a two-tier vocabulary, not an abandonment of the existing math:**

| Old term | What it actually is | New term |
|---|---|---|
| "Mechanism 1" / "leakage" (SOFA definitional) | `A_{t-1}`-derived information making a severity score non-identifiable from physiology | **Treatment-confounded severity construction** (or: "definitional treatment-dependence") |
| "Mechanism 2" / "window contamination" | Prior treatment overlapping the state's lookback window | **Treatment overlap** (Ryohei's own term — adopt it directly) |
| "Variant E — physiology-only" | State with no dose-derived features, but MAP itself is still causally downstream of treatment in a treated patient | **"No explicit treatment features"** (reviewer's suggested rename — adopt directly; "physiology-only" overclaims independence from treatment that doesn't hold) |
| (new) "True leakage" | State containing information about the *same* decision epoch's action, or anything not available at decision time | Reserved exclusively for this — and **only claimed once the alignment check below is actually done** |

This is not a retreat — it is, if anything, a **stronger and more defensible** position: the project
stops claiming the ML-flavored "leakage" charge (which Ryohei is right to push back on) and instead
makes the narrower, provable, causal-inference-flavored claim (treatment-confounded construction),
which is exactly what Theorems 1–2 actually establish. The clinical reviewer's point 1 — that the
real novelty is "offline RL pipelines use this therapy-dependent score as pre-decision state and
don't account for it" — is the correct novelty statement *precisely because* it survives this
terminology correction, while a bare "leakage" claim does not.

**Dimitris's point (leakage is task-specific) is the same insight from a different angle** and is
directly operationalized by clinical-reviewer suggestion 6 (§4 below) — a feature contaminated for
predicting the *next action* may be exactly the right feature for predicting *mortality*, because
mortality prediction doesn't have the same "was this information available before the decision"
constraint that action-prediction does.

---

## 1. Phase 0 — Terminology resolution (CRUCIAL, BLOCKING, do first)

**Why blocking:** every other phase touches content that uses the current vocabulary. Renaming
after building Phase 3/4/5 content would mean redoing that content's language a second time.

**Dependencies:** none — this can start immediately.

**Tasks:**

1. **`[NEEDS VERIFICATION]` — Resolve the actual state/action alignment**, the single fact this
   whole resolution depends on. Grep the notebook's Experiment 2 label-construction cell
   (`X_act`/`y_action`, referenced in cell 9 but not yet inspected in full) and confirm: is `A_t`
   (the prediction target) constructed strictly from treatment events *after* the state's
   observation window closes, with zero overlap? If yes — SAIL currently has zero genuine
   ML-sense leakage, and the whole project is cleanly "treatment-confounded construction," full
   stop, nothing further to fix in the pipeline itself. If no — there is a real, undisclosed
   leakage bug of exactly the kind Off by a Beat describes, and it needs to be fixed and disclosed,
   not reframed away. **This single check determines whether Phase 0 is a renaming exercise or a
   renaming-plus-bugfix exercise.** Do this before anything else in this plan.
2. Rename across the site and documents per the table in §0: `mechanisms.html`, `visualizer.html`
   (the DAG labels and the "what this means" captions), `proof.html`, `about.html`, `papers.html`,
   `index.html`, `FORMAL_ANALYSIS.md`, `README.md`, `status.html`/`evidence.html`.
3. Add a new, explicit **"Terminology" section** (either its own page or a prominent section on
   `mechanisms.html`) laying out the treatment-overlap / treatment-derived-state-information /
   true-leakage distinction from Ryohei's memo directly — including his own DAG framing
   (`A_{t-1} → S_t → A_t` normal; `A_t → S_t → Â_t` true leakage) rendered as an actual diagram,
   not just prose.
4. Update the visualizer's captions specifically — Ryohei's memo calls this out by name: it
   "currently labels treatment-derived information as leakage" and should distinguish past/current
   treatment info from target/future-action info explicitly in the UI text, not just in
   documentation a visitor might not read.
5. Add Dimitris's task-specificity point as an explicit statement near the Evidence/Novelty
   framing: the same feature's validity depends on what it's being used to predict — directly
   setting up Phase 3 (§4).

---

## 2. Phase 1 — Reframe the novelty statement (CRUCIAL, low cost, depends on Phase 0)

**Dependencies:** Phase 0's terminology must land first, since the novelty statement needs to be
written in the corrected vocabulary from the start, not written once and then edited.

**Task:** Update `papers.html`, `about.html`, and `PI_DEFENSE_PREP.md`'s novelty section (§2.3) to
state the novelty exactly as the clinical reviewer framed it: *the treatment-dependence of the SOFA
cardiovascular subscore is documented in the clinical literature; the contribution is that offline
sepsis-RL pipelines treat this therapy-dependent score as a valid pre-decision state feature without
accounting for that dependence — and Theorem 2's exact reconstruction result is the least
clinician-known and most novel single finding.* This should replace, not merely supplement, the
current framing wherever it currently leans on the word "leakage" to carry the novelty claim.

---

## 3. Phase 2 — Document the Variant D/E clinical-validity tradeoff (CRUCIAL, no new data needed)

**Dependencies:** none beyond Phase 0 (needs the corrected variant names to write about).

**The specific mechanism, verified against SAIL's own scoring logic, not just asserted:**
`sofa_cardio_decomposed`'s `score_map` branch scores `MAP < 70` as 1, else 0 — a two-level
signal. For a treated patient whose vasopressors have successfully restored MAP above 70, Variant
D's MAP-only proxy scores them as **low severity (0)**, when the fact that they *needed*
vasopressors to reach that MAP is itself the clinically meaningful severity signal the original
score was designed to capture. This is exactly the reviewer's point, and it's a real, checkable
property of the existing code, not a hypothetical.

**Tasks:**
1. Add a **Limitations/Discussion section** — natural homes are `evidence.html` (empirical framing)
   and a corresponding paragraph in `FORMAL_ANALYSIS.md` — stating this tradeoff explicitly: variant
   D/E may be a *worse* clinical severity measure specifically because it cannot distinguish
   "healthy, untreated" from "successfully treated, still critically ill."
2. **A small, concrete illustration, buildable with zero new data:** construct one or two
   synthetic patient examples (or pull a couple of real qualifying cases from the already-extracted
   cohort, aggregate-only) showing this failure mode numerically — e.g., "Patient on norepinephrine
   0.15 mcg/kg/min with MAP 74: Variant A scores cardiovascular SOFA = 4 (correctly severe);
   Variant D scores it = 0 (incorrectly low)." This is a strong, concrete visual for both the paper
   and the site.
3. This section should explicitly avoid over-correcting into "therefore sanitization is wrong" —
   the honest framing is a genuine tradeoff (predictive purity vs. clinical validity), which is
   precisely what motivates Phase 4's disentangled-state proposal.

---

## 4. Phase 3 — Add a mortality-prediction task per state variant (HIGH VALUE, feasibility HIGH)

**Why this matters:** this is the single highest-leverage new experiment in this entire feedback
set. It directly operationalizes Dimitris's task-specificity point and the clinical reviewer's
point 6, and it turns Phase 2's qualitative concern (D/E might be clinically worse) into a
quantitative, publishable comparison: *action-recoverability vs. mortality-predictive-validity,
per variant.*

**Dependencies:** none blocking — but needs one cheap verification step first.

**Tasks:**
1. **`[NEEDS VERIFICATION]`** — check whether in-hospital mortality (`hospital_expire_flag` or
   equivalent) is already present in the extracted cohort table. MIMIC-IV cohort-definition queries
   typically pull this alongside admission/demographic data as a matter of course, but this needs
   confirming against `queries/01_cohort.sql` directly rather than assumed. If present: this
   experiment needs **zero new data extraction** — it's a new modeling task on data already in
   hand. If absent: a small, well-scoped addition to the cohort query, not a new pipeline.
2. For each of variants A–E (and F once Phase 4 exists), train a simple classifier (logistic
   regression or gradient boosting, matching the existing methodology's own probe choices in
   Experiment 2) predicting in-hospital mortality from the state at a fixed decision point (24h, as
   the reviewer suggests — matches SOFA's own original validation convention, which strengthens
   the comparison's clinical legitimacy).
3. Report both axes side by side: action-recoverability AUROC (already have this) and
   mortality-AUROC (new) per variant. **The single most interesting possible finding, stated as a
   hypothesis, not a result:** if variant D/E's mortality-AUROC drops meaningfully relative to
   variant A's, that is direct, quantitative evidence for Phase 2's qualitative concern — a
   genuinely strong, clinically legible result either way (confirms or refutes the concern with
   real numbers, publishable regardless of which way it comes out).

---

## 5. Phase 4 — Disentangled state design ("Variant F"): explicit severity + explicit treatment vector

**Why this is the strongest single new contribution in this feedback set:** the clinical reviewer's
point 4 — reframe the fix around an explicit prior-treatment vector *alongside* an untouched
severity term, rather than trying to strip treatment out of a single composite score — is exactly
the resolution the Robins g-methods literature already uses (keep time-varying confounders and
treatment history as separate, explicit terms, rather than collapsing them). This gives SAIL a
second, genuinely novel technical contribution beyond the two existing theorems.

**Dependencies:** Phase 3 must exist first — evaluating whether Variant F actually solves Phase 2's
problem requires the mortality-prediction infrastructure to check against.

**Tasks:**
1. Design Variant F: physiology-based severity term (MAP, or a validated MAP-based shock index,
   kept as-is, no attempt to "fix" it) **plus** a separate, explicit treatment-history feature block
   (current dose, duration on current dose, time since last dose change) that the model can use
   without it being *fused into* the severity number itself.
2. Evaluate on both axes from Phase 3: does F recover the mortality-predictive validity variant D
   loses, while still reducing action-recoverability relative to variant A? This is the actual test
   of whether "disentangle, don't delete" is a better methodology than the current A–E ladder alone.
3. If successful, this becomes the paper's proposed *solution*, not just its diagnosis — a
   substantially stronger contribution than critique alone.

---

## 6. Phase 5 — Respiratory SOFA subscore: a second mechanism instance

**Why this matters beyond one more experiment:** this is the first real test of whether SAIL's
general leakage/treatment-dependence framework (the mechanism-agnostic definition already drafted
in `PI_DEFENSE_PREP.md` §4) actually generalizes past cardiovascular SOFA, or whether it was a
one-off property of that specific subscore. A second confirmed instance is what separates "an audit
of one score" from "a methodology."

**A finding worth stating plainly, not softening:** SAIL's own `sofa_resp` implementation
(`sofa_cardio_decomposed`'s sibling function in the notebook) is currently **PF-ratio-only** and
does not implement the official Vincent et al. 1996 respiratory criterion's ventilatory-support
condition (scores 3–4 officially require the patient to be on respiratory support, not just have a
low PF ratio). This is simultaneously the clinical reviewer's suggested extension *and* a real,
independent implementation-accuracy gap in the existing code — both should be addressed together,
not separately.

**Dependencies:** none blocking; can run in parallel with other phases, though best done after
Phase 0's terminology lands so the new mechanism is named correctly from the start.

**Tasks:**
1. **`[NEEDS VERIFICATION]`** — check whether mechanical-ventilation status is already present in
   the extracted feature set (likely yes, given `respiratory support` is a standard MIMIC-IV
   chartevents/procedureevents field commonly pulled for exactly this scoring purpose — but confirm
   against `queries/02_vitals_labs_fio2.sql` rather than assume).
2. Correct `sofa_resp` to implement the official rule with the ventilatory-support conditional.
3. Prove the analogous non-identifiability argument: once a patient is on ventilatory support with
   PF ratio in the qualifying range, does the score become insensitive to further PF-ratio changes
   the way cardiovascular SOFA becomes insensitive to MAP? (Structurally likely yes, given the
   nested-threshold pattern, but state as a proposition to prove, not assumed true by analogy.)
4. Measure prevalence empirically on the existing cohort — reuses the existing extraction, no new
   MIMIC query needed if step 1 confirms ventilation status is already present.

---

## 7. Phase 6 — Infrastructure: repo migration and compute optimization

**Two independent, non-content items, schedule opportunistically:**

1. **Repo migration to MIT Clinical Data Org** (mentioned as a meeting next step). Genuinely cheap
   now, specifically *because* of the recent Eleventy/`PATH_PREFIX` refactor — the entire site's
   subpath is a single constant in `.eleventy.js`. Once the new org/repo name is confirmed, this is
   a one-line change plus a rebuild-and-verify pass, not the multi-file hunt it would have been
   before that refactor. **Blocked only on knowing the actual destination name** — not a technical
   blocker, a coordination one.
2. **Pipeline compute optimization** (Dimitris's suggestion: profile bottlenecks, move from CSV to
   a columnar format like Parquet/PyArrow for parallel processing). This directly unblocks the
   YELLOW-status experiments already identified in `PI_DEFENSE_PREP.md` (Experiment C, D, G) that
   are currently compute-gated. Concretely: profile the notebook's slowest cells first (likely the
   per-timestep `build_dose_matrix` groupby loop, based on its current row-by-row construction),
   before assuming the CSV format itself is the bottleneck — profile before optimizing, not the
   reverse.

---

## 8. Phase 7 — Vasopressor weaning (FUTURE / GREEN, narrative for the next paper, not this one)

**Assessment:** this is a genuinely compelling clinical framing and a real methodological gap
(current sepsis-RL literature struggles to learn good down-titration policies, plausibly for
reasons connected to — but not identical to — this project's findings, now correctly reframed per
Phase 0 as treatment-derived state information rather than leakage per se). **This should not be
built into the current paper's scope.** It's a distinct research question (weaning as its own
action-space/decision-boundary problem) that deserves its own experimental design, not a bolt-on to
the current leakage-audit paper.

**Task:** add to `ROADMAP.md` as an explicitly-scoped future-paper direction, with a one-paragraph
research question capturing the reviewer's framing, rather than attempting any implementation now.

---

## 9. Priority summary and dependency graph

```
Phase 0 (terminology) ──┬──► Phase 1 (novelty reframe)
     [BLOCKING]          ├──► Phase 2 (D/E limitations writeup)
                         ├──► Phase 3 (mortality task) ──► Phase 4 (disentangled Variant F)
                         └──► Phase 5 (respiratory SOFA)

Phase 6 (infra) — independent, schedule opportunistically, partially unblocks Phase 3/5's
                  eventual larger-scale runs

Phase 7 (weaning) — independent, future-paper scope, no dependency on anything above
```

**If only one thing happens before other work resumes:** Phase 0, task 1 — the state/action
alignment verification. It is the cheapest possible check (a grep, not an experiment) and it
determines whether the rest of this plan is a pure terminology correction or also includes a real
bugfix. Everything else in Phase 0 can proceed either way, but this specific fact should be known
before any public-facing renaming commits to a specific story.

---

## 10. Starter prompt for the VS Code Claude Code session

```
Work through docs/PHASE_PLAN_TERMINOLOGY_REVISION.md in order, starting with Phase 0, task 1 only,
and stop and report back before proceeding to any renaming or content changes.

Task: grep the notebook (notebook/Sepsis_RL_SOFA_Leakage_Experiments.ipynb) for the cell that
constructs X_act / y_action for Experiment 2 (referenced but not fully shown in vaso_bins_df's
construction in an earlier cell). Confirm precisely: is the action label A_t built exclusively from
treatment events occurring strictly after the state window [t-w, t) closes, with zero overlap into
the state's own observation window? Quote the exact code and explain your reasoning plainly -- this
single fact determines whether Phase 0 is a pure renaming exercise or also requires a disclosed
bugfix, so don't guess or approximate here.

Report back with the exact answer before touching any site content, per the plan's explicit
"do this before anything else" instruction.
```

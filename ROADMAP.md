# Project Roadmap — State–Action Leakage in Sepsis RL

This is the working plan from **interactive demo → completed experiments → submission-ready
manuscript → thesis-scale project**. Each phase lists what's done, what's open, exactly where in
the manuscript/notebook it lives, and (for technical phases) a prompt written for **Claude Code in
VS Code**, where the actual MIMIC-IV/BigQuery work happens — this repo and this file are the
coordination layer, not the execution environment.

**How to use this file:** check items off as they land. Each phase is small enough to be its own
GitHub Issue or Project card if you want a board view — the checklist below is written so you can
paste each phase in as one Issue with the checkboxes intact.

---

## Phase 0 — Foundation ✅ done

- [x] Cohort extracted (11,354 stays), vitals/labs/FiO2 (7,497,914 rows), vasopressor doses (5,428,937 rows)
- [x] Experiments 1–3 executed and producing results consistent with the manuscript
- [x] Manuscript drafted end-to-end with every open question flagged inline (not silently assumed)
- [x] Interactive walkthrough (`index.html`) built and connected to the repo
- [x] Repo scaffolded: `README.md`, `LICENSE`, `CITATION.cff`, `paper/`, `notebook/`

---

## Phase 1 — Close the methodological gaps (do this first)

These are documentation/specification placeholders, not new experiments — they're what a reviewer
or your committee will ask about first, and several of them (3.4–3.6) affect how Experiment 2's
44.6% positive rate and AUROC numbers should even be interpreted. Fast to close, high leverage.

## ⚠️ Known issue — original cohort data-characteristics numbers appear inflated (found 2026-08-15)

While re-running the extraction pipeline from a fresh BigQuery environment, the cohort count
matched the manuscript exactly (11,354 stays), but the vitals/labs/FiO2 and vasopressor-dose
row counts did not:

| Table | Manuscript figure | Fresh extraction | Ratio |
|---|---|---|---|
| vitals + labs + FiO2 (combined) | 7,497,914 | ~4,850,246 | ~65% |
| vasopressor dose events (cohort-joined) | 5,428,937 | 351,720 | ~6.5% |

Diagnosis (see conversation log for full trace): the manuscript's vasopressor-dose figure would
require **49.6% of every infusion event in the entire MIMIC-IV ICU module** to be one of six
vasopressor/inotrope drugs — clinically implausible (vasopressors are a small minority of all
charted infusions: fluids, nutrition, sedation, antibiotics, blood products, etc. dominate). The
fresh extraction's proportion (7.0% of all inputevents) is far more plausible.

**Working theory:** the original numbers were generated against an earlier, uncorrected version of
the `sepsis_cohort` scratch table that likely had duplicate rows per `stay_id`, producing a join
fanout that uniformly inflated every downstream `JOIN ... USING(stay_id)` extraction. The current
`sepsis_cohort` table is verified clean (row count exactly equals distinct `stay_id` count,
11,354). `icustays` (unfiltered) matches PhysioNet's documented total (94,458) exactly, ruling out
a partial-dataset/access problem.

**Action needed before manuscript finalization (Phase 6):** re-run the full pipeline end-to-end
against the current, verified-clean cohort table, and update every cohort/data-characteristics
figure in the manuscript (Abstract, Section 3.2/3.5, Table 1, Section 4.1) to match. Check whether
Experiment 1–3's *ratio-based* statistics (30.5%/26.3% dose-determined, the 0.900→0.791 AUROC
gap, 56.1% mean window overlap) are robust to this correction — they may be far less sensitive to
it than the raw counts were, since they're proportions rather than absolute row counts.

- [ ] **3.2 Data source** — exact MIMIC-IV version + PhysioNet DOI, extraction date range, CITI/credentialing reference, pipeline commit hash
- [ ] **3.3 Cohort definition** — confirm adult-age threshold and any exclusions not yet documented
- [ ] **3.4 Temporal discretization** — confirm bin anchoring (ICU admission vs. clock time), overlapping vs. non-overlapping bins, missing-bin handling, whether decision points span the full stay or only the vasopressor-eligible window
- [ ] **3.5 State construction** — confirm the per-feature aggregation statistic (last value / mean / worst-in-window) — this directly affects how Experiment 3's overlap numbers should be read
- [ ] **3.5 SOFA computation** — confirm renal-via-creatinine-only is the *sole* simplification vs. full SOFA; confirm source tables/units per subscore
- [ ] **3.6 Action definition** — binary vs. dose-level; minimum duration/dose threshold for a positive label; boundary handling when an infusion starts/stops mid-bin; multi-agent aggregation rule. **Flagged as essential in the manuscript itself** — this changes what the 44.6% and all Exp. 2 AUROCs mean.
- [ ] **4.1 Cohort flow diagram** — standard STROBE-style flow chart from initial ICU stays → final analytic cohort

**Claude Code prompt (paste into VS Code):**
> Open `notebook/Sepsis_RL_SOFA_Leakage_Experiments.ipynb`. For each of the following, find the exact
> line(s) of code that implement it and write the answer as a short paragraph I can paste into the
> manuscript, quoting the relevant code: (1) bin anchoring and missing-bin handling in Section 4
> ("Bin Everything at Two Resolutions"), (2) the per-feature aggregation statistic used when
> building `sofa_4h`/`sofa_24h`, (3) the exact vasopressor action-labeling rule in
> `build_action_labels` — binary vs. dose-based, boundary handling, multi-agent aggregation. Do not
> infer anything not visible in the code; flag anything ambiguous instead of guessing.

---

## Phase 2 — Negative controls (Experiment 5)

This is the load-bearing phase for credibility: the 0.108 AUROC gap in Experiment 2 is explicitly
reported as an *upper bound* until this battery runs. Notebook cell already scaffolds all four
controls (`## 10. Experiment 5 — Negative Controls`) but has not been executed (`outputs=0`).

- [ ] Run (a) shuffled-label control — should collapse to ~0.5 AUROC
- [ ] Run (b) multi-offset temporal decay curve (0h/4h/8h/16h/32h) — report the *shape*, not one point; a slow decay is itself a finding (treatment persistence), not a failed control
- [ ] (c) physiology-only baseline — already satisfied by variant E (AUROC 0.791); just cross-reference
- [ ] Run (d) prevalence-matched placebo features, compared like-for-like against variant E under the *same* probe (the manuscript notes the first pass compared mismatched probes — don't repeat that)
- [ ] Populate **4.5 Status of Negative Controls** with real numbers
- [ ] Update **Abstract**, **5.3 Interpretation of Action Recoverability**, and **Conclusion** to state whether the 0.108 gap survives these controls or should be revised down

**Claude Code prompt:**
> Run the Experiment 5 cell in `notebook/Sepsis_RL_SOFA_Leakage_Experiments.ipynb` against the live
> MIMIC-IV BigQuery connection. After it completes, summarize each of the four controls' results in
> a short table (control, AUROC, interpretation), and flag explicitly whether the decay curve in (b)
> supports "genuine leakage of the specific upcoming action" or "ordinary treatment persistence" per
> the criteria described in the cell's markdown. Save results to `results/experiment5_*` matching
> the naming convention of Experiments 1–3.

---

## Phase 3 — Decide on Experiment 4 (optional, go/no-go)

Manuscript explicitly scopes this as "if computationally feasible" and out of scope by default.

- [ ] **Decision point:** for the conference version, skip it — Experiments 1–3 + completed Exp. 5
      are enough for a methodologically complete audit paper. Revisit for the thesis (Phase 7) if
      you want a policy-sensitivity angle (e.g., "does a policy trained on variant A vs. E actually
      recommend different treatments?") — that's a natural thesis extension, not a conference-window one.

---

## Phase 4 — Statistical rigor pass

- [ ] **Abstract + 3.12 + 4.3**: insert clustered-bootstrap 95% CIs (clustered by patient) for all AUROC and MI values — scaffolding already exists in cell 21's output format (`clustered CI=(...)`); confirm bootstrap parameters (n resamples, cluster unit) and extend to MI
- [ ] **3.12**: decide and document multiple-comparisons correction across the 15 variant × probe combinations in Experiment 2
- [ ] **4.4**: complete the matched 4-hour-window overlap statistic (currently only 24h is reported — 204,372 decision points, 56.1% mean overlap)
- [ ] Decide whether calibration (ECE) and macro-F1 — already computed per cell 21's output — are reported in full or omitted; the manuscript currently defers this

**Claude Code prompt:**
> In the notebook, extend the clustered-bootstrap CI logic already used for AUROC (visible in the
> Experiment 2 cell's printed `clustered CI=(...)` output) to also cover the mutual-information
> estimates. Then compute the matching 4-hour-window version of the Experiment 3 overlap audit
> (currently only `before_correction_24h` has been run). Save both to `results/` following the
> existing file-naming convention, and print a one-paragraph summary I can paste into Sections 4.3
> and 4.4.

---

## Phase 5 — Literature completion (this is what makes it "high impact," not just "correct")

A methodologically airtight audit with a thin lit review reads as a technical note. A well-placed
one reads as a contribution. This phase is mostly reading/writing, not code — good to interleave
with Phases 1–4 rather than doing it last.

- [ ] **2.2**: verified citation table of subsequent sepsis-RL studies beyond Komorowski et al. — feeds directly into Appendix A
- [ ] **2.6**: primary causal-inference reference for post-treatment conditioning / collider bias (Hernán & Robins, or Pearl — pick based on which framing fits your Discussion better)
- [ ] **2.7**: primary methodological reference(s) on temporal-aggregation/window-overlap bias in longitudinal EHR modeling
- [ ] **References**: four remaining `[CITATION NEEDED]` markers — MIMIC-III original citation, plus the three above
- [ ] **Appendix A**: populate the literature-audit table — for each sepsis-RL study found, classify definitional-leakage risk and window-overlap risk using the manuscript's own "cautious certainty categories," sourced only from primary publications, not inferred

**This is a good candidate to do with me directly in this chat** (I have live web search here,
which Claude Code in VS Code does not by default) — happy to run the literature search and draft
verified citations + the Appendix A table next, if useful.

---

## Phase 6 — Manuscript finalization

- [ ] Sweep every remaining `[PLACEHOLDER]` and `[CITATION NEEDED]` in the docx — Phases 1–5 close essentially all of them
- [ ] Rewrite the **Abstract** with final numbers once Phase 2 and 4 land
- [ ] Update **5.8** (implications for SOFA-based rewards, not just states) if the team decides to extend scope
- [ ] Full read-through for the "DRAFT FOR INTERNAL REVIEW — NOT FOR SUBMISSION" watermark removal once genuinely ready
- [ ] Re-render `paper/....pdf` from the finalized docx and re-commit

---

## Phase 7 — Thesis-scale extensions (post-conference, longer horizon)

The conference version (Phases 1–6) is a complete, defensible audit paper. A thesis bridging **MIT
computational rigor** and **BU clinical/public-health framing** benefits from going further in a
few directions — pick based on time, not all of them are necessary:

- [ ] **Cross-dataset replication** — you already have eICU experience via `criticaldata/benchmaxxing`; replicating Experiments 1–3 on eICU would be a strong generalizability chapter and directly showcases both labs' data assets
- [ ] **Beyond vasopressors** — extend the audit to fluid administration, the other half of the AI Clinician's action space
- [ ] **Reward-function leakage** — SOFA is used in *rewards*, not just states, in several sepsis-RL papers (touches your Appendix A audit); a short section quantifying reward-side leakage would broaden the contribution
- [ ] **Policy-sensitivity study** — the deferred Experiment 4, done properly, as a thesis chapter rather than a conference addendum
- [ ] **Clinical framing chapter** (BU SPH side) — health-equity angle: does state-representation leakage differentially affect subpopulations underrepresented in MIMIC (relevant to your MENA-representation work)? Worth flagging even if not run, as a limitations→future-work bridge
- [ ] **Defense-ready structure** — expand Related Work into a full literature chapter, add a formal Methods appendix with reproducibility checklist

---

## Phase 8 — Venue strategy (to revisit once Phase 6 is done, not before)

Worth deciding once the completed-controls version exists — the choice affects formatting and
required rigor. Fits for this kind of methodological-audit paper (not a treatment-effectiveness
claim) tend to be:
- **ML/health-specific venues**: Machine Learning for Healthcare (MLHC), Conference on Health,
  Inference and Learning (CHIL), NeurIPS/ICML health-ML workshops
- **Clinical informatics journals**: JAMIA, npj Digital Medicine, PLOS Digital Health (you've
  reviewed for them before), Critical Care Medicine (methodology section)

I can pull current CFPs/deadlines when you're ready to decide — timing matters more than ranking here.

---

## Suggested near-term order

Given the conference deadline, the realistic path is **Phase 1 → Phase 2 → Phase 4 → Phase 6**,
running **Phase 5 in parallel with me in this chat** since it doesn't need BigQuery access. Phase 3
is a deliberate skip for now. Phase 7–8 start after the conference, feeding the thesis.

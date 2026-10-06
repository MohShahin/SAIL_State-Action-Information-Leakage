-- =============================================================================
-- 04_ventilation_status.sql
-- Purpose: extract mechanical-ventilation events for the cohort. Required by the
--          official Vincent et al. (1996) SOFA respiratory criterion, whose
--          scores 3-4 require the patient to be on ventilatory support, not
--          just have a qualifying PaO2/FiO2 ratio -- a conditional this
--          project's own sofa_resp implementation does not yet apply (see
--          docs/PHASE_PLAN_TERMINOLOGY_REVISION.md, Phase 5).
-- Source:  MIMIC-IV v3.1 on BigQuery
-- [duckdb] Source (this port): DuckDB mimic4.db built by mimic-code (see 01_cohort.sql)
-- Depends on: 01_cohort.sql having already written `__SCRATCH_DATASET__.sepsis_cohort`
-- [duckdb] Depends on: 01_cohort.sql having created sail.sepsis_cohort
-- Output:  one row per ventilation episode (stay_id, start/end time)
-- =============================================================================

-- itemid -> ventilation type (from physionet-data.mimiciv_3_1_icu.d_items,
-- category "2-Ventilation", linksto procedureevents -- confirmed by direct
-- dictionary query, not assumed from memory):
--   225792 -> Invasive Ventilation
--   225794 -> Non-invasive Ventilation
-- physionet-data.mimiciv_derived.ventilation (a validated, pre-built classification
-- of ventilation status) was checked and is NOT accessible under this project's
-- BigQuery grant (Access Denied) -- this query reconstructs the equivalent signal
-- directly from procedureevents instead, the same pattern already used for
-- vasopressor dose extraction in 03_vasopressor_doses.sql (start/end-timestamped
-- events, not periodic chart snapshots).
-- [duckdb] mimiciv_derived.ventilation DOES exist in the DuckDB build (mimic-code
-- [duckdb] concepts_duckdb/treatment/ventilation.sql). It is deliberately NOT used
-- [duckdb] here so Experiment 7 reproduces the published procedureevents-based
-- [duckdb] numbers; a comparison against mimiciv_derived.ventilation is a separate,
-- [duckdb] optional check.

-- [duckdb] TIMESTAMP_DIFF(a, b, MINUTE) / 60.0 -> date_diff('minute', b, a) / 60.0 (boundary counting)
-- [duckdb] (see the time-arithmetic note in 02_vitals_labs_fio2.sql).
SELECT
  pe.stay_id, pe.itemid, pe.starttime, pe.endtime,
  date_diff('minute', c.intime, pe.starttime) / 60.0 AS start_hours_from_admit,  -- [duckdb] was TIMESTAMP_DIFF(pe.starttime, c.intime, MINUTE) / 60.0
  date_diff('minute', c.intime, pe.endtime) / 60.0 AS end_hours_from_admit       -- [duckdb] was TIMESTAMP_DIFF(pe.endtime, c.intime, MINUTE) / 60.0
FROM mimiciv_icu.procedureevents pe                                    -- [duckdb]
JOIN sail.sepsis_cohort c USING(stay_id)                               -- [duckdb]
WHERE pe.itemid IN (225792, 225794)
  AND pe.endtime IS NOT NULL;
-- [duckdb] endtime is NOT NULL in mimic-code's create.sql; predicate kept verbatim.

-- Post-processing (done in pandas, not SQL): "ventilated at decision point t" is
-- defined as any invasive OR non-invasive ventilation interval overlapping t's
-- lookback window -- the same any-active-interval logic already used for the
-- vasopressor "any action" label in Experiments 2/3, not distinguishing
-- invasive from non-invasive (the official 1996 rule does not distinguish
-- ventilation modality for the respiratory subscore).

-- =============================================================================
-- 04_ventilation_status.sql
-- Purpose: extract mechanical-ventilation events for the cohort. Required by the
--          official Vincent et al. (1996) SOFA respiratory criterion, whose
--          scores 3-4 require the patient to be on ventilatory support, not
--          just have a qualifying PaO2/FiO2 ratio -- a conditional this
--          project's own sofa_resp implementation does not yet apply (see
--          docs/PHASE_PLAN_TERMINOLOGY_REVISION.md, Phase 5).
-- Source:  MIMIC-IV v3.1 on BigQuery
-- Depends on: 01_cohort.sql having already written `__SCRATCH_DATASET__.sepsis_cohort`
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

SELECT
  pe.stay_id, pe.itemid, pe.starttime, pe.endtime,
  TIMESTAMP_DIFF(pe.starttime, c.intime, MINUTE) / 60.0 AS start_hours_from_admit,
  TIMESTAMP_DIFF(pe.endtime, c.intime, MINUTE) / 60.0 AS end_hours_from_admit
FROM `physionet-data.mimiciv_3_1_icu.procedureevents` pe
JOIN `__SCRATCH_DATASET__.sepsis_cohort` c USING(stay_id)
WHERE pe.itemid IN (225792, 225794)
  AND pe.endtime IS NOT NULL;

-- Post-processing (done in pandas, not SQL): "ventilated at decision point t" is
-- defined as any invasive OR non-invasive ventilation interval overlapping t's
-- lookback window -- the same any-active-interval logic already used for the
-- vasopressor "any action" label in Experiments 2/3, not distinguishing
-- invasive from non-invasive (the official 1996 rule does not distinguish
-- ventilation modality for the respiratory subscore).

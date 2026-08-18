-- =============================================================================
-- 03_vasopressor_doses.sql
-- Purpose: extract raw, per-drug vasopressor dose/infusion events for the
--          cohort. This is what drives both the Experiment 1 SOFA
--          cardiovascular decomposition (dose-scored drugs only) and the
--          Experiment 2/3 "any vasopressor active" action/overlap labels
--          (all six agents).
-- Source:  MIMIC-IV v3.1 on BigQuery
-- Depends on: 01_cohort.sql having already written `__SCRATCH_DATASET__.sepsis_cohort`
-- Output:  one row per infusion event (stay_id, drug, start/end time, rate, amount)
-- =============================================================================

-- itemid -> drug map (all six vasopressor/inotrope agents used anywhere in the
-- pipeline; only four of these — norepi, epi, dopamine, dobutamine — are
-- scored by dose in the classic (Vincent et al., 1996) cardiovascular SOFA
-- rule and are used in the Experiment 1 decomposition):
--   221906 -> norepinephrine
--   221289 -> epinephrine
--   221662 -> dopamine
--   221653 -> dobutamine
--   221749 -> phenylephrine   (action label only, not part of the 1996 dose rule)
--   222315 -> vasopressin     (action label only, not part of the 1996 dose rule)

SELECT
  ie.stay_id, ie.itemid, ie.starttime, ie.endtime, ie.rate, ie.rateuom, ie.amount,
  TIMESTAMP_DIFF(ie.starttime, c.intime, MINUTE) / 60.0 AS start_hours_from_admit,
  TIMESTAMP_DIFF(ie.endtime, c.intime, MINUTE) / 60.0 AS end_hours_from_admit
FROM `physionet-data.mimiciv_3_1_icu.inputevents` ie
JOIN `__SCRATCH_DATASET__.sepsis_cohort` c USING(stay_id)
WHERE ie.itemid IN (221906, 221289, 221662, 221653, 221749, 222315)
  AND ie.amount > 0
  AND ie.endtime IS NOT NULL;

-- Post-processing (done in pandas, not SQL — see notebook Section 3):
--   1. Rows for the four dose-scored drugs (norepi, epi, dopamine, dobutamine)
--      are checked against rateuom = 'mcg/kg/min'; any row in a different unit
--      is DROPPED from the dose-decomposition arithmetic (not converted), to
--      avoid a silent unit-conversion error, and logged as a warning.
--   2. All six drugs (including phenylephrine, vasopressin) feed the "any
--      vasopressor active" action/overlap labels used in Experiments 2 and 3.
--      Only the four dose-scored drugs feed the Experiment 1 SOFA
--      cardiovascular decomposition.

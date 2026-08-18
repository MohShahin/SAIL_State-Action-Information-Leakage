-- =============================================================================
-- 01b_cohort_fallback.sql
-- Use only if 01_cohort.sql fails with a NotFound error on
-- `physionet-data.mimiciv_3_1_derived.sepsis3` — some BigQuery grants do not
-- include the mimiciv_derived dataset.
--
-- IMPORTANT: this fallback drops the Sepsis-3 infection/SOFA-delta filter
-- entirely, weakening the cohort's external-validity claim (it becomes
-- "vasopressor-treated ICU stays," not "Sepsis-3-qualifying vasopressor-
-- treated ICU stays"). If you use this version, report it as a documented
-- deviation from the pre-specified protocol — see manuscript Section 3.3.
-- =============================================================================

WITH ranked_icu AS (
  SELECT
    ie.subject_id, ie.hadm_id, ie.stay_id, ie.intime, ie.outtime, ie.los,
    ie.first_careunit, p.anchor_age, adm.deathtime, adm.hospital_expire_flag,
    ROW_NUMBER() OVER (PARTITION BY ie.subject_id ORDER BY ie.intime) AS rn
  FROM `physionet-data.mimiciv_3_1_icu.icustays` ie
  JOIN `physionet-data.mimiciv_3_1_hosp.patients` p USING(subject_id)
  JOIN `physionet-data.mimiciv_3_1_hosp.admissions` adm USING(hadm_id)
  WHERE ie.first_careunit NOT IN ('NICU', 'PICU')
    AND p.anchor_age >= 18
    AND ie.los >= 1.0
),
first_icu AS (
  SELECT * FROM ranked_icu WHERE rn = 1
),
vasopressor_stays AS (
  SELECT DISTINCT stay_id
  FROM `physionet-data.mimiciv_3_1_icu.inputevents`
  WHERE itemid IN (221906, 221289, 222315, 221749, 221662)
    AND amount > 0
)
SELECT f.*
FROM first_icu f
INNER JOIN vasopressor_stays v USING(stay_id)
LIMIT 20000;

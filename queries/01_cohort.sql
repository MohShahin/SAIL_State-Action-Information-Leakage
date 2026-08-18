-- =============================================================================
-- 01_cohort.sql
-- Purpose: extract the analytic cohort — adult, first-ICU-stay, Sepsis-3–
--          qualifying, vasopressor-exposed ICU stays.
-- Source:  MIMIC-IV v3.1 on BigQuery (`physionet-data.mimiciv_3_1_*`)
-- Output:  one row per stay_id (cohort_df in the notebook)
-- Requires: credentialed PhysioNet access + a GCP project with the MIMIC-IV
--           BigQuery dataset shared to it. See ../DATA_ACCESS.md.
--
-- Run this first — every other query in this folder joins against the
-- scratch table this query writes (`__SCRATCH_DATASET__.sepsis_cohort`).
-- =============================================================================

-- Replace __SCRATCH_DATASET__ with your own scratch dataset, e.g. my-project.temp_dataset
-- Replace __PROJECT_ID__ accordingly. Use render_query.py (in this folder)
-- rather than hand-editing — manual find-replace previously broke this by
-- stripping the backticks around the hyphenated `physionet-data` project id,
-- which BigQuery requires quoted (unquoted hyphens are a syntax error).

WITH ranked_icu AS (
  SELECT
    ie.subject_id, ie.hadm_id, ie.stay_id, ie.intime, ie.outtime, ie.los,
    ie.first_careunit, p.anchor_age, adm.deathtime, adm.hospital_expire_flag,
    ROW_NUMBER() OVER (PARTITION BY ie.subject_id ORDER BY ie.intime) AS rn
  FROM `physionet-data.mimiciv_3_1_icu.icustays` ie
  JOIN `physionet-data.mimiciv_3_1_hosp.patients` p USING(subject_id)
  JOIN `physionet-data.mimiciv_3_1_hosp.admissions` adm USING(hadm_id)
  WHERE ie.first_careunit NOT IN ('NICU', 'PICU')
    AND p.anchor_age >= 18            -- adult only
    AND ie.los >= 1.0                 -- at least 1 day in the ICU
),
first_icu AS (
  -- first ICU stay per patient only (rn = 1)
  SELECT * FROM ranked_icu WHERE rn = 1
),
vasopressor_stays AS (
  -- any of: norepinephrine (221906), epinephrine (221289), vasopressin (222315),
  -- phenylephrine (221749), dopamine (221662)
  SELECT DISTINCT stay_id
  FROM `physionet-data.mimiciv_3_1_icu.inputevents`
  WHERE itemid IN (221906, 221289, 222315, 221749, 221662)
    AND amount > 0
),
sepsis3_stays AS (
  -- MIMIC-IV's derived Sepsis-3 concept table (mimiciv_derived.sepsis3).
  -- NOTE: this table is not present in every BigQuery grant — see the
  -- fallback query in 01b_cohort_fallback.sql if you hit a NotFound error.
  SELECT DISTINCT stay_id
  FROM `physionet-data.mimiciv_3_1_derived.sepsis3`
  WHERE sepsis3 IS TRUE
)
SELECT f.*
FROM first_icu f
INNER JOIN vasopressor_stays v USING(stay_id)
INNER JOIN sepsis3_stays s USING(stay_id)
LIMIT 20000;

-- Expected result on the full MIMIC-IV v3.1 release: 11,354 stays (as reported
-- in the manuscript). If your count differs materially, check the MIMIC-IV
-- version in DATA_ACCESS.md before assuming a bug — cohort counts do shift
-- slightly across MIMIC-IV point releases.

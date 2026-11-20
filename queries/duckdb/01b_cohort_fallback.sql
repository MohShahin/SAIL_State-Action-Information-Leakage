-- =============================================================================
-- 01b_cohort_fallback.sql
-- Use only if 01_cohort.sql fails with a NotFound error on
-- `physionet-data.mimiciv_3_1_derived.sepsis3`; some BigQuery grants do not
-- include the mimiciv_derived dataset.
-- [duckdb] DuckDB equivalent: "Catalog Error: Table with name sepsis3 does not
-- [duckdb] exist" if the loader ran with MIMIC_MAKE_CONCEPTS=false. On ORCD the
-- [duckdb] concepts ARE built, so this file should not be needed; it is ported
-- [duckdb] only so the fallback path stays runnable.
--
-- IMPORTANT: this fallback drops the Sepsis-3 infection/SOFA-delta filter
-- entirely, weakening the cohort's external-validity claim (it becomes
-- "vasopressor-treated ICU stays," not "Sepsis-3-qualifying vasopressor-
-- treated ICU stays"). If you use this version, report it as a documented
-- deviation from the pre-specified protocol; see manuscript Section 3.3.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS sail;                                      -- [duckdb]
CREATE OR REPLACE TABLE sail.sepsis_cohort AS                          -- [duckdb] same target table as 01_cohort.sql
WITH ranked_icu AS (
  SELECT
    ie.subject_id, ie.hadm_id, ie.stay_id, ie.intime, ie.outtime, ie.los,
    ie.first_careunit, p.anchor_age, adm.deathtime, adm.hospital_expire_flag,
    ROW_NUMBER() OVER (PARTITION BY ie.subject_id ORDER BY ie.intime) AS rn
  FROM mimiciv_icu.icustays ie                                         -- [duckdb]
  JOIN mimiciv_hosp.patients p USING(subject_id)                       -- [duckdb]
  JOIN mimiciv_hosp.admissions adm USING(hadm_id)                      -- [duckdb]
  WHERE ie.first_careunit NOT IN ('NICU', 'PICU')
    AND p.anchor_age >= 18
    AND ie.los >= 1.0
),
first_icu AS (
  SELECT * FROM ranked_icu WHERE rn = 1
),
vasopressor_stays AS (
  SELECT DISTINCT stay_id
  FROM mimiciv_icu.inputevents                                         -- [duckdb]
  WHERE itemid IN (221906, 221289, 222315, 221749, 221662)
    AND amount > 0
)
SELECT f.*
FROM first_icu f
INNER JOIN vasopressor_stays v USING(stay_id)
LIMIT 20000;
-- [duckdb] LIMIT 20000 kept (binds as in BigQuery). NOTE: without the Sepsis-3
-- [duckdb] filter the cohort is larger than 11,354 and may approach this cap;
-- [duckdb] check COUNT(*) below is strictly below 20000 before trusting it.
SELECT COUNT(*) AS cohort_stays FROM sail.sepsis_cohort;               -- [duckdb]

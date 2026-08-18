-- =============================================================================
-- 02_vitals_labs_fio2.sql
-- Purpose: extract hourly-binned vitals, labs, and FiO2 for the cohort, at
--          native (hourly) resolution — later re-aggregated in pandas into
--          the 4h and 24h decision windows (see notebook Section 4).
-- Source:  MIMIC-IV v3.1 on BigQuery
-- Depends on: 01_cohort.sql having already written `__SCRATCH_DATASET__.sepsis_cohort`
-- Output:  three long-format tables (stay_id, feature, hours_from_admit, value),
--          concatenated in the notebook into `raw_long`
--
-- Run each of the three SELECTs below separately (they were separate BigQuery
-- jobs in the notebook) or adapt into one UNION ALL if you prefer a single job.
-- The horizon is set to 72 hours in the manuscript's protocol (first 72h of the stay).
-- =============================================================================

-- ---------- 2a. Vitals (incl. MAP, GCS components) ----------
WITH vital_items AS (
  SELECT * FROM UNNEST([
    STRUCT(220045 AS itemid, 'heart_rate' AS label),
    STRUCT(220179 AS itemid, 'sbp' AS label),
    STRUCT(220180 AS itemid, 'dbp' AS label),
    STRUCT(220181 AS itemid, 'mbp' AS label),           -- non-invasive MAP
    STRUCT(220052 AS itemid, 'mbp_arterial' AS label),  -- invasive MAP (some ICUs chart this instead)
    STRUCT(220210 AS itemid, 'resp_rate' AS label),
    STRUCT(220277 AS itemid, 'spo2' AS label),
    STRUCT(223761 AS itemid, 'temp_f' AS label),
    STRUCT(220739 AS itemid, 'gcs_eye' AS label),
    STRUCT(223900 AS itemid, 'gcs_verbal' AS label),
    STRUCT(223901 AS itemid, 'gcs_motor' AS label)
  ])
)
SELECT
  ce.stay_id,
  vi.label AS feature,
  FLOOR(TIMESTAMP_DIFF(ce.charttime, c.intime, MINUTE) / 60.0) AS hours_from_admit,
  AVG(ce.valuenum) AS value
FROM `physionet-data.mimiciv_3_1_icu.chartevents` ce
JOIN `__SCRATCH_DATASET__.sepsis_cohort` c USING(stay_id)
JOIN vital_items vi ON ce.itemid = vi.itemid
WHERE ce.valuenum IS NOT NULL AND ce.valuenum > 0
  AND TIMESTAMP_DIFF(ce.charttime, c.intime, HOUR) BETWEEN 0 AND __HORIZON_HOURS__
  AND ce.warning = 0
GROUP BY 1, 2, 3;

-- NOTE (post-processing, done in pandas, not SQL): the two MAP item IDs
-- (mbp, mbp_arterial) are consolidated into a single 'mbp' feature after
-- extraction — non-invasive preferred, arterial used where non-invasive is
-- missing at that timestamp.

-- ---------- 2b. Labs ----------
WITH lab_items AS (
  SELECT * FROM UNNEST([
    STRUCT(50912 AS itemid, 'creatinine' AS label),
    STRUCT(50885 AS itemid, 'bilirubin_total' AS label),
    STRUCT(51265 AS itemid, 'platelets' AS label),
    STRUCT(51301 AS itemid, 'wbc' AS label),
    STRUCT(50813 AS itemid, 'lactate' AS label),
    STRUCT(50971 AS itemid, 'potassium' AS label),
    STRUCT(50983 AS itemid, 'sodium' AS label),
    STRUCT(51006 AS itemid, 'bun' AS label),
    STRUCT(50821 AS itemid, 'pao2' AS label),
    STRUCT(50818 AS itemid, 'paco2' AS label),
    STRUCT(50820 AS itemid, 'ph' AS label)
  ])
)
SELECT
  c.stay_id,
  li.label AS feature,
  FLOOR(TIMESTAMP_DIFF(le.charttime, c.intime, MINUTE) / 60.0) AS hours_from_admit,
  AVG(le.valuenum) AS value
FROM `physionet-data.mimiciv_3_1_hosp.labevents` le
JOIN `__SCRATCH_DATASET__.sepsis_cohort` c ON le.hadm_id = c.hadm_id
JOIN lab_items li ON le.itemid = li.itemid
WHERE le.valuenum IS NOT NULL
  AND TIMESTAMP_DIFF(le.charttime, c.intime, HOUR) BETWEEN 0 AND __HORIZON_HOURS__
GROUP BY 1, 2, 3;

-- ---------- 2c. FiO2 ----------
SELECT
  c.stay_id,
  'fio2' AS feature,
  FLOOR(TIMESTAMP_DIFF(ce.charttime, c.intime, MINUTE) / 60.0) AS hours_from_admit,
  AVG(ce.valuenum / 100.0) AS value          -- stored as a percentage (21-100); normalized to a fraction
FROM `physionet-data.mimiciv_3_1_icu.chartevents` ce
JOIN `__SCRATCH_DATASET__.sepsis_cohort` c USING(stay_id)
WHERE ce.itemid = 223835 AND ce.valuenum BETWEEN 21 AND 100
  AND TIMESTAMP_DIFF(ce.charttime, c.intime, HOUR) BETWEEN 0 AND __HORIZON_HOURS__
GROUP BY 1, 2, 3;

-- pao2/fio2 (P/F ratio, needed for the SOFA respiratory subscore) is computed
-- downstream in pandas from 2b's pao2 and 2c's fio2, matched by nearest hour —
-- not computed in SQL.

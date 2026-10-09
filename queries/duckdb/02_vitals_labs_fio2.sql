-- =============================================================================
-- 02_vitals_labs_fio2.sql
-- Purpose: extract hourly-binned vitals, labs, and FiO2 for the cohort, at
--          native (hourly) resolution; later re-aggregated in pandas into
--          the 4h and 24h decision windows (see notebook Section 4).
-- Source:  MIMIC-IV v3.1 on BigQuery
-- [duckdb] Source (this port): DuckDB mimic4.db built by mimic-code (see 01_cohort.sql)
-- Depends on: 01_cohort.sql having already written `__SCRATCH_DATASET__.sepsis_cohort`
-- [duckdb] Depends on: 01_cohort.sql having created sail.sepsis_cohort
-- Output:  three long-format tables (stay_id, feature, hours_from_admit, value),
--          concatenated in the notebook into `raw_long`
--
-- Run each of the three SELECTs below separately (they were separate BigQuery
-- jobs in the notebook) or adapt into one UNION ALL if you prefer a single job.
-- The horizon is set to 72 hours in the manuscript's protocol (first 72h of the stay).
-- [duckdb] __HORIZON_HOURS__ is replaced by the literal 72 (notebook cell 3, HORIZON_HOURS = 72).
-- [duckdb] To parametrize at the CLI instead:  duckdb mimic4.db -c "SET VARIABLE horizon = 72" and
-- [duckdb] use getvariable('horizon'); the notebook port passes it through the Python f-string as before.
-- =============================================================================

-- [duckdb] TIME ARITHMETIC NOTE (applies to every TIMESTAMP_DIFF below).
-- [duckdb] MIMIC-IV's BigQuery columns are DATETIME, and the published BigQuery run behaved as
-- [duckdb] unit-boundary counting on them (DATETIME_DIFF semantics), not as the truncated
-- [duckdb] microsecond difference: on the published 11,354-stay cohort boundary counting gives
-- [duckdb] exactly the published 4,850,246 physiology rows, truncation gives 4,894,707.
-- [duckdb] DuckDB's date_diff counts boundaries the same way, so the map used here is:
-- [duckdb]   TIMESTAMP_DIFF(a, b, MINUTE) -> date_diff('minute', b, a)
-- [duckdb]   TIMESTAMP_DIFF(a, b, HOUR)   -> date_diff('hour', b, a)
-- [duckdb] Example: from 23:59:59 to 01:58:00 next day is 2 hours (two boundaries), not 1.

-- ---------- 2a. Vitals (incl. MAP, GCS components) ----------
WITH vital_items AS (
  SELECT * FROM (VALUES                                                 -- [duckdb] was: SELECT * FROM UNNEST([ STRUCT(...) ... ])
    (220045, 'heart_rate'),                                            -- [duckdb]
    (220179, 'sbp'),                                                   -- [duckdb]
    (220180, 'dbp'),                                                   -- [duckdb]
    (220181, 'mbp'),           -- non-invasive MAP                     -- [duckdb]
    (220052, 'mbp_arterial'),  -- invasive MAP (some ICUs chart this instead)  -- [duckdb]
    (220210, 'resp_rate'),                                             -- [duckdb]
    (220277, 'spo2'),                                                  -- [duckdb]
    (223761, 'temp_f'),                                                -- [duckdb]
    (220739, 'gcs_eye'),                                               -- [duckdb]
    (223900, 'gcs_verbal'),                                            -- [duckdb]
    (223901, 'gcs_motor')                                              -- [duckdb]
  ) AS t(itemid, label)                                                -- [duckdb]
)
SELECT
  ce.stay_id,
  vi.label AS feature,
  FLOOR(date_diff('minute', c.intime, ce.charttime) / 60.0) AS hours_from_admit,  -- [duckdb] was FLOOR(TIMESTAMP_DIFF(ce.charttime, c.intime, MINUTE) / 60.0)
  AVG(ce.valuenum) AS value
FROM mimiciv_icu.chartevents ce                                        -- [duckdb]
JOIN sail.sepsis_cohort c USING(stay_id)                               -- [duckdb]
JOIN vital_items vi ON ce.itemid = vi.itemid
WHERE ce.valuenum IS NOT NULL AND ce.valuenum > 0
  AND date_diff('hour', c.intime, ce.charttime) BETWEEN 0 AND 72  -- [duckdb] was TIMESTAMP_DIFF(ce.charttime, c.intime, HOUR) BETWEEN 0 AND __HORIZON_HOURS__
  AND ce.warning = 0
GROUP BY 1, 2, 3;

-- NOTE (post-processing, done in pandas, not SQL): the two MAP item IDs
-- (mbp, mbp_arterial) are consolidated into a single 'mbp' feature after
-- extraction; non-invasive preferred, arterial used where non-invasive is
-- missing at that timestamp.

-- ---------- 2b. Labs ----------
WITH lab_items AS (
  SELECT * FROM (VALUES                                                 -- [duckdb] was: SELECT * FROM UNNEST([ STRUCT(...) ... ])
    (50912, 'creatinine'),                                             -- [duckdb]
    (50885, 'bilirubin_total'),                                        -- [duckdb]
    (51265, 'platelets'),                                              -- [duckdb]
    (51301, 'wbc'),                                                    -- [duckdb]
    (50813, 'lactate'),                                                -- [duckdb]
    (50971, 'potassium'),                                              -- [duckdb]
    (50983, 'sodium'),                                                 -- [duckdb]
    (51006, 'bun'),                                                    -- [duckdb]
    (50821, 'pao2'),                                                   -- [duckdb]
    (50818, 'paco2'),                                                  -- [duckdb]
    (50820, 'ph')                                                      -- [duckdb]
  ) AS t(itemid, label)                                                -- [duckdb]
)
SELECT
  c.stay_id,
  li.label AS feature,
  FLOOR(date_diff('minute', c.intime, le.charttime) / 60.0) AS hours_from_admit,  -- [duckdb] was FLOOR(TIMESTAMP_DIFF(le.charttime, c.intime, MINUTE) / 60.0)
  AVG(le.valuenum) AS value
FROM mimiciv_hosp.labevents le                                         -- [duckdb]
JOIN sail.sepsis_cohort c ON le.hadm_id = c.hadm_id                    -- [duckdb]
JOIN lab_items li ON le.itemid = li.itemid
WHERE le.valuenum IS NOT NULL
  AND date_diff('hour', c.intime, le.charttime) BETWEEN 0 AND 72  -- [duckdb] was TIMESTAMP_DIFF(le.charttime, c.intime, HOUR) BETWEEN 0 AND __HORIZON_HOURS__
GROUP BY 1, 2, 3;

-- ---------- 2c. FiO2 ----------
SELECT
  c.stay_id,
  'fio2' AS feature,
  FLOOR(date_diff('minute', c.intime, ce.charttime) / 60.0) AS hours_from_admit,  -- [duckdb] was FLOOR(TIMESTAMP_DIFF(ce.charttime, c.intime, MINUTE) / 60.0)
  AVG(ce.valuenum / 100.0) AS value          -- stored as a percentage (21-100); normalized to a fraction
FROM mimiciv_icu.chartevents ce                                        -- [duckdb]
JOIN sail.sepsis_cohort c USING(stay_id)                               -- [duckdb]
WHERE ce.itemid = 223835 AND ce.valuenum BETWEEN 21 AND 100
  AND date_diff('hour', c.intime, ce.charttime) BETWEEN 0 AND 72  -- [duckdb] was TIMESTAMP_DIFF(ce.charttime, c.intime, HOUR) BETWEEN 0 AND __HORIZON_HOURS__
GROUP BY 1, 2, 3;

-- pao2/fio2 (P/F ratio, needed for the SOFA respiratory subscore) is computed
-- downstream in pandas from 2b's pao2 and 2c's fio2, matched by nearest hour;
-- not computed in SQL.

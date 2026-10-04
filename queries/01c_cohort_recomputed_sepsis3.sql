-- =============================================================================
-- 01c_cohort_recomputed_sepsis3.sql
-- Purpose: the cell 5 cohort (adult, first ICU stay, LOS >= 1 day, vasopressor-
--          exposed) with Sepsis-3 RECOMPUTED from mimiciv_3_1_derived.sofa and
--          suspicion_of_infection, instead of read from the published
--          mimiciv_3_1_derived.sepsis3 table.
-- Sepsis-3 logic: mimic-code mimic-iv/concepts/sepsis/sepsis3.sql (MIT-LCP),
--          adapted only by pointing its table references at mimiciv_3_1_derived.
--          Earliest suspicion-of-infection row per stay (rn_sus = 1); a stay is
--          Sepsis-3 when SOFA >= 2 with suspected infection in the 48h-before to
--          24h-after window.
-- Output:  one row per stay_id; NO LIMIT.
-- Status:  NOT the cohort the notebook ran. Cell 5 and queries/01_cohort.sql
--          use the published sepsis3 table, which is a strict subset of this
--          recomputation (see the audit: 32,899 published vs 41,295 recomputed).
-- Verified counts (SELECT COUNT(*) against this logic, see audit notes):
--          stage 3 first stay 54,551; stage 4 vasopressor 18,399;
--          stage 5 Sepsis-3 13,192. By anchor_year_group: 3,698 / 3,086 /
--          3,302 / 2,255 / 851.
-- Requires: credentialed PhysioNet access + BigQuery access to MIMIC-IV v3.1.
--           Replace the project id with your own; see ../DATA_ACCESS.md.
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
sepsis3_recomputed AS (
  -- Sepsis-3 recomputed with the mimic-code logic (one row per stay, rn_sus = 1)
  -- rather than read from mimiciv_3_1_derived.sepsis3.
  SELECT DISTINCT stay_id
  FROM (
    -- Creates a table with "onset" time of Sepsis-3 in the ICU.
    -- That is, the earliest time at which a patient had SOFA >= 2
    -- and suspicion of infection.
    -- As many variables used in SOFA are only collected in the ICU,
    -- this query can only define sepsis-3 onset within the ICU.

    -- extract rows with SOFA >= 2
    -- implicitly this assumes baseline SOFA was 0 before ICU admission.
    WITH sofa AS (
        SELECT stay_id
            , starttime, endtime
            , respiration_24hours AS respiration
            , coagulation_24hours AS coagulation
            , liver_24hours AS liver
            , cardiovascular_24hours AS cardiovascular
            , cns_24hours AS cns
            , renal_24hours AS renal
            , sofa_24hours AS sofa_score
        FROM `physionet-data.mimiciv_3_1_derived.sofa`
        WHERE sofa_24hours >= 2
    )

    , s1 AS (
        SELECT
            soi.subject_id
            , soi.stay_id
            -- suspicion columns
            , soi.ab_id
            , soi.antibiotic
            , soi.antibiotic_time
            , soi.culture_time
            , soi.suspected_infection
            , soi.suspected_infection_time
            , soi.specimen
            , soi.positive_culture
            -- sofa columns
            , starttime, endtime
            , respiration, coagulation, liver, cardiovascular, cns, renal
            , sofa_score
            -- All rows have an associated suspicion of infection event
            -- Therefore, Sepsis-3 is defined as SOFA >= 2.
            -- Implicitly, the baseline SOFA score is assumed to be zero,
            -- as we do not know if the patient has preexisting
            -- (acute or chronic) organ dysfunction before the onset
            -- of infection.
            , sofa_score >= 2 AND suspected_infection = 1 AS sepsis3
            -- subselect to the earliest suspicion/antibiotic/SOFA row
            , ROW_NUMBER() OVER
            (
                PARTITION BY soi.stay_id
                ORDER BY
                    suspected_infection_time, antibiotic_time, culture_time, endtime
            ) AS rn_sus
        FROM `physionet-data.mimiciv_3_1_derived.suspicion_of_infection` AS soi
        INNER JOIN sofa
            ON soi.stay_id = sofa.stay_id
                AND sofa.endtime >= DATETIME_SUB(
                    soi.suspected_infection_time, INTERVAL '48' HOUR
                )
                AND sofa.endtime <= DATETIME_ADD(
                    soi.suspected_infection_time, INTERVAL '24' HOUR
                )
        -- only include in-ICU rows
        WHERE soi.stay_id IS NOT NULL
    )

    SELECT
        subject_id, stay_id
        -- note: there may be more than one antibiotic given at this time
        , antibiotic_time
        -- culture times may be dates, rather than times
        , culture_time
        , suspected_infection_time
        -- endtime is latest time at which the SOFA score is valid
        , endtime AS sofa_time
        , sofa_score
        , respiration, coagulation, liver, cardiovascular, cns, renal
        , sepsis3
    FROM s1
    WHERE rn_sus = 1
  )
  WHERE sepsis3
)
SELECT f.*
FROM first_icu f
INNER JOIN vasopressor_stays v USING(stay_id)
INNER JOIN sepsis3_recomputed s USING(stay_id)

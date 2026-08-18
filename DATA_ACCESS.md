# Data access and what can (and can't) live in this repository

MIMIC-IV is credentialed-access data under a PhysioNet Data Use Agreement (DUA), not open data.
This file is the single place documenting what that means for this repo. **When in doubt about a
specific file, leave it out and ask — this doc gives the general rule, not a substitute for reading
your own signed DUA.** I'm not a lawyer; this reflects standard practice across MIMIC-based
open-source projects (including MIT-LCP's own public repos), not a legal opinion.

## The short version

| | Safe to publish on GitHub | Not safe to publish on GitHub |
|---|---|---|
| **SQL queries / extraction code** | ✅ Yes — code isn't data | |
| **Analysis code (notebook, scripts)** | ✅ Yes | |
| **Aggregate statistics reported in the manuscript** (counts, percentages, AUROCs, CIs) | ✅ Yes — that's what a paper *is* | |
| **Row-level or patient-level extracted data** (any CSV with one row per `stay_id` or per timestep) | | ❌ No |
| **Model artifacts trained on row-level features** (pickled models, raw feature matrices) | | ❌ No, unless you've specifically confirmed they carry no re-identification risk |
| **BigQuery credentials, project IDs tied to your billing account** | | ❌ No |

## Why

Your PhysioNet credentialing agreement for MIMIC-IV requires that you not redistribute the data, or
data derived from it at patient- or timestep-level granularity, to anyone who hasn't independently
completed the same credentialing (CITI training + PhysioNet data use agreement). A public GitHub
repo is, by definition, redistribution to uncredentialed people — regardless of your intent, and
regardless of whether the data has been "de-identified" already (MIMIC-IV itself is already
de-identified; the DUA restriction is about *access control*, not re-identification risk alone).

**Aggregate, already-published statistics are the exception** — the whole point of the DUA is that
credentialed researchers can publish findings from the data, just not the data (or row-level
derivatives of it) itself. A sentence like "30.5% of eligible timesteps were dose-determined" in
your manuscript or README is fine. A CSV with one row per `stay_id` and a dose-determined flag is
not, even though it's "just" a summary of the same underlying finding.

## What this means for this repo specifically

- `queries/*.sql` — safe, already public
- `notebook/*.ipynb` — safe as long as **cell outputs are cleared or contain only aggregate
  print statements** before committing (see checklist below) — not raw dataframes
- `paper/*.pdf`, `paper/*.docx` — safe; contains only aggregate results
- `results/` — **gitignored by default** (see below). If you want to publish a specific aggregate
  summary file (e.g. `experiment1_summary.json`, if it truly contains only counts/percentages and
  no per-stay rows), review it by hand first and add it back explicitly — don't bulk-unignore the folder
- Anything under `data/`, `*.csv`, `*.parquet` at the repo root or in `notebook/` — gitignored

## Before every commit that touches the notebook

1. Check for any output cell that printed a `.head()`, `.sample()`, or full dataframe rather than an
   aggregate statistic — clear that cell's output before committing
   (`jupyter nbconvert --clear-output --inplace notebook/*.ipynb` clears all outputs at once if you'd
   rather regenerate them fresh each time)
2. Check `results/` isn't accidentally staged (`git status` — it shouldn't show up; `.gitignore` covers it)
3. If unsure whether a specific number is "aggregate enough," a reasonable rule of thumb used across
   MIMIC-based publications: any statistic derived from a group of **at least a few dozen** patients,
   reported as a summary (mean/percentage/count), is standard practice to publish. A statistic that
   could isolate a single patient or a very small group is not.

## Getting your own MIMIC-IV BigQuery access (for anyone cloning this repo)

1. Complete CITI "Data or Specimens Only Research" training
2. Apply for credentialed access to MIMIC-IV via PhysioNet: <https://physionet.org/content/mimiciv/>
3. Request access to the `physionet-data` BigQuery project through PhysioNet's cloud-access instructions
4. Set `PROJECT_ID` / `SCRATCH_DATASET` in the notebook's config cell to your own GCP project
5. Run `queries/01_cohort.sql` first, then `02_vitals_labs_fio2.sql` and `03_vasopressor_doses.sql`
   — see `queries/README.md`

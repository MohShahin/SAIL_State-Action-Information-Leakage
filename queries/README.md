# BigQuery extraction queries (MIMIC-IV v3.1)

These are the five SQL queries behind every result in this project — they're extracted verbatim
(logic unchanged) from `notebook/Sepsis_RL_SOFA_Leakage_Experiments.ipynb`, as standalone `.sql`
files so the extraction logic is reviewable without running the notebook.

**These queries are safe to publish. Their output is not — see [`../DATA_ACCESS.md`](../DATA_ACCESS.md).**

## Run order

1. **`01_cohort.sql`** — builds the analytic cohort (11,354 stays). Writes a scratch table
   (`__SCRATCH_DATASET__.sepsis_cohort`) that every later query joins against.
   Use **`01b_cohort_fallback.sql`** instead if your BigQuery grant doesn't include
   `mimiciv_derived.sepsis3` (see the file for what that changes about the cohort claim).
2. **`02_vitals_labs_fio2.sql`** — three extractions (vitals, labs, FiO2) at native hourly
   resolution. Re-aggregated into 4h/24h decision windows downstream in pandas, not in SQL.
3. **`03_vasopressor_doses.sql`** — per-drug infusion events, used both for the Experiment 1
   SOFA-cardiovascular dose decomposition and the Experiment 2/3 action/overlap labels.
4. **`04_ventilation_status.sql`** — mechanical-ventilation episodes, used only by Experiment 7
   (respiratory SOFA's ventilatory-support conditional). Not needed for Experiments 1–3, 5, or 6.

Everything after this point — SOFA subscore computation, the five state variants (A–E), the
classifiers in Experiment 2, the window-overlap audit in Experiment 3, the mortality task in
Experiment 6, and the negative controls in Experiment 5 — is pandas/NumPy/scikit-learn on the
dataframes these queries return, not additional SQL. See the notebook directly for that logic.

## Adapting these to your own GCP project

Each query references `__SCRATCH_DATASET__` and, in the notebook, `__PROJECT_ID__` /
`__HORIZON_HOURS__` — placeholders that are Python f-string substitutions when run through the
notebook. **Use `render_query.py` to fill these in — don't hand-edit the `.sql` files.**

```bash
python3 render_query.py 01_cohort.sql --scratch-dataset my-gcp-project.temp_dataset -o /tmp/01.sql
python3 render_query.py 02_vitals_labs_fio2.sql --scratch-dataset my-gcp-project.temp_dataset --horizon-hours 72 -o /tmp/02.sql
python3 render_query.py 03_vasopressor_doses.sql --scratch-dataset my-gcp-project.temp_dataset -o /tmp/03.sql

# then either paste the output into the BigQuery console, or:
bq query --use_legacy_sql=false < /tmp/01.sql
```

**Why not just find-replace by hand?** These placeholders used to be `{SCRATCH_DATASET}` /
`{HORIZON_HOURS}` (curly braces). BigQuery Standard SQL parses `{...}` as a struct-literal
constructor, so pasting the file unmodified failed with `Invalid braced constructor element`. And
hand-editing to fix it is exactly what stripped the backticks around the hyphenated
`physionet-data` project id in one case — BigQuery requires that quoted (unquoted hyphens are a
separate syntax error). The placeholders are now double-underscore style specifically so they
can't collide with BigQuery syntax, and `render_query.py` substitutes them without touching
anything else in the file, including the backticks.

You'll need your own credentialed PhysioNet access to MIMIC-IV, with the `physionet-data` BigQuery
project shared to your GCP account. See [`../DATA_ACCESS.md`](../DATA_ACCESS.md).

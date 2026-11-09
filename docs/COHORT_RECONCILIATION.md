# Cohort reconciliation: 11,354 vs 13,192

For the team. This document records where each cohort number appears and what it refers to. **It
does not choose which number leads**; section 4 sets out both options. Prepared 2026-11-09 against
`origin/main` at `37de767`, plus the manuscript draft in `paper/` and the files that PR #2
(`h3-paired-bootstrap`) will add.

## 1. What the two numbers are

| Cohort | Definition | Release | Role today | Evidence |
|---|---|---|---|---|
| **13,192** | Adult first ICU stay, vasopressor, Sepsis-3 **recomputed** from `mimiciv_3_1_derived.sofa` + `suspicion_of_infection` (mimic-code logic) | MIMIC-IV **v3.1** throughout | Primary for H3 (Decision 1) and on the site | `queries/01c_cohort_recomputed_sepsis3.sql`, `docs/DECISIONS_H3.md` decision 1 |
| **11,354** | Same cohort query, but the Sepsis-3 condition comes from the **published** `derived.sepsis3` table | v3.1 base tables, while the **published sepsis3 table was built from MIMIC-IV v2.2** (effectively 2008-2019) | Sensitivity cohort (Decision 1); the manuscript draft's only cohort | `queries/01_cohort.sql`, `scripts/duckdb_backend.py:85`, `docs/ORCD_DUCKDB_RUN.md:31` (PR #2), DECISIONS_H3 amendment |

So "11,354 on MIMIC-IV v3.1" (`queries/01_cohort.sql`, ROADMAP: BigQuery v3.1, `icustays` = 94,458)
and "11,354 = Sepsis-3 stays of the v2.2 build" (2026-10-07 amendment, DuckDB runs) describe the
**same stay set reached two ways**. The DuckDB runs reproduce it by passing the v2.2 sepsis3
stay_ids into the v3.1 query (`SAIL_COHORT_STAYS`). Neither description is wrong, but each is
incomplete without the other. The complete label is: *"v3.1 cohort query, Sepsis-3 from the
published derived table (built from MIMIC-IV v2.2)"*.

## 2. Every occurrence on main

"Correctly labeled" means the text says, or makes unambiguous from context, which cohort the number
is and what role it plays. **Historical** means the text describes work done before Decision 1 made
13,192 primary, and it reads as such.

| File | Line | Number | Refers to | Labeled correctly? |
|---|---|---|---|---|
| `README.md` | 72 | 11,354 | published-table cohort (manuscript draft) | **Incomplete.** "Verified results" table; no release and no note that it is now the sensitivity cohort. `src/evidence.html` carries that note for the same table |
| `SAIL_PACKAGE_README.md` | 142 | 11,354 | published-table cohort | **Inconsistent with the site.** Calls it "the empirical audit" with no sensitivity label; the site's headline is 13,192. Same sentence calls H3 "not-yet-run" (stale). This is the PyPI long description |
| `ROADMAP.md` | 17, 34, 59 | 11,354 | published-table cohort, BigQuery v3.1 | Historical (Phase 0 extraction and the WRITE_APPEND fix). OK |
| `docs/DECISIONS_H3.md` | 15, 20 | 13,192 | v3.1 recomputed | Yes |
| `docs/DECISIONS_H3.md` | 18 | 11,354 | published table, "effectively 2008-2019" | Yes |
| `docs/DECISIONS_H3.md` | 56 | 11,354 | "Sepsis-3 stays of the MIMIC-IV v2.2 build" | Yes. Omits that the base query is v3.1 (see section 1) |
| `docs/PHASE_PLAN_TERMINOLOGY_REVISION.md` | 195 | 11,354 | published-table cohort (n=11,336 of 11,354) | Historical. OK |
| `docs/PI_DEFENSE_PREP.md` | 313, 501 | 11,354 | published-table cohort | Historical prep notes ("existing verified cohort"); predate Decision 1 |
| `docs/WEBSITE_REBUILD_STATUS.md` | 69, 70 | both | headline change 11,354 -> 13,192 | Yes |
| `docs/WEBSITE_REBUILD_STATUS.md` | 76 | 11,354 | demo/evidence "not audited" note | Yes as a log entry. The audit here finds both pages now label it (rows below) |
| `queries/01_cohort.sql` | 58 | 11,354 | "full MIMIC-IV v3.1 release" | **Partly.** True for the query as run on BigQuery, but omits the v2.2-built sepsis3 table and the sensitivity role |
| `queries/01c_cohort_recomputed_sepsis3.sql` | 18 | 13,192 | v3.1 recomputed | Yes |
| `queries/README.md` | 11 | 11,354 | sensitivity cohort, published table | Yes |
| `queries/README.md` | 16 | 13,192 | primary, recomputed | Yes |
| `results/experiment1_sofa_decomposition_summary.json` | 3 | 11354 | published-table cohort (`cohort_size`) | No release field. Committed result: **not to be edited** |
| `results/experiment3_summary.json` | 3 | 11354 | same | Same |
| `results/experiment6_mortality_vs_action_recoverability.json` | 4 | 11354 | same (`cohort_size_full`) | Same |
| `results/experiment7_respiratory_sofa_summary.json` | 3 | 11354 | same | Same |
| `src/demo.html` | 346 | 13,192 | primary, "MIMIC-IV v3.1" | Yes |
| `src/demo.html` | 347 | 11,354 | "published Sepsis-3 table ... sensitivity cohort" | Yes (no release, but role and table are clear) |
| `src/demo.html` | 391-392 | both | "100% ... in both" | Yes. Checked: `pct_dose_determined_treated_only` = 1.0 in `results/pinned_13192/experiment1_summary.json` (PR #2) and in the 11,354 summary |
| `src/evidence.html` | 21 | 11,354 | manuscript draft's cohort | Yes, via the note at 35-38 |
| `src/evidence.html` | 35, 37 | both | sensitivity / primary (v3.1, recomputed) | Yes |
| `src/llms.txt` | 8 | both | 13,192 headline, 11,354 sensitivity | Yes |
| `src/research.html` | 9 | both | same | Yes |
| `.claude/commands/fix-leaked-comment.md` | 23 | 11,354 | example sentence in an internal tool prompt | n/a (not published) |
| `.claude/commands/run-phase4-variant-f.md` | 21 | 11,354 | internal tool prompt | n/a (not published) |

### Manuscript draft (`paper/SOFA_Leakage_Sepsis_RL_Manuscript_DRAFT.docx` and `.pdf`)

The PDF text matches the DOCX. Line numbers below are from `pdftotext -layout`.

| Location (PDF line) | Text | Labeled correctly? |
|---|---|---|
| Abstract, 29 | "from MIMIC-IV (11,354 ICU stays; ...)" | **Release unlabeled** |
| Methods, data source, 291 | "[PLACEHOLDER ... Insert exact MIMIC-IV version number (e.g., v2.2 or later)...]" | **Open placeholder.** Neither "v2.2" nor "v3.1" alone is complete (section 1) |
| Methods, cohort, 317 | "This yielded 11,354 ICU stays as the base cohort." | Release unlabeled |
| Table, 509 | 11,354 | Release unlabeled |
| Flow diagram placeholder, 525 | "base cohort (11,354 stays)" | Release unlabeled |
| Conclusion, 876 | "In an 11,354-stay MIMIC-IV sepsis cohort" | Release unlabeled |

13,192 does not appear in the manuscript.

### Added by PR #2 (not on main yet)

PR #2 adds about 40 occurrences: `results/README.md`, `results/pinned_13192/`,
`results/primary_13192/`, `results/sensitivity_v22_11354/`, the H3 JSONs,
`results/experiment0_cohort_duckdb_diagnostics.json`, `docs/ORCD_DUCKDB_RUN.md` and
`queries/duckdb/`. The README-type files label both cohorts with role and release (e.g.
`results/README.md:27`: "Sepsis-3 stays of a MIMIC-IV v2.2 build applied to the v3.1 cohort
query"). One repeats the partial label: `queries/duckdb/01_cohort.sql:75` ("full MIMIC-IV v3.1
release: 11,354").

## 3. Text fixes

**None applied.** No occurrence is mislabeled in a way that can be fixed without first deciding
which cohort leads:

- `README.md:72` and `SAIL_PACKAGE_README.md:142` need a decision about the headline before they can change.
- `queries/01_cohort.sql:58` is true as written. Completing it ("Sepsis-3 from the published table,
  which was built from MIMIC-IV v2.2") is a safe improvement once the team agrees on the wording.
- The `results/*.json` files are committed results and stay as they are.

Separate from cohort labeling: `SAIL_PACKAGE_README.md:142` says H3 is "not-yet-run", which is stale
since the 2026-10-07 amendment. It ships in the PyPI description.

## 4. Options for the team (not decided here)

### Option A: 13,192 leads, 11,354 as sensitivity

- Matches Decision 1 (H3 primary), the site, `llms.txt` and `research.html`.
- Single release (v3.1) throughout; Sepsis-3 recomputed with public mimic-code logic.
- **Costs:** the manuscript's abstract, Methods, Table and Conclusion move to 13,192, and every
  Exp 1 to 3 number is replaced from `results/primary_13192/` / `pinned_13192/`. For example, Exp 1
  dose-determined is 34.9% (4h) / 31.0% (24h) on 13,192 vs 32.3% / 28.6% on 11,354. The
  long-verified 11,354 numbers become the sensitivity column. `README.md:72` and
  `SAIL_PACKAGE_README.md:142` need updating.

### Option B: 11,354 leads, 13,192 as sensitivity

- Matches the manuscript draft, the README "Verified results" table and the package README. It
  has the longest verification history, and anyone with BigQuery access can reproduce it from the
  published table.
- **Costs:** H3 was pre-registered with 13,192 as primary (Decision 1, frozen before the final run).
  The paper would have to report H3 on its pre-registered primary and everything else on a
  different lead cohort, or say clearly that H3's primary differs from the paper's lead cohort.
  Changing H3's primary after seeing results is not an option under DECISIONS_H3. The site
  headline (changed on 2026-10-07) would need to change back.
- The release label must be the full one from section 1: "v2.2" alone or "v3.1" alone would be
  wrong.

### Either way

- Fill the manuscript's MIMIC-IV version placeholder with the section 1 wording for 11,354, and
  "v3.1, Sepsis-3 recomputed" for 13,192.
- Use one wording for 11,354 everywhere (site, READMEs, `queries/01_cohort.sql`,
  `queries/duckdb/01_cohort.sql`).

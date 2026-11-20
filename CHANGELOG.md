# Changelog

This file starts at 0.1.5. Earlier releases (0.1.0-0.1.4) aren't backfilled here -- see the git
tags and commit history for their changes.

## Unreleased

- New command line: `sail check`, `sail requirements`, `sail demo` (also `python -m sail`). Exit codes 0 pass, 1 gated finding, 2 usage error, 3 nothing testable; `--fail-on {leakage,any,never}`.
- New `LeakageFinding.kind` (`"leakage"` or `"diagnostic"`) and `LeakageFinding.inconclusive`. Persistence dominance is a diagnostic and no longer counts as a leakage finding in `LeakageReport.leakage_flagged` / `exit_code()`. `flagged` is unchanged for existing callers.
- fix: a check that cannot test anything is now reported as inconclusive instead of "not flagged": reconstruction with no complete row, timing with no testable row, temporal overlap with no complete row, construction with no treatment-active rows or no signal variation within any treatment level.
- fix: reconstruction and temporal-overlap exclude rows with missing values and report `evidence["n_missing"]` (a single NaN row used to make reconstruction report "not recoverable, error 0").
- New `treatment_bins` option for the construction check, for continuous doses (previously every dose value was its own group, so nothing could be tested and the result read as clean).
- `PersistenceDominanceDetector` validates its inputs (AUROCs between 0 and 1, non-negative margin). `sail.check` raises `ValueError` on an empty table.
- `LeakageReport.to_json()` now includes `schema_version`, `sail_version`, `generated_at`, an `input` block (shape, columns, SHA-256 of the rows) and a `result` block.
- Package README: states that a bare table cannot run any check, adds a non-SOFA example and a command-line section.

## 0.1.6

- `sail.check`: the signature note now lives in the function docstring (it used to be in the module docstring, with the package and function docstrings pointing at each other).
- `sail.check`: docstring states up front that `state_cols`/`action_col` only name columns and no detector reads them.
- `sail.check`: `UserWarning` when `timestamp_col` and `action_start_col` are the same column (the timing check cannot fail); the finding also carries a caution and `evidence["same_column"]`.
- New `sail.requirements()`; every "NOT RUN" reason (all five checks) ends with a "To enable:" hint showing the exact parameters to pass, and `report.summary()` ends with a "TO RUN MORE CHECKS" pointer. A plain CSV still cannot run the detectors without those inputs.
- fix: timing-violation check counted rows with a missing action start or state window end (NaN) as "no violation" and included them in `n_rows`. Such rows are now excluded from `n_violations` and `n_rows`, reported as `evidence["n_missing"]`, and mentioned in the explanation; if no row can be tested, the finding says so instead of reporting a clean result. Example: with 4 rows of which 2 have no action time and 1 violates, 0.1.5 reported "1 of 4 row(s)"; 0.1.6 reports "1 of 2 row(s)" and 2 excluded.
- Package README: the H3 test is reported as run (pinned run, Delta 0.147, 95% CI 0.140 to 0.154, Prediction A) instead of "not-yet-run".

## 0.1.5

- fix: `sail.check(action_col=None)`

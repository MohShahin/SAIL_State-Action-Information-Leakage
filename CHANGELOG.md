# Changelog

This file starts at 0.1.5. Earlier releases (0.1.0-0.1.4) aren't backfilled here -- see the git
tags and commit history for their changes.

## 0.1.6

- `sail.check`: the signature note now lives in the function docstring (it used to be in the module docstring, with the package and function docstrings pointing at each other).
- `sail.check`: docstring states up front that `state_cols`/`action_col` only name columns and no detector reads them.
- `sail.check`: `UserWarning` when `timestamp_col` and `action_start_col` are the same column (the timing check cannot fail); the finding also carries a caution and `evidence["same_column"]`.
- New `sail.requirements()`; every "NOT RUN" reason (all five checks) ends with a "To enable:" hint showing the exact parameters to pass, and `report.summary()` ends with a "TO RUN MORE CHECKS" pointer. A plain CSV still cannot run the detectors without those inputs.
- fix: timing-violation check counted rows with a missing action start or state window end (NaN) as "no violation" and included them in `n_rows`. Such rows are now excluded from `n_violations` and `n_rows`, reported as `evidence["n_missing"]`, and mentioned in the explanation; if no row can be tested, the finding says so instead of reporting a clean result. Example: with 4 rows of which 2 have no action time and 1 violates, 0.1.5 reported "1 of 4 row(s)"; 0.1.6 reports "1 of 2 row(s)" and 2 excluded.
- Package README: the H3 test is reported as run (pinned run, Delta 0.147, 95% CI 0.140 to 0.154, Prediction A) instead of "not-yet-run".

## 0.1.5

- fix: `sail.check(action_col=None)`

# Changelog

This file starts at 0.1.5. Earlier releases (0.1.0-0.1.4) aren't backfilled here -- see the git
tags and commit history for their changes.

## 0.1.6

- `sail.check`: the signature note now lives in the function docstring (it used to be in the module docstring, with the package and function docstrings pointing at each other).
- `sail.check`: docstring states up front that `state_cols`/`action_col` only name columns and no detector reads them.
- `sail.check`: `UserWarning` when `timestamp_col` and `action_start_col` are the same column (the timing check cannot fail); the finding also carries a caution and `evidence["same_column"]`.
- New `sail.requirements()`; "NOT RUN" reasons for construction/reconstruction show the exact spec to pass, and `report.summary()` ends with a "TO RUN MORE CHECKS" pointer. A plain CSV still cannot run the detectors without those inputs.

## 0.1.5

- fix: `sail.check(action_col=None)`

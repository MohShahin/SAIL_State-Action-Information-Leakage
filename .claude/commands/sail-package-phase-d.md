---
description: Phase D — CI workflow for the sail package, verified by deliberately breaking something and confirming CI actually catches it, plus a real check of the unverified Python 3.9 claim
---

# SAIL package, Phase D — CI

**The standing rule for this phase specifically:** a CI workflow that's never been watched failing
is not verified — it's assumed. Every step here that claims something works must be demonstrated,
the same way every detector's negative case was tested, not just its positive one.

## Step 1 — Read existing conventions first

Read `.github/workflows/deploy.yml` (the site's existing workflow) to match this project's
established style (trigger conventions, job naming, any shared patterns) before writing a new one.

## Step 2 — Build the workflow

Create `.github/workflows/test.yml`:
- Triggers: `push` to `main`, and `pull_request` — tests should run before code lands, not just
  after.
- **Matrix across Python 3.9 and 3.12** (or whatever the latest stable is) — this is the first
  actual check of the "Python 3.9+ compatible" claim already sitting in `pyproject.toml`, never
  verified anywhere in this project so far.
- Steps: install the package with test dependencies, run the full `pytest` suite, then separately
  run `python -m build` and `twine check dist/*` — packaging correctness should be checked on every
  push, not just remembered to be checked manually before a release the way Phase C2 did.

## Step 3 — Check whether the 3.9 claim is actually true

Before assuming the matrix will just pass: scan `sail/`'s source for any syntax that requires a
newer Python than 3.9 — most likely candidate is `X | Y` union type hints (PEP 604, requires 3.10+)
used in place of `Optional[X]`/`Union[X, Y]`. If any exist, fix them for 3.9 compatibility rather
than quietly lowering the stated minimum version — the claim was already public in the README and
on PyPI as of v0.1.0, so changing it now would mean an accuracy correction, not a preference.

**Report what you find here before the matrix run, not after** — if the 3.9 job fails, we want to
know it's a real, previously-unknown compatibility gap, not a surprise discovered only by reading
CI's red X after the fact.

## Step 4 — Push and confirm the workflow runs green on working code

Commit and push `test.yml` to `main`. Confirm both matrix jobs (3.9 and 3.12) complete and pass —
report the actual run URL/status, not just "should work."

## Step 5 — The real test: deliberately break something and confirm CI catches it

This is the step that actually verifies the safety net, not just its existence.

1. Create a throwaway branch (not `main`) — e.g. `ci-verification-do-not-merge`.
2. On that branch, introduce one deliberate, obvious failure — the simplest is inverting an
   assertion in one existing test (e.g. flip `assert result.flagged is True` to
   `assert result.flagged is False` in one of the already-passing Theorem-1 tests) so it's certain
   to fail for a reason unrelated to any real bug.
3. Push the branch and open a pull request (or just push and check the workflow run directly if a
   PR isn't necessary for this) — confirm the CI run for that branch actually shows **red/failed**,
   and that the failure message correctly identifies the specific test that broke.
4. **This is the actual verification — do not skip it even though it feels like extra work.** A CI
   config that's never been seen to fail is exactly as unverified as a detector that's never been
   tested on a negative case.
5. Delete the throwaway branch (and close the PR without merging, if one was opened) once the
   failure is confirmed. Nothing from this step should reach `main`.

## Step 6 — Add the PyPI badge to the README, now that it's factually accurate to do so

Since v0.1.0 is genuinely published, add a PyPI version badge to `SAIL_PACKAGE_README.md` (and a
CI-status badge once Step 4 confirms the workflow's badge URL). This was correctly deferred as
"stretch" before publish — it's a two-line addition, not a redesign, worth doing now that it's true.

## Reporting

Report Step 3's findings (any 3.9-incompatible syntax found and fixed) before the matrix run.
Report Step 4's actual green run. **Report Step 5's actual red run explicitly, with the failing
test's name and error message shown** — this is the one piece of evidence that actually matters in
this whole phase, more than the green run does.

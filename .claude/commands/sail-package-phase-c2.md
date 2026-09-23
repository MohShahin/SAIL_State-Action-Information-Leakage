---
description: Phase C2 — publish sail-leakage, via a mandatory TestPyPI dry run before any real, irreversible PyPI upload
---

# SAIL package, Phase C2 — publish

**This is the one phase in this whole project where a mistake can't simply be reverted.** A bad
`git push` gets fixed with another commit. A bad PyPI release burns that version number forever —
even yanking it doesn't free the number for reuse. Treat every step here accordingly: verify before
each irreversible action, never combine "build" and "the real upload" into one command run without
a checkpoint between them.

## Step 1 — Account and credentials check (report before proceeding)

1. Confirm a PyPI account exists for publishing under, and that an API token is available (PyPI
   requires token-based auth now, not username/password) — report what's actually available rather
   than assuming.
2. Confirm a **separate** TestPyPI account/token exists (test.pypi.org is a genuinely separate
   registry with its own accounts — do not assume the real PyPI token works there).
3. Do not store either token in any file that could be committed — use environment variables or an
   interactive prompt, and confirm neither ends up in `.git` history, even in an ignored file that
   could later be un-ignored by mistake.

## Step 2 — Final pre-publish verification (re-run, don't trust prior runs)

Given how much has changed since the wheel was last built and tested:
1. Clean rebuild from scratch: `rm -rf dist/ build/ *.egg-info`, then `python -m build`.
2. Full test suite one more time.
3. `twine check dist/*` — must pass cleanly.
4. Re-extract and re-run the README's exact Quickstart code block against a **fresh** venv
   installing from the freshly-built wheel — same discipline as the last verification pass, run
   again now because "verified once" isn't the same guarantee as "verified against what's about to
   actually ship."

## Step 3 — TestPyPI upload (the dry run)

```bash
twine upload --repository testpypi dist/*
```

After upload: **install from TestPyPI into a genuinely fresh venv** —
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ sail-leakage
```
(the `--extra-index-url` is necessary because TestPyPI doesn't mirror dependencies like `pandas`/
`numpy` — without it, the install will fail for the wrong reason and look like a packaging bug when
it isn't one).

Run the README's Quickstart against this install. Confirm the package page renders correctly on
`test.pypi.org` — specifically confirm the README's Markdown actually renders as formatted text,
not raw Markdown source, since this is the one thing that can't be checked by `twine check` alone.

**Stop here and report the TestPyPI package page URL for review before Step 4.**

## Step 4 — Real PyPI publish (only after explicit go-ahead on Step 3's results)

```bash
twine upload dist/*
```

Immediately after: install from the real PyPI into a fresh venv (`pip install sail-leakage`,
no index overrides this time) and re-run the Quickstart one final time. This is the last
opportunity to catch a problem before other people start depending on this version number.

## Step 5 — Tie the release to the repo

1. Tag the release in git (`git tag v0.1.0`, pushed) so the exact commit that produced this
   published version is unambiguous later.
2. Update the README's install instructions if they still say "if not live yet, use git+https" —
   that hedge is no longer accurate once this step completes and should be removed, not left as
   stale caution.
3. Confirm the PyPI project page's listed links (Homepage, Repository, per the METADATA already
   verified) actually resolve.

## Reporting

Report Step 1's findings before doing anything with credentials. Report Step 3's TestPyPI results
and stop — do not proceed to Step 4 without an explicit go-ahead on what Step 3 produced.

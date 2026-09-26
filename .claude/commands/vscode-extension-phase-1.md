---
description: VS Code extension Phase 1 — verify the Jupyter kernel-execution API actually works as needed before building anything on top of it, then the full check-and-render loop
---

# SAIL for VS Code, Phase 1

**The standing rule for this phase specifically:** this is the first piece of this whole project
built on an external API (the `ms-toolsai.jupyter` extension's interface) that hasn't been directly
verified in this session. Do not write UI or orchestration code assuming a specific API shape from
memory or documentation alone — confirm it against a real running instance first, exactly the way
every Python detector was proven against real data before being trusted.

## Step 0 — Research and prove the actual Jupyter API before writing anything else

1. Find `ms-toolsai.jupyter`'s current published API surface for third-party extensions — its
   GitHub repo publishes a TypeScript API definition for exactly this purpose. Read the actual,
   current type definitions, not recalled documentation.
2. Specifically confirm these three things are genuinely possible, and how:
   - Getting a reference to the currently active kernel for the notebook the user has open.
   - Executing a string of Python code **silently** (not inserting a visible cell) and capturing
     its stdout output back in the extension.
   - Listing variables currently defined in that kernel, and their types — needed to let the user
     pick their dataframe from a real list rather than typing a name.
3. Build the smallest possible scaffold needed to test this for real: a minimal extension that
   registers one command, depends on `ms-toolsai.jupyter` via `extensionDependencies` in
   `package.json`, and does nothing but attempt the three things above.
4. **Run this in a real VS Code Extension Development Host window, with a real Jupyter notebook
   open, with a simple dataframe created in a cell** (`import pandas as pd; df =
   pd.DataFrame({'a': [1,2,3]})`). Confirm the extension can detect the kernel, execute
   `print(1+1)` silently and capture `"2"` back, and list `df` as an available variable with its
   columns.

**If any of the three capabilities in step 2 don't work as hoped, stop and report exactly what's
actually possible instead of forcing a worse workaround silently.** A plausible fallback worth
naming explicitly if silent execution turns out to be unavailable: writing the check code to a
temp file and asking the user to run one cell themselves — a real, working, but less seamless
degradation, not a failure. Report this as a design decision needed, not something to route around
quietly.

## Step 1 — Full scaffold

Once Step 0 confirms the approach works, build out the structure from
`docs/VSCODE_EXTENSION_PLAN.md`: `extension.ts`, `jupyter.ts` (the confirmed-working wrapper from
Step 0, cleaned up), `checkCommand.ts`, `resultsPanel.ts`.

## Step 2 — The role-assignment form

Using the real column list retrieved via Step 0's confirmed method, build a form (a VS Code
QuickPick/multi-step input, or a simple WebView form — your call on which fits VS Code's UI
conventions better, state which and why) letting the user assign real columns to `state_cols`,
`action_col`, `treatment_col`, `window_col`, `timestamp_col` roles. No free-text column name entry
anywhere in this flow.

## Step 3 — Dependency check

Before attempting to run a check, silently execute `import sail` in the target kernel. If it fails,
offer to run `pip install sail-leakage` in that same kernel's environment, with the user's
confirmation — do not silently install anything without asking first.

## Step 4 — Execute the real check and render results

Construct the `sail.check(...)` call using the role assignments from Step 2, execute it silently,
capture and parse the JSON output. Render in a WebView panel, grouped flagged / not flagged / not
run — matching `LeakageReport.summary()`'s own grouping exactly, not a redesigned taxonomy for the
UI.

## Step 5 — End-to-end verification with the project's own known fixture

In a real Extension Development Host with a real kernel with the real, published `sail-leakage`
installed (not a local dev copy — the actual PyPI package, to test what a real user would
experience):

1. Construct Theorem 1's own dopamine=6 fixture — the same worked example every other phase of this
   project has tested against — as a dataframe in the kernel.
2. Run the full command flow through the extension's actual UI, not a script bypassing it.
3. Confirm the WebView correctly shows `construction_leakage_1a` flagged, with the same explanation
   text the Python package's own tests already verify.
4. Also run a clean/negative case in the same session and confirm it correctly shows "not flagged."

## Reporting

Report Step 0's findings in full before anything else — this determines whether the rest of this
plan is buildable as designed or needs to change. Report Step 5's end-to-end result with the actual
WebView output shown, not just "it worked."

# SAIL for VS Code — Architecture Plan (Tier 1)

## What this is, precisely

An extension that runs the existing, already-proven `sail-leakage` package against a dataframe
already sitting in a live Jupyter kernel the user has open in VS Code, and surfaces the real report
inline — not a new detection engine, a new *delivery mechanism* for the one that already exists and
is already tested. Tier 2 (live-as-you-type heuristic scanning) is explicitly out of scope here,
tracked as future work in `ROADMAP.md`, not silently implied by anything built in this phase.

## How it actually gets the dataframe

VS Code's official Jupyter extension (`ms-toolsai.jupyter`) exposes an API other extensions can
depend on, including the ability to execute code silently in the currently active kernel and
capture the result. This extension depends on that API rather than reimplementing kernel
communication — the same mechanism VS Code's own Variables panel already uses to inspect kernel
state.

**Flow:**
1. User runs `SAIL: Check DataFrame for Leakage` (command palette, or a button surfaced near an
   active notebook).
2. Extension queries the kernel for available variable names and their types (reusing the Jupyter
   extension's own variable-inspection call), so the user picks their dataframe from a real list
   rather than typing a name blind.
3. Extension inspects the dataframe's actual columns (another silent kernel call) and presents them
   in a form so the user assigns roles (`state_cols`, `action_col`, `treatment_col`, etc.) by
   picking from real column names — not free-text entry prone to typos.
4. Extension checks whether `sail-leakage` is importable in that kernel's environment. If not,
   offers to `pip install sail-leakage` into it directly, rather than failing silently or assuming
   it's present — the same "check before assuming" discipline used for every dependency check in
   this project so far.
5. Constructs and silently executes:
   ```python
   import json, sail
   _sail_result = sail.check(df, state_cols=[...], action_col=..., ...)
   print(json.dumps(_sail_result.to_json()))
   ```
   captures the output, parses it.
6. Renders results in a VS Code WebView panel — one section per category, clearly separated into
   flagged / not flagged / not run, matching `LeakageReport.summary()`'s own grouping, not a
   different taxonomy invented for the UI.

## Project structure

```
sail-vscode/
  src/
    extension.ts          # activation, command registration
    jupyter.ts             # wraps the Jupyter extension API: list variables, get columns, execute
    checkCommand.ts         # the role-assignment form + orchestration
    resultsPanel.ts         # WebView rendering
  package.json             # extension manifest (VS Code Marketplace metadata)
  README.md                # extension-specific, not the Python package's README
```

## Explicitly deferred to a later phase, not this one

- **LLM-assisted fix suggestions** — the three-tier privacy design (aggregate metadata always
  eligible, code snippets requiring separate opt-in and pre-send preview, raw data values never
  transmissible) is already specified and ready for when this phase is built, but no network-call
  code, consent UI, or API-key storage should appear in this phase at all. Mixing it in now would
  make Tier 1's actual core value — a working, verified, fully local check-in-editor loop — harder
  to test in isolation.
- **Tier 2 static/heuristic scanning** — a different and weaker kind of check by nature; building
  it alongside Tier 1 risks blurring the line this project has held everywhere else between proven
  results and heuristic hints.
- **File-based (non-Jupyter) dataframe access** — a natural, low-cost future addition once Tier 1's
  Jupyter path is solid, not part of this build.

## Marketplace publishing — start this in parallel, don't wait

Publishing requires an Azure DevOps organization and a VS Code Marketplace publisher identity, each
needing account creation and a personal access token — the same category of external, human-only
setup PyPI required. Worth starting now:
1. Create an Azure DevOps organization (free): https://dev.azure.com
2. Create a Marketplace publisher: https://marketplace.visualstudio.com/manage
3. Generate a PAT scoped to Marketplace (Manage) — store it the same way the PyPI tokens were
   handled: outside any file Claude Code writes or reads, via VS Code's own secure mechanism for
   the `vsce` publishing tool, not pasted into any command.

## Phase 1 scope (what actually gets built and verified now)

The full flow above, end to end, tested against a real VS Code instance with a real Jupyter kernel
running the real, published `sail-leakage` package — not a mock. Verification must include actually
watching it correctly flag a known case (reuse Theorem 1's dopamine=6 example, the same fixture
every other phase of this project has tested against) inside a real running extension, not just
unit-testing the TypeScript in isolation.

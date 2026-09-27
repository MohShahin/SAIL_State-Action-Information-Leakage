# SAIL for VS Code

Check a treatment dataset for state-action information leakage, with plain-language results. Everything
runs on your computer: your patient data is never uploaded.

> **Status: in development (Phase 2 of 6).** The panel, status bar, menus and Get Started page exist but
> are static. Choosing a dataset and running the checks arrives in Phase 3.

![The SAIL panel in a dark and a light theme](docs/screenshots/panel-dark-and-light.png)

## What is in it

* **SAIL panel** (sail icon in the activity bar): the dataset, the five checks and the privacy note, drawn
  with your theme's colors and fonts. A loading skeleton shows until the panel has its content
  ([screenshot](docs/screenshots/loading-skeleton-dark.png)).
* **Status bar**: the sail icon and *SAIL: Ready*. Click it to open the panel.
* **Editor title bar**: a sail button next to the split-editor button, and **SAIL: Check a dataset** in the
  Command Palette (Ctrl+Shift+P).
* **Get Started walkthrough** (Command Palette: *SAIL: Get Started*): choose data, confirm columns, read
  the report ([screenshot](docs/screenshots/walkthrough-dark.png)).
* **Move it to the right**: drag the sail icon to the right-hand side of the window, or run *SAIL: Move to
  Secondary Side Bar* and choose *Leakage Checks*, then *New Secondary Side Bar Entry*
  ([screenshot](docs/screenshots/secondary-sidebar-light.png)).

## Try it (development)

1. In VS Code choose **File → Open Folder…** and open this `extension` folder.
2. Run `npm install` once in a terminal there.
3. Press **Ctrl+F5** (*Run Without Debugging*). A window titled *[Extension Development Host]* opens with only
   SAIL loaded. Click the sail icon in its activity bar.

**If plain F5 says "Extension host did not start in 10 seconds"**, that is not SAIL. F5 attaches a
debugger to the new window, and on machines where `localhost` resolves to IPv6 (`::1`) the debugger's
connection is refused, so the window waits for a debugger that never attaches. Use **Ctrl+F5**, or run the
task **SAIL: open test window (no debugger)** (*Terminal → Run Task*). Both skip the debugger. To confirm the
cause on your machine, open *Help → Toggle Developer Tools* in the main window and look for
`ECONNREFUSED ::1`.

## Build and test

| Command | What it does |
|---|---|
| `npm run bundle` | Bundle `src/extension.ts` into one file, `dist/extension.js` (about 0.3 s). This is what F5 runs first. |
| `npm run typecheck` | Type-check without emitting (about 5 s). |
| `npm run build` | Type-check, then bundle. |
| `npm run build:icons` | Rebuild the icon font `media/sail-icons.woff` from `media/icons/*.svg`. |
| `npm test` | Start a real VS Code with a throwaway profile and run the integration tests. Set `VSCODE_EXE` to an installed `Code.exe` to avoid a download. |

## Repository rules

* Fixtures and screenshots use synthetic data only, never real patient data.
* The repository's pre-commit hooks must pass (`python -m pre_commit run --all-files`).

# SAIL for VS Code

Check a treatment dataset for state-action information leakage, with plain-language results. Everything
runs on your computer: your patient data is never uploaded.

> **Status: in development (Phase 2 of 6).** The sidebar and status bar exist but are static. Choosing a
> dataset and running the checks arrives in Phase 3. Design and phases: see the project's design canvas.

## Try it (development)

1. In VS Code choose **File → Open Folder…** and open this `extension` folder.
2. Run `npm install` once in a terminal there (installs the TypeScript compiler and test tools).
3. Press **F5**. A second window titled *[Extension Development Host]* opens.
4. In that window, click the **sail icon** in the activity bar (below the Extensions icon).

You should see the **SAIL: Leakage Checks** panel and, at the right of the status bar, **SAIL: Ready**.
Switch themes with **Ctrl+K Ctrl+T** to see it follow light and dark.

## Tests

```
npm test
```

Starts a real VS Code with a throwaway profile, loads the extension, and checks that it activates,
that the SAIL container and the *Leakage Checks* view are contributed, that the command opens the
sidebar, and that the status bar reads "SAIL: Ready". Set `VSCODE_EXE` to the path of an installed
`Code.exe` to use it instead of downloading one.

## Repository rules

* Fixtures and screenshots use synthetic data only, never real patient data.
* The repository's pre-commit hooks must pass (`python -m pre_commit run --all-files`).

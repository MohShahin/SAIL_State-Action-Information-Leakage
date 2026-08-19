---
description: Real-browser verification pass for the SAIL site's interactive components
---

# Verify site interactivity

Four specific checks are outstanding, none of them ever confirmed in a real browser — prior
verification in this project used jsdom, which executes JavaScript but does **not** apply real CSS
layout or media queries. That means claims like "the mobile bottom sheet works" were never actually
checked visually, only that the right DOM classes toggled. This command exists to close that gap
properly, using an actual browser engine.

## Setup

```
cd "c:\Users\MEPI\Desktop\Leakage\sofa-leakage-audit-site"
rm -rf node_modules _site
npm ci
npm run build
npx playwright install chromium --with-deps
```

If `npx playwright install` fails (no network access, permission issue, etc.), stop and report the
exact error — do not fall back to jsdom for the checks below and call it equivalent. A jsdom-only
result must be reported as "JS logic verified, visual rendering not verified," never as a full pass.

Serve the built site locally at the real subpath structure, matching how it's actually deployed:

```
mkdir -p /tmp/pages_check/SAIL_State-Action-Information-Leakage
cp -r _site/* /tmp/pages_check/SAIL_State-Action-Information-Leakage/
cd /tmp/pages_check && python -m http.server 8940 &
```
(run the server in the background, then continue in the same or a new shell)

## The four checks

Write a single Playwright script (Node, `chromium.launch()`) that performs all four and prints a
clear PASS/FAIL line for each, plus saves a screenshot for any check involving visual layout.

**1. Proof page derivation panel (desktop)**
- Navigate to `http://localhost:8940/SAIL_State-Action-Information-Leakage/proof/`
- Click the "Show derivation →" button under Theorem 1
- Assert `#derivPanel` has class `open` AND assert its bounding box is actually visible on screen
  (`right` CSS property resolves to `0px`, not just the class being present)
- Assert the panel's rendered text contains "Step 1"
- Click the close button; assert the panel is no longer visible
- Screenshot the open state to `screenshots/proof-panel-desktop.png`

**2. Proof page derivation panel (mobile viewport)**
- Set viewport to 390×844 (iPhone-ish)
- Reload `/proof/`, click the same "Show derivation →" button
- Assert the panel renders as a **bottom sheet**: check that its computed `bottom` CSS value is
  `0px` and that it spans close to the full viewport width (not the 440px desktop drawer width)
- Screenshot to `screenshots/proof-panel-mobile.png` — this is the check most worth a human's own
  eyes afterward, since "looks right" is ultimately a visual judgment call

**3. Live mechanism visualizer**
- Navigate to `/visualizer/`
- Read the initial gauge value and state-vector chip colors
- Click the vasopressor toggle, then set dose to a value >5 (e.g. drag/set the slider to 8)
- Assert the `sofa_cardio` chip's class changes to indicate contamination, assert the DAG's
  `#e-aprev-cardio` edge opacity increases, assert the gauge value actually changes from its
  initial reading
- Screenshot before/after to `screenshots/visualizer-toggle.png`

**4. Reproducibility page file-viewer**
- Navigate to `/reproducibility/`
- For each of the 5 tabs: click it, wait for the fetch to resolve, assert the displayed filename
  matches the tab and the code panel's text is non-empty and different from the previous tab's
  content
- Assert no tab shows the error state (`.fv-status` containing "Couldn't load")

## Reporting

For each of the four checks, report exactly one of:
- **PASS** — visually confirmed via screenshot review, not just assertion success
- **FAIL** — with the specific assertion that failed and the actual vs. expected value
- **COULD NOT VERIFY** — if Playwright setup failed; state this explicitly rather than substituting
  a weaker check and calling it equivalent

Do not mark anything as verified based on code review alone. If a check fails, stop and report
before attempting a fix — diagnosis first, same as every other bug in this project.

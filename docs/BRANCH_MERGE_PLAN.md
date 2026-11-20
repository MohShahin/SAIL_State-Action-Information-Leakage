# Branch merge plan

Analysis only. Nothing here has been merged. Snapshot taken 2026-11-09 against `origin/main` at
`37de767`. The project lead (@MohShahin) merges. Every open PR already requests review from
@MohShahin, and there is no CODEOWNERS file. The "Reviewer" column below is a proposal: it adds a
second reader where the content calls for one, named by role because the repo does not assign
these roles to people.

## How this was checked

- Ahead/behind: `git rev-list --left-right --count origin/main...origin/<branch>`.
- Contains h3-paired-bootstrap: `git merge-base --is-ancestor origin/h3-paired-bootstrap origin/<branch>`.
- Conflicts with main: the local Git is 2.35, which has no `git merge-tree --write-tree` (needs 2.38+).
  The three-way form `git merge-tree $(git merge-base origin/main B) origin/main B` was used instead,
  counting conflict markers. No branch was merged.
- PR states: GitHub REST API, `GET /repos/.../pulls?state=all` (#2 to #9; there is no #1).

## Remote branches

| Branch | Behind / ahead of main | Contains h3-paired-bootstrap | Files changed vs main | Conflicts with main | PR |
|---|---|---|---|---|---|
| `h3-paired-bootstrap` | 9 / 21 | (is it) | 66 | none | #2 open -> main |
| `exp-decision6a` | 9 / 22 | yes (forks at tip `bb3d30a`) | 72 | none | **no PR** |
| `exp-scaler-within-fold` | 9 / 21 | no: forks at `177aa96`, lacks `bb3d30a` | 59 | none | #9 open -> h3-paired-bootstrap |
| `exp-persistence` | 9 / 23 | no: forks at `177aa96` | 61 | none | #4 open -> h3-paired-bootstrap |
| `exp-label-alignment` | 9 / 23 | no: forks at `177aa96` | 59 | none | #5 open -> h3-paired-bootstrap |
| `exp-paired-cis` | 9 / 24 | no: forks at `177aa96` | 60 | none | #6 open -> h3-paired-bootstrap |
| `exp-dose-decisions` | 9 / 25 | no: forks at `177aa96` | 60 | none | #7 open -> h3-paired-bootstrap |
| `exp-simulation` | 9 / 27 | no: forks at `177aa96` | 63 | none | #8 open -> h3-paired-bootstrap |
| `cohort-decision` | 9 / 0 | no | 0 | n/a | #3 merged |
| `decisions-h3-amendment` | 8 / 0 | no | 0 | n/a | none |
| `about-add-sebastian-cajas` | 11 / 1 | no | 2 | **yes**, `src/about.html` | none |
| `about-add-vincent-huang` | 11 / 1 | no | 2 | **yes**, `src/about.html` | none |
| `vscode-extension` | 38 / 9 | no | 61 | none (textual) | none |
| `release-0.1.6` | 0 / 1 | no | 7 | none | to be opened (package 0.1.6) |

"Does not contain h3-paired-bootstrap" for the exp-* branches means the branch was cut one commit
before the h3-paired-bootstrap tip: every exp branch except exp-decision6a lacks only `bb3d30a`
("Results: pinned run aggregates (13,192)"). Their other commits are the h3-paired-bootstrap
history plus their own 1 to 6 commits (`git cherry`).

Local-only branches (never pushed, 0 commits ahead of main, nothing to merge): `pre-verily-release`,
`release-0.1.5`, `site-h3-update`.

## Already contained in main (confirmed)

- `cohort-decision`: 0 commits ahead of main; merged via PR #3.
- `decisions-h3-amendment`: 0 commits ahead of main; every commit is in main.
- `about-add-sebastian-cajas`, `about-add-vincent-huang`: superseded rather than contained. Main's
  `37de767` adds both people to the Team grid itself (both names appear in `src/about.html` on
  main), and diffing either branch against main shows only lines main has that the branch lacks.
  Merging either would conflict and duplicate a card.

These four can be deleted once the project lead agrees. Nothing has been deleted.

## What each exp branch adds (own files only)

Every exp branch adds a `.gitignore` block, files under `results/exploratory/<topic>/` (README plus
aggregate JSON/CSV/PNG), a script in `scripts/`, and a test in `tests/`. No two branches touch the
same file except `.gitignore`.

| Branch | Topic folder | Own commits |
|---|---|---|
| exp-decision6a | `decision6a/` | 1 (`c70edbe`) |
| exp-scaler-within-fold | `scaler_within_fold/` | 1 (`5d03325`) |
| exp-persistence | `persistence/` | 2 |
| exp-label-alignment | `label_alignment/` | 2 |
| exp-paired-cis | `paired_cis/` | 3 |
| exp-dose-decisions | `dose_decisions/` | 4 |
| exp-simulation | `simulation/` | 6 |

## Proposed merge order

| # | Merge | Into | Reviewer (proposed) | Why this position |
|---|---|---|---|---|
| 1 | #2 `h3-paired-bootstrap` | main | Project lead (Decision 4 approval of the post-pin change `ff530e0` is a precondition, per the PR body) | Every exp branch is built on it |
| 2 | `exp-decision6a` (open PR first) | main | Project lead (it is the decision-6(a) H3 follow-up) | H3-related; already contains the full h3-paired-bootstrap |
| 3 | #9 `exp-scaler-within-fold` | main (retarget) | Project lead plus a statistics reader | H3 sensitivity; one commit |
| 4 | #4 `exp-persistence` | main (retarget) | Project lead | Persistence control feeds the H3 freeze checklist |
| 5 | #6 `exp-paired-cis` | main (retarget) | Statistics reader | Pure re-analysis of existing gaps |
| 6 | #5 `exp-label-alignment` | main (retarget) | Clinical reviewer | Label-definition claims |
| 7 | #7 `exp-dose-decisions` | main (retarget) | Clinical reviewer | Clinical label definitions (UP/DOWN/STOP) |
| 8 | #8 `exp-simulation` | main (retarget) | Statistics reader | Synthetic data only; largest, least coupled |
| 9 | `release-0.1.6` | main | Project lead | Independent of the above; can go any time |
| 10 | `vscode-extension` via a rebased copy | main | Project lead | 38 commits behind; see the Step 5 PR |

PRs #4 to #9 target `h3-paired-bootstrap`. After #2 merges, retarget each to `main` (GitHub does this
automatically only if the `h3-paired-bootstrap` branch is deleted on merge). After retargeting, each
diff shrinks to its own commits plus `bb3d30a`, which main will already have.

## Expected conflict: `.gitignore` allowlists

Each exp branch merges cleanly into main by itself. They conflict with each other: six of the seven
insert their block at the same place (after `!results/figures/cohort_flow.png`), and exp-decision6a
inserts at line 100. From the second exp merge onward, expect a `.gitignore` conflict every time.

**Do not resolve it by keeping both sides verbatim.** Every block starts with

```
!results/exploratory/
results/exploratory/*
```

`.gitignore` uses last-match-wins, so a repeated `results/exploratory/*` re-ignores every topic folder
allowlisted above it. Tested in a scratch repo: with two blocks kept verbatim, only the second
topic's files remain addable. Already-tracked files stay tracked, so this fails silently and only
shows up when a later rerun cannot add its updated JSON.

Correct resolution: keep the header once, then one block per topic:

```
# Exploratory analyses (not pre-registered; do not change the H3 decision), aggregates only
!results/exploratory/
results/exploratory/*
!results/exploratory/decision6a/
results/exploratory/decision6a/*
!results/exploratory/decision6a/README.md
...
!results/exploratory/persistence/
results/exploratory/persistence/*
!results/exploratory/persistence/README.md
...
```

Check after each merge: `git status --porcelain --ignored results/exploratory` should show no
`!!` entries for allowlisted files, and `git check-ignore -v results/exploratory/<topic>/README.md`
should print nothing for every topic.

## Open questions for the project lead

1. Approve `ff530e0` under Decision 4 (precondition for #2; all exp PRs depend on it).
2. Open a PR for `exp-decision6a` (the only exp branch without one), stacked on #2 like the others?
3. Delete `cohort-decision`, `decisions-h3-amendment` and both `about-add-*` branches?

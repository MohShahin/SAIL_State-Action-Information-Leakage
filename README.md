<div align="center">

# SAIL
### State‑Action Information Leakage in Sepsis Reinforcement Learning

**Does the severity score a clinical RL policy learns from already know what treatment it's about to recommend?**

[![License: MIT](https://img.shields.io/badge/license-MIT-7c1d2e.svg)](LICENSE)
[![Data: MIMIC-IV](https://img.shields.io/badge/data-MIMIC--IV%20v3.1-2f5d50.svg)](DATA_ACCESS.md)
[![Status: preliminary](https://img.shields.io/badge/status-preliminary%20audit-8a6d1f.svg)](status.html)
[![Live demo](https://img.shields.io/badge/demo-live-7c1d2e.svg)](https://mohshahin.github.io/State-Action-Information-Leakage-in-Sepsis-Reinforcement-Learning/)

**MIT Laboratory for Computational Physiology  ·  Boston University School of Public Health**

[**Live project site**](https://mohshahin.github.io/State-Action-Information-Leakage-in-Sepsis-Reinforcement-Learning/) — start here, no installation required

</div>

---

> **Status: preliminary, internal audit.** The manuscript in this repository is a draft prepared
> for conference presentation, not a peer-reviewed publication. Two independent re-extractions have
> confirmed the headline findings and corrected two of the original figures — see
> [Verified results](#verified-results) below and
> [`status.html`](https://mohshahin.github.io/State-Action-Information-Leakage-in-Sepsis-Reinforcement-Learning/status.html)
> for the full, unfiltered history.

## The question

Offline reinforcement learning for sepsis treatment — the "AI Clinician" (Komorowski et al., 2018)
and its descendants — learns a policy by fitting **state → action** from retrospective ICU
trajectories. The state is built substantially from the **SOFA organ-dysfunction score**. SAIL asks
a narrow, falsifiable question: does that state already encode the treatment action it's supposed
to *precede*, undermining the premise the whole framework rests on?

We find two provable mechanisms by which it can, and one open question about how much it actually
matters in practice — see [`FORMAL_ANALYSIS.md`](FORMAL_ANALYSIS.md) for the proofs, or the
[interactive proof page](https://mohshahin.github.io/State-Action-Information-Leakage-in-Sepsis-Reinforcement-Learning/proof.html)
for the illustrated version.

| | Claim | Status |
|---|---|---|
| **H1** | The SOFA cardiovascular subscore's own definition encodes treatment, not just physiology (treatment-confounded severity construction) | **Proven** |
| **H2** | Temporal aggregation windows overlap prior treatment periods (treatment overlap) | **Proven** |
| **H3** | The resulting predictability gap reflects these mechanisms specifically, not just treatment persistence | **Open — under test** |

*Terminology note:* H1/H2 were previously described as "leakage." They're actually ordinary
`A_(t-1) → S_t → A_t` treatment-history structure, not `A_t → S_t → Â_t` (a state containing
information about the *same* action epoch it predicts) — a real distinction a reviewer raised. See
[`FORMAL_ANALYSIS.md`](FORMAL_ANALYSIS.md) §1.1 for the precise correction; this project's own
action labels were verified to have zero such overlap.

## Explore the project

This repository is also a live, five-page site — not just code and a PDF.

| | |
|---|---|
| **[Project hub](https://mohshahin.github.io/State-Action-Information-Leakage-in-Sepsis-Reinforcement-Learning/)** | Overview and entry point to everything below |
| **[Interactive walkthrough](https://mohshahin.github.io/State-Action-Information-Leakage-in-Sepsis-Reinforcement-Learning/demo.html)** | Six-step, plain-language guide — try the live SOFA calculator yourself |
| **[Live mechanism visualizer](https://mohshahin.github.io/State-Action-Information-Leakage-in-Sepsis-Reinforcement-Learning/visualizer.html)** | Adjust one synthetic patient and watch the mechanism happen: the causal graph, the state vector, and the predictability gauge move together in real time |
| **[Formal proof](https://mohshahin.github.io/State-Action-Information-Leakage-in-Sepsis-Reinforcement-Learning/proof.html)** | The theorems, illustrated, with a pre-registered test for the one claim that isn't provable in closed form |
| **[Status & roadmap](https://mohshahin.github.io/State-Action-Information-Leakage-in-Sepsis-Reinforcement-Learning/status.html)** | What's confirmed, what's open, and the honest history of two bugs found and fixed |

## Verified results

Every figure below has been independently re-extracted from MIMIC-IV and reproduced across five or
more separate pipeline runs — not just computed once.

| Statistic | Manuscript draft | Verified | |
|---|---|---|---|
| Cohort size | 11,354 | 11,354 | exact match |
| Exp. 1 — dose-determined (4h window) | 30.5% | 32.3% | revised |
| Exp. 1 — dose-determined (24h window) | 26.3% | 28.6% | revised |
| Exp. 2 — AUROC, full state → no explicit treatment features | 0.900 → 0.791 | 0.900 → 0.791 | exact match |
| Exp. 2 — recoverability gap | ≈0.108 | 0.109 | essentially exact |
| Exp. 3 — mean window overlap (24h) | 56.1% | 31.1% | revised down |
| Exp. 3 — % of decision points >50% overlapping | 55.7% | 28.7% | revised down |

The Experiment 2 gap survived a **15× difference** in underlying row counts almost untouched —
evidence it's a real, ratio-based effect rather than an artifact of the extraction bugs that
inflated the raw counts. Full diagnostic trail, including how those bugs were found (one of them
confirmed by literally recovering the original buggy run from an earlier commit and reproducing
its exact numbers), is in [`ROADMAP.md`](ROADMAP.md).

## Repository structure

```
.
├── index.html, demo.html, visualizer.html,       # the live project site
│   proof.html, status.html, assets/
├── FORMAL_ANALYSIS.md          # theorems, proofs, causal DAG, pre-registered H3 test
├── ROADMAP.md                  # phased plan + full bug-fix / verification history
├── DATA_ACCESS.md              # MIMIC-IV governance — read before touching results/ or notebook/
├── paper/                      # manuscript draft (docx + pdf)
├── notebook/                   # full analysis pipeline (MIMIC-IV via BigQuery)
├── queries/                    # standalone BigQuery SQL — safe to publish; data output is not
├── results/                    # curated, aggregate-only result summaries (see results/README.md)
└── scripts/                    # environment setup check, crash-safe notebook execution driver
```

## Reproducing the analysis

**MIMIC-IV is credentialed-access data.** Read [`DATA_ACCESS.md`](DATA_ACCESS.md) before touching
`results/` or the notebook's own output directory — the queries in [`queries/`](queries/) are
public; their output is not.

```bash
bash scripts/check_setup.sh                    # verify BigQuery access, credentials, packages
python3 queries/render_query.py queries/01_cohort.sql \
  --scratch-dataset your-project.temp_dataset -o /tmp/01.sql
```

See [`queries/README.md`](queries/README.md) for the full extraction sequence, or open
[`notebook/`](notebook/) directly for the complete pipeline (cohort → extraction → SOFA
decomposition → Experiments 1–5).

## Citing this work

This is a preliminary, non-peer-reviewed working draft. See [`CITATION.cff`](CITATION.cff) for
machine-readable citation metadata.

```bibtex
@misc{sail2026,
  title  = {SAIL: State--Action Information Leakage in Sepsis Reinforcement Learning},
  author = {Shahin, Mohammad},
  year   = {2026},
  note   = {Preliminary working draft},
  url    = {https://github.com/MohShahin/State-Action-Information-Leakage-in-Sepsis-Reinforcement-Learning}
}
```

## License

Code (site, notebook, queries, scripts) is MIT-licensed — see [`LICENSE`](LICENSE). Manuscript text
and figures in `paper/` are not covered by that license; contact the authors before reuse.

---

<div align="center">
<sub>MIT Laboratory for Computational Physiology · Boston University School of Public Health</sub>
</div>

# SAIL as an Open-Source Library — Architecture & Roadmap to Oct 7

## The core advantage worth naming up front

This isn't a from-scratch package. Every category below is a generalization of something already
*proven*, not a new invention under deadline pressure — and every detector has a known-good test
case already sitting in this project's own verified results. That's the difference between "we
hope this works" and "we can prove this works," and it's worth leading with when this gets shown
to Verily.

---

## The taxonomy — five categories, each a generalization of a real, proven finding

**1. Construction leakage.** A state-derived variable is partly *defined* by a treatment/action
value, making it non-identifiable from the signal it claims to measure once treatment is active.
Two sub-types, both already proven as distinct shapes, not guessed at:
- **1a — full non-identifiability** (Theorem 1's shape): the variable becomes *constant* with
  respect to the true signal once treatment crosses into any active state.
- **1b — score-shift collision** (Proposition 3's shape): the variable still varies with the true
  signal, but the *same* true-signal value maps to different outputs depending on treatment status.

**2. Reconstruction leakage.** Removing a leaking feature doesn't remove the information, because
it's exactly or near-exactly recoverable from other retained features (Theorem 2 — the SOFA-total
identity). A detector here checks: is there a deterministic or near-deterministic relationship that
lets a dropped feature be rebuilt from what's left?

**3. Temporal / window-overlap leakage.** A feature's aggregation window overlaps a period when
treatment was already active, contaminating what's meant to be a clean pre-decision snapshot
(Proposition 1 — including the corrected non-monotonicity result, which matters: a naive detector
that assumes "wider window = worse" would itself be wrong).

**4. Timing-violation leakage.** The strict, reserved sense of "leakage" — the state's window
extends into or past the timestamp of the action being predicted. This is exactly Phase 0's
alignment check, generalized into a reusable, automatic test instead of a one-off manual
verification.

**5. Persistence-dominance flag.** Not leakage — a related, equally useful diagnostic this
project's own Variant F result motivates directly. Checks whether a model's predictive power on
treatment-derived features is matched or exceeded by a trivial "last action repeats" baseline. A
package that only checked categories 1–4 would miss exactly the finding that made this project's
own result sharper than expected.

---

## Package architecture

```
sail/
  __init__.py
  detectors/
    base.py              # LeakageCheck ABC: .run(df, spec) -> LeakageFinding
    construction.py       # Category 1 (both sub-types)
    reconstruction.py     # Category 2
    temporal_overlap.py   # Category 3
    timing_violation.py   # Category 4
    persistence.py        # Category 5
  report.py               # LeakageFinding / LeakageReport — human-readable + JSON
  specs/                  # worked examples as starting specs: sofa_cardio, sofa_resp
tests/                    # each detector tested against this project's own verified numbers
pyproject.toml
README.md
```

**API sketch:**
```python
import sail

report = sail.check(
    df,
    state_cols=[...],
    action_col="action_next",
    timestamp_col="decision_time",
    treatment_col="dose",       # optional, enables categories 1, 2, 5
    window_col="window_start",  # optional, enables category 3
)
report.summary()   # plain-language findings, category by category
report.to_json()
```

The package should not force every check to run — a user with no treatment column simply can't run
categories 1/2/5, and the report should say so plainly rather than error out or fake a result.

---

## Roadmap to Oct 7 — phased, with an honest line on what won't be fully mature

**Phase A (now):** Package scaffold, `pyproject.toml`, the two most rigorously-proven detectors —
construction leakage (1a/1b) and reconstruction leakage (2) — each ported directly from the
already-verified notebook functions (`sofa_cardio_decomposed`, the Theorem 2 identity check), with
real tests asserting against this project's own known numbers (e.g., dopamine=6 correctly flags
1a; the SOFA-total reconstruction correctly flags 2).

**Phase B:** Temporal-overlap (3), timing-violation (4), and persistence-dominance (5) detectors.
Then run the whole package end to end against the real SAIL cohort as a worked example —
dogfooding: the package should re-derive this project's own headline findings automatically. This
is the strongest possible demonstration for Verily — not a claim that it works, a live re-run
proving it does.

**Phase C:** `pip`-installable (PyPI, or at minimum `pip install git+...` if PyPI review timing is
tight), a proper root README in standard OSS style, and the website's homepage rebuilt around
install/quickstart rather than narrative research framing — with the existing proofs and evidence
preserved as a "Research" section for anyone who wants the depth, not deleted.

**Phase D — stretch, be honest about this if time runs out:** CI (tests running on every push),
a polished docs site beyond the quickstart, PyPI badge/versioning discipline. If Phase D doesn't
fully land by the 7th, the honest framing is "v0.1, actively developed" — which is a completely
normal and credible thing to tell a partner like Verily about a two-week-old package. Overclaiming
maturity here is a much bigger risk than admitting the scope.

---

## What's explicitly not being promised

No claim that this package catches every possible leakage pattern — the five categories are what
this project has actually proven exist, not an exhaustive taxonomy of all leakage. The README and
site should say so directly: this is a growing, evidence-based specification, not a finished
standard.

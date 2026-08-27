# SAIL Research Program: PhD-Level Redesign & PI Defense Preparation

**Prepared for:** PI/research-defense meeting, Friday
**Scope:** This document does the thinking and writing work needed *before* Friday. It does not
fabricate results, run experiments, or build the BU Showcase demo — those are separate, explicitly
scoped follow-ups (see §14 and the RED/YELLOW/GREEN breakdown in §9).

**A note on rigor, matching how the rest of this project has operated:** every claim below is
labeled by status. `[VERIFIED]` = already proven or measured in this repo. `[LITERATURE]` = a real,
checked citation. `[PROPOSED]` = a design for future work, not a result. `[HYPOTHETICAL]` = an
expected outcome, explicitly not yet observed. Nothing in this document invents a number.

---

## 0. Audit of current claims

| # | Claim | Status |
|---|---|---|
| 1 | SOFA cardiovascular score is non-identifiable from MAP alone once any vasopressor is active | `[VERIFIED]` — Theorem 1, proof.html, direct inspection of scoring rule |
| 2 | σ_cardio is exactly reconstructible from SOFA_total minus other subscores | `[VERIFIED]` — Theorem 2, algebraic identity |
| 3 | 32.3%/28.6% of eligible timesteps are dose-determined; 100% of treated timesteps are | `[VERIFIED]` — Experiment 1, reproduced 5+ times; the "100%" figure is itself now a proven corollary, not an observation |
| 4 | Window overlap exists and its fraction is non-monotonic in window length | `[VERIFIED]` — Proposition 1 + exact quotient-rule derivative |
| 5 | AUROC gap (0.900 → 0.791) between full-state and physiology-only variants | `[VERIFIED]` — Experiment 2, survived a 15× row-count bug largely unchanged |
| 6 | The AUROC gap reflects genuine, temporally-specific leakage rather than ordinary treatment persistence | **`[HYPOTHESIZED]`** — this is H3, explicitly open, not yet tested |
| 7 | State containing treatment information invalidates the learned policy in practice | **Not claimed anywhere in the current repo** — and it must not be, until Experiment 5+ and a policy-divergence study actually run |
| 8 | Two mechanisms (definitional, window-overlap) are the *complete* set of leakage mechanisms in sepsis-RL state construction | **`[OVERSTATED IF IMPLIED]`** — nothing in the repo claims completeness explicitly, but the two-mechanism framing risks reading that way to a reviewer. Should be stated as "two proven mechanisms we identified," not "the leakage mechanisms." |

**Missing for publication:** a completed H3 test (Experiment 5, pending compute), a policy-level
consequence study (does sanitization change the learned policy at all?), and — as of this audit —
an honest positioning against very recent, closely related work (§2 below).

**Missing for an MIT PhD-level contribution:** a mechanism-agnostic formalization (right now the
theorems are SOFA-specific; a general leakage functional applicable to *any* clinical state
construction is what elevates this from "an audit of one score" to "a methodology"), and empirical
evidence that leakage changes something a clinician would care about (a policy, not just an AUROC).

**What a skeptical reviewer would attack first, ranked by how damaging:**
1. "Isn't this just `Off by a Beat` (Tang et al., *npj Digital Medicine*, 2026) restated?" — see §2.
2. "You've shown information exists in the state. You haven't shown it *matters*." — this is H3 and
   the entire missing policy-consequence layer.
3. "SOFA is not the whole state in any real sepsis-RL pipeline — why should this generalize?"

---

## 1. Identity decision: what is SAIL, fundamentally?

Given the options (A: SOFA audit, B: sepsis-RL audit, C: general clinical-RL leakage detection
framework, D: causal methodology for treatment contamination in longitudinal states, E: leakage-aware
offline-RL benchmark, F: combination):

**Decision: primarily D, with C as the natural generalization path, and E as a credible
longer-horizon artifact — not A or B alone, and not E as the immediate identity.**

**Why not A or B alone:** "we found a problem in SOFA" is a bug report, not a thesis. It has a
ceiling — once the bug is described, there's nowhere left to go. A PI or reviewer will correctly
read a SOFA-only framing as incremental.

**Why D is the right center of gravity, not C or E yet:** The project's actual strength right now
is two *proofs* — a non-identifiability theorem and a reconstruction identity — plus a causal-graph
argument for why non-identifiability doesn't automatically imply leakage. That is causal
methodology: a way of *diagnosing* when a state construction has created a treatment-affected
covariate, grounded in an existing, well-established causal pathology (treatment-confounder
feedback / time-varying confounding — Robins' g-methods literature `[LITERATURE]`) applied to a
setting (RL state representations) where that diagnostic vocabulary is not yet standard practice.

**Why C (a general detection framework) is the honest near-term ambition, not the current
identity:** the project has exactly one instantiation (SOFA cardiovascular score) worked out to
proof-level rigor. Calling it a "framework" today, before a second mechanism or a second
state-construction has been run through the same diagnostic process, would be overclaiming. The
right move is to *state the general framework explicitly* (§4 below gives a first formal pass) and
*prove it concretely once* on SOFA — which is exactly what's already done — rather than claim
generality without demonstrating it a second time.

**Why E (a benchmark) is real but should be Phase 2 of the research program, not Friday's claim:**
a benchmark implies other researchers submit representations and get scored. That requires the
synthetic ground-truth environment (Experiment G) to exist first, so the benchmark's own scoring
function can be validated against known injected leakage. Right now that environment doesn't
exist. Claiming "benchmark" before it does is the single easiest thing for an MIT ML reviewer to
puncture.

**One-sentence identity statement for Friday:**

> SAIL is a causal-diagnostic methodology, proven on one concrete and clinically important
> instance (SOFA-based sepsis-RL states), for detecting when longitudinal clinical state
> constructions have become treatment-confounder-contaminated — with a designed (not yet run)
> empirical program to determine whether that contamination changes learned policies, and a
> designed (not yet built) path toward a general-purpose leakage-audit benchmark.

---

## 2. Positioning against the literature that actually exists

This section is the single most time-sensitive part of this document. All citations below were
checked directly (fetched or searched), not recalled from training data.

### 2.1 What already exists

- **Vincent et al. 1996** `[LITERATURE]` — defines the SOFA rule SAIL's Theorem 1 is a proof about.
- **Komorowski et al. 2018, "AI Clinician"** `[LITERATURE]` — the motivating sepsis-RL framework.
- **Gottesman et al. 2019, "Guidelines for RL in Healthcare"** (*Nat. Med.*) `[LITERATURE]` —
  field-level guidance on confounding and OPE pitfalls in clinical RL; general, not mechanism-specific.
- **Jeter et al. 2019** `[LITERATURE]` — an independent critique of the AI Clinician; Section 6.1
  documents a *different* temporal confound (within-bin MAP-crash/recovery masking a treatment
  event), mechanistically distinct from SAIL's window-overlap mechanism (cross-bin contamination
  from a *prior* period). Already correctly distinguished on the proof page.
- **Hernán & Robins, *Causal Inference: What If*, 2020** `[LITERATURE]` — general principle:
  conditioning on a variable affected by treatment.
- **Robins' g-methods literature** (Robins 1986/1987; the treatment-confounder-feedback / g-formula
  tradition) `[LITERATURE]` — the classical biostatistics answer to exactly the causal structure
  SAIL's mechanisms instantiate. **SAIL currently does not cite this tradition anywhere**, which is
  a gap: a causal-inference reviewer (Reviewer 2, §7) will ask why a 40-year-old, well-developed
  toolkit (g-computation, marginal structural models) for exactly this problem class isn't engaged
  with. This needs to be fixed before Friday at the level of an explicit paragraph, even without
  implementing g-methods computationally.

### 2.2 The two discoveries from this session that change the novelty framing

**Discovery 1 — "Conceptualizing Treatment Leakage in Text-Based Causal Inference"** (Daoud, Jerzak
& Johansson, NAACL 2022; extended in a 2026 preprint on distillation/sensitivity analysis)
`[LITERATURE, VERIFIED VIA SEARCH]`. This paper *names and formalizes* "treatment leakage" as a
general causal phenomenon: a representation (there, text used as a confounder proxy) that is
itself affected by treatment, inducing post-treatment/collider bias when conditioned on. **This is
the same causal pathology SAIL's Theorem 1 instantiates, already named, in a different
representation-learning setting (text, not longitudinal clinical state).**

*What this means for Friday:* SAIL cannot claim to have invented the concept of treatment leakage
into a representation. It can — correctly — claim to be the first (as far as this search found) to:
(a) formalize the *specific mechanism* by which it arises in a widely-used clinical severity score
via a provable non-identifiability theorem, rather than an empirically-observed correlation; and
(b) situate it inside the sequential-decision (RL, not single-timepoint ATE) setting, where the
consequence isn't a biased effect estimate but a potentially self-fulfilling policy.

**Discovery 2 — "Off by a Beat: The Effects of Temporal Misalignment in Reinforcement Learning for
Sepsis Treatment"** (Tang, Yao, Wiens & Parbhoo, *npj Digital Medicine*, May 2026) `[LITERATURE,
VERIFIED VIA FULL-TEXT FETCH]`. This is the paper most likely to come up in the room Friday if the
PI or anyone on the committee reads recent sepsis-RL literature — it is three months old, in a
high-visibility venue, explicitly uses the phrase "temporal information leakage," explicitly
studies MIMIC-based sepsis RL with SOFA, and cites the same foundational papers SAIL already cites
(Komorowski, Gottesman, Jeter).

**The mechanism is different, and this must be stated precisely, not gestured at:**

| | Off by a Beat | SAIL Mechanism 2 (window overlap) |
|---|---|---|
| What's misaligned | The **index** assigned to states vs. actions — action `a_t` should be indexed as following `s_t` and preceding `s_t+1`, but common practice aligns it contemporaneously with `s_t`, implying `a_t` was chosen using information from the future | The **content** of the state itself — a lookback window `[t-w, t)` used to build `s_t` overlaps a period when treatment was *already running before t*, contaminating what's meant to be a pre-decision snapshot |
| Root cause | A discretization/indexing convention applied uniformly across the whole pipeline | The interaction between window length `w` and per-patient treatment timing, which the paper proves is not simply monotonic |
| Fix proposed | Shift the action index back by one timestep | Not yet proposed as a fix in SAIL (Experiment D, sanitization, is designed but not run) |
| Evidence | Empirical: 44.7% of states show disagreeing optimal actions between aligned and misaligned versions, on real MIMIC-III policies, already trained | Formal: a proven, exact derivative characterizing when contamination fraction rises, plus a measured contamination rate |

These are **complementary, not competing** diagnoses of the same underlying problem class (temporal
structure in EHR data breaking causal assumptions required for valid RL). A defensible move for
Friday is not to distinguish SAIL from this paper defensively, but to **absorb it as directly
relevant related work and explicitly note that Off by a Beat's index-misalignment mechanism is a
third, distinct leakage mechanism SAIL's general framework (§4) should be able to describe** —
this is a strength if framed as "our formal apparatus generalizes to a mechanism we didn't
originally design it for," and a weakness only if SAIL is caught not knowing this paper exists.

**Action required before Friday:** add this citation to `papers.html` and `FORMAL_ANALYSIS.md`,
and rehearse the one-paragraph answer above — a PI question naming this paper is now a near-certainty
to prepare for, not a long-shot.

### 2.3 Novelty Defense

1. **Existing knowledge:** treatment leakage into a representation is a named causal phenomenon
   (Daoud et al.). Temporal misalignment in sepsis RL specifically is a documented, recent,
   high-visibility problem (Tang et al.). Time-varying confounding has a 40-year classical solution
   in biostatistics (Robins). Guidelines-level critique of clinical RL confounding exists
   (Gottesman et al.). A specific critique of the AI Clinician's OPE robustness exists (Jeter et al.).

2. **Missing knowledge:** none of the above provides a *mechanism-level, provable* account of how a
   specific, widely-used clinical scoring rule's *own definition* creates treatment-confounder
   feedback — as opposed to an indexing convention (Off by a Beat) or an empirically-detected
   correlation (Daoud et al.'s text setting). No existing work distinguishes, for a concrete
   clinical score, which part of the observed action-predictability is attributable to a provable
   definitional mechanism versus ordinary treatment persistence, nor proposes the paired-bootstrap
   test needed to tell them apart in this specific setting.

3. **SAIL's proposed contribution:** a causal-diagnostic method that (a) proves, rather than
   measures, that a specific scoring construction creates a definitional treatment-confounder
   pathway; (b) formally characterizes a second, distinct mechanism (window overlap) with an exact
   result correcting a naive monotonicity intuition; (c) provides a causal graph and falsifiable
   test distinguishing "state encodes treatment" from "state's encoding of treatment materially
   drives predicted actions" — a distinction the existing literature (including Off by a Beat)
   does not make this explicit about.

4. **Why technically nontrivial:** Theorem 1 required identifying that MAP appears in *zero*
   dose-branches of the actual scoring rule (not merely "above some threshold," which was the
   project's own earlier, weaker draft of the claim) — a fact that requires reading the exact
   nested conditional structure, not an approximation. Theorem 2's reconstruction identity and
   Proposition 1's exact quotient-rule derivative are genuine, checkable mathematics, not hand-waving.

5. **Why it matters beyond sepsis:** any clinical severity score constructed partly from treatment
   response (not just SOFA — e.g., components of APACHE II, qSOFA modifications, vasopressor-dependent
   shock indices) is a candidate for the same non-identifiability argument. The window-overlap
   mechanism applies to *any* fixed-window state aggregation in longitudinal EHR-based RL,
   independent of which score is used.

6. **Why another researcher could build on it:** the general leakage functional in §4 gives a
   template — define the state-construction function, identify which of its branches reference
   treatment-derived quantities directly, and the same non-identifiability proof strategy applies.

---

## 3. Reformed core research question and hypothesis

**Original question:** "Does the state representation used in offline sepsis reinforcement
learning already encode information about the treatment action it precedes, thereby undermining
the assumptions required for valid policy learning?"

**Assessment:** Not strong enough as a *terminal* question, because it can be fully answered "yes"
(as SAIL already has, via Theorems 1–2) without establishing that anything about learned policies
actually changes. A "yes" to this question alone invites exactly the reviewer response: "So what?"

**Reformed core research question:**

> When a longitudinal clinical state representation is constructed using rules that can reference
> treatment-derived quantities (as SOFA's cardiovascular subscore does), can we (1) formally prove
> which parts of the resulting action-predictability are attributable to that construction, as
> opposed to ordinary treatment persistence, and (2) determine whether removing that attributable
> component changes the policy an offline-RL algorithm would learn?

This keeps the project's actual strength (proof-level rigor on a concrete mechanism) as the first
half, and makes the second half — currently H3, currently open — the thing that would make the
project's conclusions matter clinically, not just statistically.

**Central hypothesis (falsifiable, stated in advance):**

> H_SAIL: A nontrivial share of the AUROC gap measured in Experiment 2 (0.900 → 0.791) is
> attributable to the proven definitional and window-overlap mechanisms specifically — evidenced by
> a paired-bootstrap-significant decay in offset-predictability (§H3) — and sanitizing the state to
> remove these mechanisms changes the action distribution an offline-RL algorithm learns on a
> nontrivial fraction of states (a threshold to be pre-registered, e.g. >10%, matching the scale of
> disagreement found by Off by a Beat's 44.7% for a different mechanism).

This is explicitly falsifiable: if the decay curve is flat (persistence dominates) *and* sanitized
vs. unsanitized policies agree on nearly all states, H_SAIL is false, and the honest conclusion
becomes "the mechanisms are mathematically real but practically inert in this cohort" — itself a
publishable, useful null result (see §8).

---

## 4. Formal leakage definition — mechanism-agnostic

The existing theorems are correct but SOFA-specific. A general definition, stated once, is what
lets a second researcher apply the same diagnostic to a different score without redoing the proof
strategy from scratch.

**Setup.** Let `X_t` denote physiological information available at time `t` (unobserved directly;
proxied by measurements), `H_t` the treatment history up to `t`, and `S_t = φ(X_t, H_t)` the state
construction function actually used — an explicit function of both physiology and treatment
history, since most clinical scores (SOFA included) are defined this way by design (SOFA's
cardiovascular component literally takes drug/dose as an argument). `A_t` is the action at `t`.

**Definition (state-construction leakage).** A component `c` of `S_t = φ(X_t, H_t)` exhibits
*definitional leakage* at history `h` if there exists a nonempty set of physiological values
`{x_1, x_2, \dots}` such that `c(x_i, h) = c(x_j, h)` for all `i,j` — i.e., the component is
constant in `X_t` once `H_t = h` is fixed. This generalizes Theorem 1 directly: `h` there is "any
nonzero dose," and the constant value is the dose-determined score.

**Definition (window-overlap leakage).** For a state built by aggregating a function `g` over a
lookback window `[t-w, t)`, define contamination `c_t(w) = O_t(w)/w` as in Proposition 1. Window-
overlap leakage exists whenever `c_t(w) > 0`, and the *fractional* leakage rate is governed by the
exact derivative already proven (§Proposition 1). This generalizes to *any* fixed-window
aggregation over longitudinal EHR data, independent of `g` or `w`'s choice.

**A general leakage functional — proposed, not yet formally developed to theorem-level.**
`[PROPOSED]` A natural candidate, matching the conditional-mutual-information intuition in the
brief but avoiding forcing it where inappropriate:

```
L(S, A, X, H) = I(S_t ; A_t | X_t)  —  the information about the next action recoverable
                                        from the state, beyond what physiology alone provides
```

This is *not* proposed as a drop-in replacement for the AUROC-based recoverability metric already
in use (Experiment 2) — AUROC is a simpler, more interpretable, more estimable quantity for a
finite, imperfectly-measured cohort, and mutual information estimation in this setting is itself
methodologically fraught (curse of dimensionality, discretization sensitivity). The right role for
`L` is as a **theoretical target** the AUROC-based metric is estimating a monotonic proxy for —
worth stating explicitly in the paper's Methods section as a limitation-and-justification pair,
not as a claim that mutual information was actually estimated.

**What a useful leakage metric needs (properties, not yet all verified for the current metric):**
(1) zero when the state is provably a deterministic function of physiology alone; (2) monotonic in
the true confounding-feedback strength under a simulated ground truth (this is exactly what
Experiment G, §5, is designed to check); (3) decomposable into a definitional component and a
temporal/window component, matching the two proven mechanisms, so a practitioner knows *which* fix
to apply.

---

## 5. Experimental matrix

Full specification for every experiment in the brief, at the depth actually achievable before
Friday. RED experiments get complete specs since they don't require new compute. YELLOW/GREEN get
lighter specs — designed, not yet resourced.

### RED — designed and defensible now, executable once compute is available

**Experiment C — Treatment persistence control (this is H3, already partially specified)**

- RQ: Does the AUROC gap reflect the proven mechanisms specifically, or ordinary persistence?
- H0: `Δ = AUROC(0) − AUROC(8) = 0` (persistence-only; no offset-specific decay)
- H1: `Δ > 0`, paired-bootstrap CI excludes 0
- Dataset/cohort: existing verified 11,354-stay cohort, no new extraction needed
- State definitions: variants A (full) through E (physiology-only), already built
- Statistical test: paired cluster bootstrap on `Δ` directly (resample patients, compute both
  AUROC(0) and AUROC(8) per resample) — already corrected on the proof page from an invalid
  CI-overlap heuristic
- Seeds: ≥1,000 bootstrap resamples (standard for stable percentile CIs)
- Expected failure mode: `Δ`'s CI includes 0 → persistence dominates; this is a valid, reportable
  outcome, not a project failure (see §8)
- **Compute requirement: none beyond what's already run for Experiment 2.** This should be the
  first thing run once time permits — it requires no new data extraction.

**Experiment D — Counterfactual state sanitization (design only; the compute-heavy RL training is YELLOW)**

- RQ: Does a sanitized state (variant D, already defined: cardio subscore replaced with a
  MAP-only proxy, total recomputed) change a *learned policy*, not just an AUROC?
- Design: train the *same* offline-RL algorithm (to be chosen — see open decision below) on
  variant A vs. variant D state representations, holding cohort, action space, and reward
  identical
- Primary endpoint: fraction of states where the two policies' argmax action disagrees
  (directly comparable to Off by a Beat's 44.7% figure — same units, different mechanism)
- Secondary endpoints: policy entropy, action-distribution total variation distance, Q-value
  correlation
- **Open decision needed before this can be specced further, not resolved in this document:**
  which offline-RL algorithm (discrete Q-learning matching Komorowski's original approach, for
  direct comparability to both Komorowski 2018 and Off by a Beat; or a modern conservative
  method like CQL/BCQ). Recommend the discrete/tabular approach for the first pass specifically
  *because* it makes the comparison to both foundational papers apples-to-apples — a reviewer
  will ask why a different RL algorithm was used than the papers being compared against.
- Compute requirement: nontrivial (full offline-RL training pipeline) — this is the item most
  likely to actually wait for additional compute, exactly as the brief anticipates.

### YELLOW — designed, explicitly deferred pending compute or scope decisions

**Experiment A (leakage prevalence across representations), B (systematic window-size sweep),
E (policy divergence metrics), F (off-policy evaluation of sanitized vs. unsanitized policies)** —
each is a natural extension of C/D once the base comparison exists. Not separately re-specified
here to avoid the appearance of a padded matrix; each follows the same template as C/D with a
different independent variable (representation choice, window size, policy metric, OPE method
respectively).

**Experiment G — Synthetic ground-truth environment.** This is the single highest-leverage YELLOW
item, and probably deserves to be promoted to RED priority *for design* even though it can't run by
Friday, because it is what would let SAIL's leakage metric be validated against a known quantity —
directly answering "how do you know your metric measures what you say it measures?" A minimal
version: simulate patient trajectories where physiology and treatment are generated with a known,
tunable causal-feedback strength, construct a SOFA-like score from the simulated data, and check
whether the AUROC-gap metric recovers the injected leakage level monotonically. This does not
require MIMIC-IV access or heavy compute — it's a simulation study, buildable in Python without
GPU resources. **Recommend scoping this as the very next concrete task after this document,
independent of the Experiment C/D compute wait.**

### GREEN — future extension, correctly out of scope for Friday

Experiment H (external/generalization validation across datasets or RL algorithms) — appropriately
deferred; claiming generalization before a second dataset is even attempted would be the kind of
overclaim a reviewer catches immediately.

---

## 6. Adversarial review

**Reviewer 1 (MIT ML faculty) — attacks novelty and RL relevance**

| Criticism | Valid? | Current response | Missing response | Fix |
|---|---|---|---|---|
| "Isn't this just target leakage with medical terminology?" | Partially — the underlying causal shape (post-treatment variable) is known (Daoud et al. 2022) | None on the current site | Needs the §2.2 positioning explicitly stated | Add to `about.html`/`papers.html`; rehearse the one-paragraph answer |
| "Where's the RL-specific contribution, versus a causal-inference paper wearing an RL costume?" | Valid, sharp | H3's framing (predictability of *next action*, sequential) gestures at it | Need Experiment D's actual policy-divergence result to make this concrete | This is exactly why D matters more than more theorems |
| "You have zero trained RL policies in this project." | True, currently | None | — | State explicitly as the RED/YELLOW boundary; do not hide it |

**Reviewer 2 (causal inference professor) — attacks identifiability and confounding treatment**

| Criticism | Valid? | Current response | Missing response | Fix |
|---|---|---|---|---|
| "Why isn't Robins' g-formula tradition cited or engaged with?" | Valid, and a real gap found in this audit | None currently | A paragraph explaining why g-methods (built for *effect estimation* under treatment-confounder feedback) are a different tool than what SAIL needs (*detection*, not effect estimation) | Add citation + one paragraph distinguishing detection from estimation |
| "Conditioning on `S_t` (a descendant of `A_{t-1}`) to predict `A_t` — what's the actual estimand?" | Valid — this is a fair challenge to whether AUROC(S→A) is even the right quantity | The causal graph (Proposition 2) correctly frames `S_t` as a descendant | Doesn't yet state what the *causal* estimand would be, only the *predictive* one | State explicitly: this project's estimand is predictive/associational (recoverability), not causal (effect of leakage on outcomes) — and say so as a limitation |
| "Temporal ordering — is `A_t` truly the action *following* `t`, or is there an Off-by-a-Beat-style misalignment in your own pipeline?" | Now urgent given Discovery 2 | Not yet checked | **This needs to be verified against the actual notebook code before Friday** — see action item below | Grep the notebook's actual bin-alignment logic |

**Reviewer 3 (clinical AI researcher) — attacks clinical realism**

| Criticism | Valid? | Current response | Missing response | Fix |
|---|---|---|---|---|
| "Real sepsis-RL state spaces are 40+ dimensional, not just SOFA — why should this matter?" | Valid | Implicit in Corollary reasoning but not stated | An explicit sentence: SOFA components typically comprise a nontrivial fraction of any sepsis-RL feature set (cite Komorowski's own feature list) | Add to About/novelty section |
| "Could sanitization remove clinically useful information (e.g., that a patient's cardiovascular status is currently *managed*, which is itself informative)?" | Valid, sharp, currently unaddressed anywhere | None | This is a real open question — variant D's MAP-only proxy is a design choice with a cost, not a free lunch | State explicitly as a limitation, do not paper over it |
| "Does the AI Clinician (or any deployed system) actually use raw SOFA as state?" | Fair — worth confirming precisely which published pipelines use decomposed vs. total SOFA | Not verified | Check Komorowski's actual feature list | Verify before claiming broad applicability |

**Action items from this section that are genuinely urgent, not just thorough:** (a) verify the
notebook's action/state timestep alignment against Off by a Beat's "shifted vs. original" framing
— if SAIL's own pipeline uses the "original" (contemporaneous) alignment, that is a *third*, currently
undocumented leakage mechanism in SAIL's own data, and needs to be checked and disclosed either way;
(b) add the g-methods paragraph; (c) add the "40+ dimensional state" context sentence.

**Partial answer to (a), checked directly against this repo, not deferred:** `FORMAL_ANALYSIS.md`
already *defines* `A_t` as "vasopressor active in the interval **following** decision point `t`"
— that is the correct, "shifted" convention Off by a Beat recommends, stated as the formal
definition from the start. This is genuinely good news and worth saying plainly in the room if
asked. **What is not yet verified** is whether the actual notebook code that builds the Experiment
2 action-recoverability labels implements this definition exactly, or whether — as can happen —
the formal write-up states the intended convention while an implementation detail somewhere
uses the next bin's index inconsistently. This is a single, concrete, cheap thing to grep for in
the notebook (the cell that constructs `y_action` for Experiment 2) before claiming the alignment
question is closed. Flagging the distinction between "correctly defined" and "verified as
correctly implemented" precisely, rather than collapsing them, is itself the standard this whole
project has tried to hold itself to.

---

## 7. Red / Yellow / Green — what's actually needed before Friday

**RED (this document + immediate small fixes cover all of it):**
- Research question (reformed, §3) — done, this document
- Novelty statement (§2) — done, this document; **requires disclosure of the two new citations**
- Theoretical framework — already exists (Theorems 1–2, Proposition 1) at genuine proof rigor
- Mathematical definitions — general functional now stated (§4)
- Causal DAG — already exists on proof.html; needs one addition (Off by a Beat's index-misalignment
  as a third describable mechanism, stated in prose, not necessarily redrawn before Friday)
- Hypotheses — reformed (§3)
- Experimental matrix — done (§5), RED items fully specced
- Baselines — variants A–E already are the baseline ladder
- Statistical analysis plan — paired bootstrap on Δ, already corrected
- Expected outcomes — stated as explicit, falsifiable predictions (§3, §8)
- Limitations — compiled honestly in §6's tables and §8
- Publication strategy — §10
- Demo concept — §14 (concept only; building it is explicitly YELLOW/GREEN, see below)

**YELLOW (designed now, executed once compute/scope allows):**
- Experiment C's actual run (no new compute needed — should happen first, cheaply)
- Experiment G's synthetic environment (no MIMIC access needed — recommend prioritizing this
  immediately after Friday, since it doesn't wait on compute at all, only on engineering time)
- Experiment D's RL policy training (genuinely compute-bound)
- The g-methods engagement paragraph, the timestep-alignment verification, the two literature
  additions to `papers.html` — all small, should be done within days, not held for a future phase

**GREEN (future extension, correctly deferred):**
- Experiment H (external validation)
- The full BU Showcase demo build (§14) — concept is RED, implementation is GREEN/VS-Code work
- A formal general-leakage-metric theorem (beyond the functional stated in §4)
- The benchmark artifact (identity F) as a standalone deliverable


---

## 8. Success / failure / falsification criteria — do not protect the hypothesis

**Strongly supported if:** the paired-bootstrap decay in Experiment C is significant and large
(`Δ ≥ 0.10`, CI excludes 0), *and* Experiment D's sanitized-vs-unsanitized policy disagreement rate
is nontrivial (a rate comparable in order of magnitude to Off by a Beat's 44.7%, though an exact
pre-registered threshold should be set once D is scoped — recommend >10% as a first anchor, revised
after Experiment G validates the metric).

**Valuable but redirected if:** leakage is proven and measurable (already true) but Experiment D
shows negligible policy disagreement. The honest conclusion becomes: *these mechanisms are
mathematically real and provable, but practically inert for this specific cohort/algorithm/action
space* — itself worth writing up, since a negative result with proof-level rigor behind it is
more useful to the field than an unresolved "maybe" left in most critique papers.

**Should be reconsidered if:** Experiment C's decay is flat *and* a rigorous persistence-only
baseline (predicting `A_t` from `A_{t-1}` alone, no state at all) achieves comparable AUROC to the
full state — this would suggest the entire measured predictability, mechanisms and all, is
attributable to ordinary clinical continuity, not anything SOFA-specific. **This baseline (`A_{t-1}`-only
predictor) is missing from the current experimental design and should be added** — it is the single
cheapest, highest-value addition to Experiment 2's variant ladder (call it variant F: pure action-history,
zero physiology), directly operationalizing the persistence-pathway comparison the causal graph
already draws but never numerically bounds.

---

## 9. Publication strategy

| Target | Fit | Contribution bar required | What reviewers expect | Rejection risk if |
|---|---|---|---|---|
| **Ambitious** — *Nature Medicine* / *npj Digital Medicine* (the exact venue Off by a Beat just appeared in) | High topical fit, direct precedent | Experiment D's policy-level result, not just AUROC | A clinically legible headline finding (a specific, quantified overtreatment/undertreatment pattern, as Off by a Beat delivered via GCS/SOFA stratification) | Submitted with only Theorems 1–2 and no policy consequence — will read as "interesting but so what" |
| **Realistic** — ML4H / CHIL (Conference on Health, Inference and Learning) / a workshop at NeurIPS/ICML | Very high fit — exactly the audience that already engages with Gottesman, Jeter, Killian et al. | The current formal apparatus plus Experiment C's result, even without D | Rigor on the causal/statistical side, willingness to state H3 honestly as open if D isn't done yet | Overclaiming leakage "invalidates" AI Clinician-style policies without the policy-level evidence |
| **Fallback** — a focused methods paper or extended technical report (e.g., arXiv preprint + workshop poster) | Always achievable | The theorems alone, positioned explicitly as a methodological note, not a full empirical study | Mathematical correctness (already met), honest scope statement | Essentially none, if scoped honestly as "formal analysis + open empirical question" |

**Recommendation:** target CHIL or an ML4H workshop as the realistic near-term goal — the venue
culture there explicitly values exactly this kind of methodological rigor-plus-honesty framing, and
both venues have prior work (Killian et al., Jeter et al.) this project already sits adjacent to.

---

## 10. PI defense structure (10 minutes)

| # | Slide | One-sentence takeaway | Say | Likely PI question | Answer |
|---|---|---|---|---|---|
| 1 | Problem | Sepsis-RL state representations can be built from rules that reference treatment directly | "SOFA's cardiovascular score takes drug and dose as literal inputs." | "Isn't this well known?" | "The *mechanism* — a provable non-identifiability — isn't in the literature; the *general concern* about confounding is (Gottesman 2019), which we cite." |
| 2 | Why current evaluation is insufficient | AUROC-based recoverability alone can't distinguish genuine leakage from persistence | Show the causal graph's two pathways | "Then why report AUROC at all?" | "It's necessary evidence, not sufficient — that's exactly the gap Experiment C's design closes." |
| 3 | SAIL hypothesis | Reformed research question (§3) | Read it once, plainly | "What would prove you wrong?" | Point directly to §8's falsification criteria |
| 4 | Mathematical mechanism | Two proven theorems, not two observations | Show Theorem 1's corrected branch structure | "Is the dopamine=6 example a real clinical scenario?" | "Yes — it's a moderate-dose infusion within the range this cohort's patients actually receive; verified against the notebook's real implementation, not invented." |
| 5 | Empirical evidence so far | 11,354 stays, two mechanisms measured, one bug-fix history that survived scrutiny | Show the Evidence page's table | "How do I know the bugs are actually fixed, not just relabeled?" | "Independently re-derived five times; one bug confirmed by literally recovering the original buggy run and reproducing its exact wrong numbers." |
| 6 | What remains unknown | H3, stated as a real open question | Say plainly: "We do not yet know if this matters for policy." | "Why should I fund/support work with an admittedly open core question?" | "Because the theorems de-risk the expensive part — we know *where* to look before spending compute, which is the value of doing theory first." |
| 7 | New research framework | The general leakage functional (§4), positioned as first-pass | Show the definition, not apologize for its incompleteness | "Is this publishable on its own?" | "As a methods note, yes; as a full framework claim, not yet — needs Experiment G." |
| 8 | Experiments | RED/YELLOW/GREEN (§7) | Be explicit about what's compute-gated vs. not | "What can you finish with zero new compute?" | "Experiment C and Experiment G — both should start immediately." |
| 9 | Demo | One sentence describing the September concept (§14) | Do not over-promise the build state | "Is this built yet?" | "Concept and architecture are designed; implementation is scoped as a distinct engineering phase, starting now, four months out." |
| 10 | Broader impact & limitations | State the sanitization-removes-useful-information risk explicitly | Own it, don't bury it | "What's the biggest weakness right now?" | "No trained RL policy anywhere in the project yet — that's the single fact most likely to be challenged, and it's true." |

## 11. Anticipated PI questions (selected, with answers)

1. **"Isn't this just target leakage?"** — The causal *shape* (post-treatment variable) is a named
   phenomenon (Daoud et al. 2022); the *mechanism-specific proof* for a clinical score, and its
   placement in a sequential-decision setting, is not.
2. **"Why is this specifically an RL problem?"** — Because the consequence isn't a biased ATE
   estimate (the text-leakage literature's concern) but a policy that could recommend actions based
   on its own past recommendations — a feedback loop unique to sequential decision-making.
3. **"If the action is persistent, why does prediction from the state imply leakage?"** — It
   doesn't, by itself; that's exactly why H3 exists and why Experiment C's paired test (not a
   CI-overlap heuristic) is the actual disambiguating instrument.
4. **"Why should SOFA be considered invalid?"** — It isn't being called invalid for its designed
   purpose (organ-dysfunction severity scoring); the claim is narrower — it's a poor choice as an
   RL *state* input specifically, because of properties irrelevant to its clinical use.
5. **"What is actually new?"** — See §2.3, items 3–4, verbatim.
6. **"What happens if the policy does not change after sanitization?"** — Reportable null result;
   see §8's "valuable but redirected" branch.
7. **"How do you know your physiology-only representation isn't simply worse?"** — Not yet fully
   known; this is why Experiment D compares policies, not just AUROC — a worse-but-honest state and
   a better-but-contaminated one need a policy-level, not just predictive, comparison.
8. **"What is the unit of leakage?"** — Currently AUROC points (a predictive-recoverability scale);
   §4 states the theoretical target (conditional mutual information) this is a proxy for.
9. **"What is your ground truth?"** — None yet for the *metric itself* — this is precisely
   Experiment G's purpose, and its absence is a real, acknowledged gap today.
10. **"Could this simply reflect clinician treatment behavior (i.e., legitimate clinical judgment
    encoded as a pattern)?"** — Yes, partially, and this is exactly the persistence pathway in the
    causal graph — not dismissed, formally represented as a competing explanation.
11. **"What's your strongest single publication claim if D never runs?"** — Theorem 1 plus
    Corollary 1.1 alone: a provable, not merely observed, non-identifiability result about a score
    used across a large fraction of published sepsis-RL work.
12. **"What's the minimum experiment needed to establish the thesis?"** — Experiment C alone,
    since it requires no new data and directly tests H3's core claim.

*(A full 30-question bank following this same answer style is a natural next artifact — flagged as
a quick follow-up, not included in full here to keep this document usable rather than exhaustive
for its own sake.)*


---

## 12. BU Showcase demo — concept, explicitly not built here

**This section is a design brief for a separate engineering phase, not a build.** The full
15-feature demo in the original brief (dual RL agents, live Q-value comparison, a leakage
forensics trace, a "stress test" mode) requires Experiment D's trained policies to exist — it
cannot be built honestly with real numbers before that experiment runs. Building it now would mean
either fabricating Q-values (explicitly forbidden) or shipping a demo that *looks* like it shows
real dual-agent divergence while actually showing nothing. Neither is acceptable.

**What can be honestly built now, as a September-appropriate first version:**
- The already-existing live mechanism visualizer (real, verified) as the "Act 1" — DAG lighting up,
  state vector contamination, live gauge — all genuinely computed from the real, cited numbers.
- A **signature visualization** (§13 below) as "Act 2" — this can be built now, using only the
  already-verified AUROC values for variants A–E, no fabrication required.
- A clearly-labeled "Act 3: what we don't know yet" panel, presenting H3 and Experiment D as an
  open question the audience is invited to think about — turning the current incompleteness into
  the actual hook, rather than hiding it. "We proved this. We don't yet know if it matters. Here's
  the experiment that would tell us" is a genuinely strong, honest 60-second scientific story.

**Once Experiment D actually runs**, the dual-agent comparison, Q-value divergence, and stress-test
mode become buildable with real data — that is the natural Act 4, added when true.

**Recommended engineering approach:** this build (interactive, JS-heavy, needs real design
iteration) is exactly the kind of task suited to a dedicated Claude Code session in VS Code,
working directly against this repo's existing Eleventy site and design system, rather than
attempted inside this document. Suggested first prompt for that session, once ready:

> Build a new `/showcase/` page for the September BU Health Data Science & AI Showcase, using the
> existing site's design tokens. Act 1: embed or link the existing live mechanism visualizer. Act
> 2: build the signature "State Purity vs. Action Recoverability" plane (spec in
> docs/PI_DEFENSE_PREP.md §13), plotting the five already-verified AUROC values for variants A–E.
> Act 3: a clearly-labeled panel presenting H3 as an open question. Do not fabricate any policy
> comparison, Q-value, or dual-agent visualization — those depend on Experiment D, which hasn't run.

### 12.1 A better opening hook than the brief's draft

The brief's suggested opener ("If an AI recommends a vasopressor because it sees a patient's
physiology, that is learning. But what if the state already tells the AI that a vasopressor was
given?") is good but slightly soft in its second sentence. A tighter version, matching the "≤60
seconds" and "provocative" requirements:

> "We gave a model a question and accidentally also gave it the answer. This is that story — and
> it's not about a bad model. It's about a widely-used clinical score that was never designed to be
> a machine-learning feature in the first place."

---

## 13. Signature visualization — "State Purity vs. Action Recoverability" plane

**Axes, defined mathematically, not just visually:**
- **x-axis — Physiological purity:** `1 − (definitional-leakage indicator rate)`, i.e., the
  fraction of a state's SOFA-derived features that pass Theorem 1's non-identifiability check
  (constant-in-MAP-given-treatment) as *false* — physiology genuinely still drives the score. For
  variant E (physiology-only, no dose-derived component at all), this is 1 by construction.
- **y-axis — Action recoverability:** the AUROC already computed for each variant (0.900 down to
  0.791) — no new computation needed, directly plottable today.

**Where each existing variant sits (using already-verified numbers, nothing new):**

| Variant | Purity (x) | AUROC (y) |
|---|---|---|
| A — full state | low (contains raw σ_cardio) | 0.900 |
| B — total removed, subscore kept | low (subscore itself still dose-determined) | 0.900 |
| C — subscore removed, total kept | low (reconstructible, per Theorem 2) | 0.885 |
| D — MAP-only proxy, total recomputed | high | 0.792 |
| E — physiology-only | highest (by construction) | 0.791 |

This plane makes the entire project's empirical finding legible in one glance: purity and
recoverability move together for D and E (the sanitized ones) but *not* for B and C, visually
demonstrating Theorem 2's reconstruction argument — C looks "purified" by name (subscore removed)
but sits at the same predictability as the unpurified state, because purity and *feature-list
membership* are different things. **This single plot is, on its own, a strong visual argument for
why "just remove the feature" (a naive practitioner's first instinct) doesn't work — arguably the
single most legible communication of the whole project's core finding.**

This is buildable today with the Visualizer/chart tooling already used elsewhere on the site — a
strong first candidate for the actual Friday-relevant deliverable, since it requires zero new
experiments and directly visualizes already-verified numbers.

---

## 14. Honest scoring — current vs. redesigned

| Category | Current | Redesigned (after this document's changes are actually made) | What causes the increase |
|---|---|---|---|
| Scientific novelty | 5 | 7 | Honest positioning against Daoud et al. and Off by a Beat, rather than an implicit (and incorrect) claim of being first to name treatment-leakage-like phenomena |
| Theoretical depth | 7 | 7 | Already genuinely strong (real proofs); §4's general functional is a first pass, not yet theorem-level, so no increase claimed here without doing the work |
| RL contribution | 3 | 5 | Reformed research question ties the mechanism explicitly to policy consequences; still capped until Experiment D produces a real number |
| Causal rigor | 6 | 7 | Adding the g-methods engagement and the explicit predictive-vs-causal-estimand statement (§6, Reviewer 2) |
| Clinical relevance | 5 | 6 | Explicit acknowledgment of the sanitization-cost tradeoff (Reviewer 3) makes the framing more credible, not less |
| Experimental rigor | 4 | 4 | Cannot honestly increase until Experiment C actually runs — designing it doesn't run it |
| Statistical rigor | 6 | 8 | The CI-overlap-to-paired-bootstrap fix (already made on proof.html) is a real, completed improvement |
| Generalizability | 3 | 5 | The mechanism-agnostic definitions in §4 genuinely widen scope, even before a second instantiation exists |
| Reproducibility | 8 | 8 | Already a genuine strength; no claimed change |
| Software quality | 7 | 7 | The site/build infrastructure is solid; this document doesn't touch it |
| Demo quality | 6 | 6 (concept), pending → 8 once built | Explicitly not inflating this before the build exists |
| Publication readiness | 4 | 6 | A CHIL/ML4H-scoped submission is realistic today; a *Nature Medicine*-scoped one is not, and shouldn't be claimed as such |
| PhD-level potential | 6 | 8 | The identity decision (§1) and the falsifiable, policy-consequential reformed question (§3) are what move this most — a defensible research *program*, not a single audit |

**What would move every score further, in priority order:** (1) run Experiment C — cheapest, fastest,
most falsification-relevant; (2) build Experiment G's synthetic validation — no compute or MIMIC
access wait required; (3) scope and eventually run Experiment D, which is the only item that
actually requires new compute.

---

*End of document. Companion follow-up work, explicitly separate: (a) add the two new citations to
`papers.html`/`FORMAL_ANALYSIS.md`; (b) verify the notebook's Experiment 2 action-label alignment
directly; (c) a dedicated VS Code Claude Code session to build the signature visualization (§13)
and the honestly-scoped Act 1–3 showcase page (§12).*

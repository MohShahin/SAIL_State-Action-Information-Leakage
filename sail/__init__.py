"""
sail-leakage: detectors for state-action information leakage in offline
reinforcement learning, generalized from the proofs and empirical audit at
https://github.com/MohShahin/SAIL_State-Action-Information-Leakage.

No claim is made that this package catches every possible leakage pattern --
each detector generalizes a specific result this project has already proven,
not an exhaustive taxonomy. This is a growing, evidence-based specification,
not a finished standard.

Phase A ships two of five planned categories: construction leakage and
reconstruction leakage. The remaining three (temporal/window-overlap,
timing-violation, and persistence-dominance) land in Phase B, along with a
single ``sail.check(df, ...)`` convenience entry point that dispatches across
all five and reports plainly on any category it can't run for lack of a
required column. Until Phase B, use the detector classes directly.
"""

from .detectors.base import LeakageCheck, LeakageFinding
from .detectors.construction import ConstructionLeakageDetector
from .detectors.reconstruction import ReconstructionLeakageDetector
from .report import LeakageReport

__version__ = "0.1.0"

__all__ = [
    "LeakageCheck",
    "LeakageFinding",
    "ConstructionLeakageDetector",
    "ReconstructionLeakageDetector",
    "LeakageReport",
]

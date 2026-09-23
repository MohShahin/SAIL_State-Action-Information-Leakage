"""
sail-leakage: detectors for state-action information leakage in offline
reinforcement learning, generalized from the proofs and empirical audit at
https://github.com/MohShahin/SAIL_State-Action-Information-Leakage.

No claim is made that this package catches every possible leakage pattern --
each detector generalizes a specific result this project has already proven,
not an exhaustive taxonomy. This is a growing, evidence-based specification,
not a finished standard.

All five planned categories now exist: construction leakage and
reconstruction leakage (Phase A); temporal/window-overlap, timing-violation,
and persistence-dominance (Phase B). Note that persistence-dominance is
explicitly NOT a leakage category -- see ``sail.detectors.persistence`` for
why. ``sail.check(df, ...)`` (Phase C1) dispatches across all five and
reports plainly, per category, on anything it can't run for lack of a
required input -- see ``sail.check`` for a note on where its signature had
to grow beyond this package's original API sketch once the actual detectors
existed.
"""

from .check import check
from .detectors.base import LeakageCheck, LeakageFinding
from .detectors.construction import ConstructionLeakageDetector
from .detectors.persistence import PersistenceDominanceDetector
from .detectors.reconstruction import ReconstructionLeakageDetector
from .detectors.temporal_overlap import TemporalOverlapDetector
from .detectors.timing_violation import TimingViolationDetector
from .report import LeakageReport

__version__ = "0.1.0"

__all__ = [
    "check",
    "LeakageCheck",
    "LeakageFinding",
    "ConstructionLeakageDetector",
    "ReconstructionLeakageDetector",
    "TemporalOverlapDetector",
    "TimingViolationDetector",
    "PersistenceDominanceDetector",
    "LeakageReport",
]

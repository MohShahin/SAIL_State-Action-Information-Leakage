"""Shared interface every SAIL leakage detector implements."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LeakageFinding:
    """The result of running one leakage check against one spec."""

    category: str
    flagged: bool
    explanation: str
    evidence: dict[str, Any] = field(default_factory=dict)
    # "leakage" for the four leakage categories; "diagnostic" for persistence dominance, which is
    # explicitly not a leakage finding. Gates (CI, exit codes) must only fail on kind == "leakage".
    kind: str = "leakage"
    # True when the check could not actually test anything (no usable rows, no variation to test).
    # An inconclusive finding is never "not flagged": it is reported on its own.
    inconclusive: bool = False


class LeakageCheck(ABC):
    """Base interface every SAIL leakage detector implements."""

    @abstractmethod
    def run(self, df, spec: dict[str, Any]) -> LeakageFinding:
        """Run this check against `df` using the column names/callables in `spec`."""
        raise NotImplementedError

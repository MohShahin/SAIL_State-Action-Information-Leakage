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


class LeakageCheck(ABC):
    """Base interface every SAIL leakage detector implements."""

    @abstractmethod
    def run(self, df, spec: dict[str, Any]) -> LeakageFinding:
        """Run this check against `df` using the column names/callables in `spec`."""
        raise NotImplementedError

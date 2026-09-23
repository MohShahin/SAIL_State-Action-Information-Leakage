"""Collects findings from however many detectors were run into one report."""

import json
from dataclasses import dataclass, field

from .detectors.base import LeakageFinding


@dataclass
class LeakageReport:
    """Aggregates findings (and explicitly-skipped categories) across
    however many detectors were run against a given dataset."""

    findings: list[LeakageFinding] = field(default_factory=list)
    skipped: dict[str, str] = field(default_factory=dict)

    def add(self, finding: LeakageFinding) -> None:
        self.findings.append(finding)

    def skip(self, category: str, reason: str) -> None:
        """Record that a category couldn't be checked -- e.g. a required
        column wasn't provided. Callers should always call this rather than
        silently omitting a category, so the report says so explicitly."""
        self.skipped[category] = reason

    def summary(self) -> str:
        """Plain-language summary, not a dict dump."""
        flagged = [f for f in self.findings if f.flagged]
        clean = [f for f in self.findings if not f.flagged]
        lines: list[str] = []

        if flagged:
            lines.append(f"LEAKAGE FLAGGED ({len(flagged)}):")
            lines.extend(f"  [{f.category}] {f.explanation}" for f in flagged)
        if clean:
            lines.append(f"No leakage found ({len(clean)}):")
            lines.extend(f"  [{f.category}] {f.explanation}" for f in clean)
        if self.skipped:
            lines.append(f"Skipped ({len(self.skipped)}):")
            lines.extend(f"  [{cat}] {reason}" for cat, reason in self.skipped.items())
        if not lines:
            lines.append("No checks were run.")
        return "\n".join(lines)

    def to_json(self) -> str:
        payload = {
            "findings": [
                {
                    "category": f.category,
                    "flagged": f.flagged,
                    "explanation": f.explanation,
                    "evidence": f.evidence,
                }
                for f in self.findings
            ],
            "skipped": self.skipped,
        }
        return json.dumps(payload, indent=2, default=str)

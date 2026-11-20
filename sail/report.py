"""Collects findings from however many detectors were run into one report."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from .detectors.base import LeakageFinding

#: Version of the JSON layout produced by ``LeakageReport.to_json``. Bump on any breaking change.
REPORT_SCHEMA_VERSION = "1"


@dataclass
class LeakageReport:
    """Aggregates findings (and explicitly-skipped categories) across
    however many detectors were run against a given dataset."""

    findings: list[LeakageFinding] = field(default_factory=list)
    skipped: dict[str, str] = field(default_factory=dict)
    #: Provenance written by ``sail.check``: input shape, column names and a content hash. It
    #: never contains row values.
    meta: dict[str, Any] = field(default_factory=dict)

    def add(self, finding: LeakageFinding) -> None:
        self.findings.append(finding)

    def skip(self, category: str, reason: str) -> None:
        """Record that a category couldn't be checked -- e.g. a required
        column wasn't provided. Callers should always call this rather than
        silently omitting a category, so the report says so explicitly."""
        self.skipped[category] = reason

    # ---- gate-friendly views -------------------------------------------------------------
    @property
    def leakage_flagged(self) -> list[LeakageFinding]:
        """Flagged findings that are genuine leakage (excludes diagnostics such as persistence
        dominance, which is explicitly not a leakage finding)."""
        return [f for f in self.findings if f.flagged and f.kind == "leakage"]

    @property
    def diagnostics_flagged(self) -> list[LeakageFinding]:
        return [f for f in self.findings if f.flagged and f.kind != "leakage"]

    @property
    def inconclusive(self) -> list[LeakageFinding]:
        return [f for f in self.findings if f.inconclusive]

    def exit_code(self, fail_on: str = "leakage") -> int:
        """0 = pass; 1 = a gated condition was found; 3 = nothing could be tested.

        ``fail_on``: ``"leakage"`` (default) fails on genuine leakage findings only;
        ``"any"`` also fails on flagged diagnostics and on inconclusive checks; ``"never"``
        always passes (except 3 when no check ran at all).
        """
        if not self.findings:
            return 3
        if fail_on == "never":
            return 0
        if self.leakage_flagged:
            return 1
        if fail_on == "any" and (self.diagnostics_flagged or self.inconclusive):
            return 1
        if len(self.inconclusive) == len(self.findings):
            return 3
        return 0

    # ---- output --------------------------------------------------------------------------
    def summary(self) -> str:
        """Plain-language summary, not a dict dump. Grouped flagged / not
        flagged / not run, in that order -- flagged first, since that's what
        a user actually came for."""
        inconclusive = [f for f in self.findings if f.inconclusive]
        flagged = [f for f in self.findings if f.flagged and not f.inconclusive]
        clean = [f for f in self.findings if not f.flagged and not f.inconclusive]
        lines: list[str] = []

        def tag(f: LeakageFinding) -> str:
            return f"[{f.category}]" + (" (diagnostic, not leakage)" if f.kind != "leakage" else "")

        if flagged:
            lines.append(f"FLAGGED ({len(flagged)}):")
            lines.extend(f"  {tag(f)} {f.explanation}" for f in flagged)
        if inconclusive:
            lines.append(f"INCONCLUSIVE ({len(inconclusive)}): could not be tested, not a clean result")
            lines.extend(f"  {tag(f)} {f.explanation}" for f in inconclusive)
        if clean:
            lines.append(f"NOT FLAGGED ({len(clean)}):")
            lines.extend(f"  {tag(f)} {f.explanation}" for f in clean)
        if self.skipped:
            lines.append(f"NOT RUN ({len(self.skipped)}):")
            lines.extend(f"  [{cat}] {reason}" for cat, reason in self.skipped.items())
        if self.skipped:
            lines.append(
                "TO RUN MORE CHECKS: each needs an extra input beyond the table itself -- "
                "see the 'To enable' hints above or print(sail.requirements())."
            )
        if not lines:
            lines.append("No checks were run.")
        return "\n".join(lines)

    def to_json(self, generated_at: Optional[str] = None) -> str:
        """Machine-readable report. Stable layout, identified by ``schema_version``.

        ``generated_at`` defaults to the current UTC time; pass a fixed string for reproducible
        output.
        """
        from . import __version__

        payload = {
            "schema_version": REPORT_SCHEMA_VERSION,
            "sail_version": __version__,
            "generated_at": generated_at
            or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "input": self.meta,
            "findings": [
                {
                    "category": f.category,
                    "kind": f.kind,
                    "flagged": f.flagged,
                    "inconclusive": f.inconclusive,
                    "explanation": f.explanation,
                    "evidence": f.evidence,
                }
                for f in self.findings
            ],
            "skipped": self.skipped,
            "result": {
                "leakage_flagged": len(self.leakage_flagged),
                "diagnostics_flagged": len(self.diagnostics_flagged),
                "inconclusive": len(self.inconclusive),
                "not_run": len(self.skipped),
            },
        }
        return json.dumps(payload, indent=2, default=str)

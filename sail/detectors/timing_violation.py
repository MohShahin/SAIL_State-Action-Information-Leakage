"""
Category 4 -- timing-violation leakage: the strict, reserved sense of
"leakage" in this project's own taxonomy (see ``mechanisms.html`` #term, the
H1/H2 terminology correction). A state's window extends into or past the
timestamp of the action it's meant to precede.

Generalizes the alignment check already performed manually on this project's
own pipeline (the notebook's ``build_action_labels`` plus the ``shift(-1)``
step): the state built from bin t's own window is paired with the action
label for bin t+1's window, and those two windows are adjacent --
``[t*I, (t+1)*I)`` and ``[(t+1)*I, (t+2)*I)`` -- touching at exactly one
boundary, never overlapping. That verified real case is this detector's own
first test.
"""

from typing import Any

from .base import LeakageCheck, LeakageFinding


class TimingViolationDetector(LeakageCheck):
    """Detects Category 4 timing-violation leakage.

    Required ``spec`` keys:
        state_end_col: column naming each row's state window END.
        action_start_col: column naming each row's action window (or
            instantaneous action timestamp) START.

    A row is a violation when the action's window starts strictly before the
    state's window ends -- genuine boundary overlap. An action window that
    starts exactly when the state window ends is adjacent, not overlapping,
    and is NOT a violation: this project's own real pipeline is exactly that
    adjacent case, verified as zero overlap -- a stricter ``<=`` here would
    incorrectly flag it.
    """

    def run(self, df, spec: dict[str, Any]) -> LeakageFinding:
        state_end_col = spec["state_end_col"]
        action_start_col = spec["action_start_col"]

        violation = df[action_start_col] < df[state_end_col]
        n_violations = int(violation.sum())
        n_rows = int(len(df))
        flagged = n_violations > 0

        if flagged:
            explanation = (
                f"{n_violations} of {n_rows} row(s) have an action window that "
                f"starts before the state window ends -- genuine boundary overlap. "
                f"This is the strict, reserved sense of 'leakage' in this project's "
                f"taxonomy."
            )
        else:
            explanation = (
                f"No timing violation in {n_rows} row(s): every action window "
                f"starts at or after its corresponding state window's end."
            )

        return LeakageFinding(
            category="timing_violation_leakage",
            flagged=flagged,
            explanation=explanation,
            evidence={"n_violations": n_violations, "n_rows": n_rows},
        )

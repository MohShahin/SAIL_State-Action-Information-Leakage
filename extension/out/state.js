"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.initialState = initialState;
exports.isWebviewMessage = isWebviewMessage;
exports.computeStatusBar = computeStatusBar;
const checks_1 = require("./checks");
function initialState() {
    return {
        dataset: null,
        checks: checks_1.CHECKS.map((c) => ({ id: c.id, name: c.name, question: c.question, status: 'pending' })),
    };
}
function isWebviewMessage(value) {
    return typeof value === 'object' && value !== null && value.type === 'ready';
}
/**
 * What the status bar item should show for the current app state. Pure: the same state always produces
 * the same text, so this is testable without a running VS Code or status bar item.
 */
function computeStatusBar(state) {
    const statuses = state.checks.map((c) => c.status);
    if (statuses.some((s) => s === 'running')) {
        return { text: 'SAIL: Checking…', tooltip: 'SAIL is running your checks.', settled: false, warn: false };
    }
    const settledChecks = state.checks.filter((c) => c.status === 'flagged' || c.status === 'passed' || c.status === 'not-run');
    if (settledChecks.length === 0) {
        return {
            text: 'SAIL: Ready',
            tooltip: 'SAIL leakage checks: ready. Click to open.',
            settled: false,
            warn: false,
        };
    }
    const flagged = settledChecks.filter((c) => c.status === 'flagged').length;
    if (flagged === 0) {
        return {
            text: 'SAIL: No issues found',
            tooltip: `None of the ${settledChecks.length} check(s) that ran found leakage. Click to open the report.`,
            settled: true,
            warn: false,
        };
    }
    const noun = flagged === 1 ? 'issue' : 'issues';
    return {
        text: `SAIL: ${flagged} ${noun} found`,
        tooltip: `${flagged} of ${settledChecks.length} check(s) that ran found leakage. Click to open the report.`,
        settled: true,
        warn: true,
    };
}
//# sourceMappingURL=state.js.map
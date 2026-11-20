"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.initialWizardState = initialWizardState;
exports.computeViewModel = computeViewModel;
exports.categoryToCheckId = categoryToCheckId;
exports.mapReportToStatuses = mapReportToStatuses;
exports.buildResultCards = buildResultCards;
/**
 * The setup wizard's state and the pure functions that turn it into what the webview draws, and turn a
 * finished report back into sidebar check statuses. No `vscode` import here on purpose: everything in
 * this file runs (and is tested) without a running VS Code.
 */
const checks_1 = require("./checks");
function initialWizardState() {
    const enabled = {};
    for (const c of checks_1.CHECKS) {
        enabled[c.id] = true;
    }
    return {
        step: 'welcome',
        error: null,
        files: [],
        selectedFileId: null,
        columns: [],
        map: { stay: null, time: null, action: null, reward: null },
        enabled,
        isExample: false,
        datasetLabel: null,
        results: null,
        selectedResultId: null,
    };
}
const FIELD_META = [
    { key: 'stay', label: 'Patient or stay ID', help: 'Identifies each ICU stay' },
    { key: 'time', label: 'Time step', help: 'When each row was measured' },
    { key: 'action', label: 'Treatment (action)', help: 'What the model decides' },
    { key: 'reward', label: 'Outcome (reward)', help: 'What the model tries to improve' },
];
const VERDICT_LABEL = {
    pending: 'Pending',
    running: 'Running',
    flagged: 'Flagged',
    passed: 'Passed',
    'not-run': 'Not run',
    off: 'Off',
};
function computeViewModel(state) {
    const anyEnabled = Object.values(state.enabled).some(Boolean);
    const showNav = state.step === 'data' || state.step === 'map' || state.step === 'checks';
    const results = (state.results ?? []).map((r) => ({
        ...r,
        selected: r.id === state.selectedResultId,
        verdictLabel: VERDICT_LABEL[r.status],
    }));
    const flaggedCount = results.filter((r) => r.status === 'flagged').length;
    return {
        step: state.step,
        error: state.error,
        isWelcome: state.step === 'welcome',
        isData: state.step === 'data',
        isMap: state.step === 'map',
        isChecks: state.step === 'checks',
        isRunning: state.step === 'running',
        isDone: state.step === 'done',
        showNav,
        files: state.files.map((f) => ({ ...f, selected: f.id === state.selectedFileId })),
        fields: FIELD_META.map((f) => ({ ...f, value: state.map[f.key], options: state.columns })),
        checks: checks_1.CHECKS.map((c) => ({ id: c.id, name: c.name, question: c.question, on: state.enabled[c.id] })),
        nextDisabled: state.step === 'data' ? !state.selectedFileId : state.step === 'checks' ? !anyEnabled : false,
        nextLabel: state.step === 'checks' ? 'Run checks' : 'Continue',
        isExample: state.isExample,
        datasetLabel: state.datasetLabel,
        results,
        selectedResult: results.find((r) => r.selected) ?? null,
        flaggedCount,
        headline: `${flaggedCount} of ${checks_1.CHECKS.length} checks found leakage`,
    };
}
/** The category strings `sail.check()` actually reports, mapped back to a check's id. */
function categoryToCheckId(category) {
    if (category.startsWith('construction_leakage'))
        return 'c1';
    if (category === 'reconstruction_leakage')
        return 'c2';
    if (category === 'temporal_overlap_leakage')
        return 'c3';
    if (category === 'timing_violation_leakage')
        return 'c4';
    if (category === 'persistence_dominance')
        return 'c5';
    return null;
}
/**
 * Turns one finished `sail.check()` report into a status per check id.
 *
 * A check the user turned off is 'off', full stop -- it never shows as 'not-run' even though it is
 * also absent from the report (sail.check() has no way to tell "disabled" from "no reason to run it"
 * apart from the caller's own enabled/disabled record, which is exactly what `enabled` is here).
 */
function mapReportToStatuses(report, enabled) {
    const statuses = {};
    for (const id of Object.keys(enabled)) {
        statuses[id] = enabled[id] ? 'pending' : 'off';
    }
    for (const finding of report.findings) {
        const id = categoryToCheckId(finding.category);
        if (id) {
            // An inconclusive finding (e.g. too little data) is never shown as a pass.
            statuses[id] = finding.flagged ? 'flagged' : finding.inconclusive ? 'not-run' : 'passed';
        }
    }
    for (const category of Object.keys(report.skipped)) {
        const id = categoryToCheckId(category);
        if (id && enabled[id] && statuses[id] !== 'flagged' && statuses[id] !== 'passed') {
            statuses[id] = 'not-run';
        }
    }
    return statuses;
}
const OFF_EXPLANATION = 'You turned this check off before running.';
const OFF_FIX = 'Turn it back on and run again to see a result.';
const NOT_RUN_FIX = "SAIL didn't have enough information about this file to run this check.";
/**
 * Generic, honest guidance grounded in each detector's own real mechanism (see the detectors'
 * docstrings) -- never a dataset-specific claim, since the four generic wizard fields never tell SAIL
 * enough about the data to say anything more specific than this.
 */
const FIX_TEXT = {
    c1: {
        flagged: 'Remove or replace the state feature(s) that are computed from treatment doses, or use a version of the score that excludes treatment inputs.',
        notFlagged: 'Nothing to do -- the signal still determines the score independent of treatment status.',
    },
    c2: {
        flagged: "Remove the retained total (or the other retained components) as well, so the missing feature can't be reconstructed from what's left.",
        notFlagged: 'Nothing to do -- the removed feature is not recoverable from what was kept.',
    },
    c3: {
        flagged: 'Shorten the lookback window, or measure the state strictly before the treatment window starts.',
        notFlagged: "Nothing to do -- no decision point's window was mostly treatment.",
    },
    c4: {
        flagged: "Fix the alignment: the action window must start at or after the state window's end.",
        notFlagged: 'Nothing to do -- every action window already starts at or after its state window ends.',
    },
    c5: {
        flagged: "Compare your model against a simple 'repeat the last action' baseline before trusting its apparent skill.",
        notFlagged: "Nothing to do -- the state's predictive power isn't explained by ordinary treatment persistence alone.",
    },
};
function fixText(id, status) {
    if (status === 'off')
        return OFF_FIX;
    if (status === 'not-run')
        return NOT_RUN_FIX;
    const entry = FIX_TEXT[id];
    if (!entry)
        return '';
    return status === 'flagged' ? entry.flagged : entry.notFlagged;
}
/** Turns one finished report into the five-card results view's data. Pure; no vscode, no I/O. */
function buildResultCards(report, enabled) {
    const statuses = mapReportToStatuses(report, enabled);
    const explanationByCheck = new Map();
    for (const finding of report.findings) {
        const id = categoryToCheckId(finding.category);
        if (id) {
            explanationByCheck.set(id, finding.explanation);
        }
    }
    const skippedByCheck = new Map();
    for (const [category, reason] of Object.entries(report.skipped)) {
        const id = categoryToCheckId(category);
        if (id) {
            skippedByCheck.set(id, reason);
        }
    }
    return checks_1.CHECKS.map((c) => {
        const status = statuses[c.id];
        const explanation = status === 'off' ? OFF_EXPLANATION : explanationByCheck.get(c.id) ?? skippedByCheck.get(c.id) ?? '';
        return { id: c.id, name: c.name, question: c.question, status, explanation, fix: fixText(c.id, status) };
    });
}
//# sourceMappingURL=wizardModel.js.map
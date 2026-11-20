"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
const assert = __importStar(require("assert"));
const columnMapping_1 = require("../../columnMapping");
const wizardModel_1 = require("../../wizardModel");
const checks_1 = require("../../checks");
const state_1 = require("../../state");
const reportHtml_1 = require("../../reportHtml");
const friendlyError_1 = require("../../friendlyError");
suite('column auto-detect (pure)', () => {
    test('detects the four generic fields from typical names', () => {
        assert.deepStrictEqual((0, columnMapping_1.autoDetect)(['patient_id', 'step', 'treatment', 'outcome']), {
            stay: 'patient_id',
            time: 'step',
            action: 'treatment',
            reward: 'outcome',
        });
    });
    test('detects the README quickstart-style names too', () => {
        const map = (0, columnMapping_1.autoDetect)(['stay_id', 'charttime_bin', 'vaso_dose_bin', 'survived_90d']);
        assert.deepStrictEqual(map, { stay: 'stay_id', time: 'charttime_bin', action: 'vaso_dose_bin', reward: 'survived_90d' });
    });
    test('never assigns the same column to two fields', () => {
        // "action_time" matches both the time pattern and nothing else; must not also get claimed by "action".
        const map = (0, columnMapping_1.autoDetect)(['action_time', 'treatment']);
        const values = Object.values(map).filter((v) => v !== null);
        assert.strictEqual(new Set(values).size, values.length, `duplicate assignment in ${JSON.stringify(map)}`);
    });
    test('unrecognised columns are left null, not guessed', () => {
        assert.deepStrictEqual((0, columnMapping_1.autoDetect)(['col_a', 'col_b']), { stay: null, time: null, action: null, reward: null });
    });
    test('an empty column list is handled without throwing', () => {
        assert.deepStrictEqual((0, columnMapping_1.autoDetect)([]), { stay: null, time: null, action: null, reward: null });
    });
});
suite('wizard view model (pure)', () => {
    test('the Data step is disabled until a file is selected', () => {
        const state = { ...(0, wizardModel_1.initialWizardState)(), step: 'data' };
        assert.strictEqual((0, wizardModel_1.computeViewModel)(state).nextDisabled, true);
        const withFile = { ...state, selectedFileId: 'x' };
        assert.strictEqual((0, wizardModel_1.computeViewModel)(withFile).nextDisabled, false);
    });
    test('the Checks step is disabled once every check is turned off', () => {
        const allOff = {};
        for (const c of checks_1.CHECKS)
            allOff[c.id] = false;
        const state = { ...(0, wizardModel_1.initialWizardState)(), step: 'checks', enabled: allOff };
        assert.strictEqual((0, wizardModel_1.computeViewModel)(state).nextDisabled, true);
    });
    test('nav is shown for data/map/checks and hidden for welcome/running/done', () => {
        for (const step of ['data', 'map', 'checks']) {
            assert.strictEqual((0, wizardModel_1.computeViewModel)({ ...(0, wizardModel_1.initialWizardState)(), step }).showNav, true, step);
        }
        for (const step of ['welcome', 'running', 'done']) {
            assert.strictEqual((0, wizardModel_1.computeViewModel)({ ...(0, wizardModel_1.initialWizardState)(), step }).showNav, false, step);
        }
    });
});
suite('report -> sidebar status mapping (pure)', () => {
    const enabledAll = {};
    for (const c of checks_1.CHECKS)
        enabledAll[c.id] = true;
    test('a flagged finding maps to the right check id', () => {
        const statuses = (0, wizardModel_1.mapReportToStatuses)({ findings: [{ category: 'construction_leakage_1a', flagged: true }], skipped: {} }, enabledAll);
        assert.strictEqual(statuses.c1, 'flagged');
    });
    test('a clean finding maps to passed, and the base "construction_leakage" category still maps to c1', () => {
        const statuses = (0, wizardModel_1.mapReportToStatuses)({ findings: [{ category: 'construction_leakage', flagged: false }], skipped: {} }, enabledAll);
        assert.strictEqual(statuses.c1, 'passed');
    });
    test('every real category string maps to the check the design puts it under', () => {
        const pairs = [
            ['construction_leakage_1a', 'c1'],
            ['construction_leakage_1b', 'c1'],
            ['reconstruction_leakage', 'c2'],
            ['temporal_overlap_leakage', 'c3'],
            ['timing_violation_leakage', 'c4'],
            ['persistence_dominance', 'c5'],
        ];
        for (const [category, id] of pairs) {
            const statuses = (0, wizardModel_1.mapReportToStatuses)({ findings: [{ category, flagged: true }], skipped: {} }, enabledAll);
            assert.strictEqual(statuses[id], 'flagged', category);
        }
    });
    test('a skipped category becomes not-run, only when the user left it enabled', () => {
        const statuses = (0, wizardModel_1.mapReportToStatuses)({ findings: [], skipped: { construction_leakage: 'not run: ...' } }, enabledAll);
        assert.strictEqual(statuses.c1, 'not-run');
        const c1Off = { ...enabledAll, c1: false };
        const statusesOff = (0, wizardModel_1.mapReportToStatuses)({ findings: [], skipped: { construction_leakage: 'not run: ...' } }, c1Off);
        assert.strictEqual(statusesOff.c1, 'off', 'a check the user disabled must stay "off", never "not-run"');
    });
});
suite('result cards (pure)', () => {
    const enabledAll = {};
    for (const c of checks_1.CHECKS)
        enabledAll[c.id] = true;
    test('one card per check, in the design order, carrying the real explanation text', () => {
        const report = {
            findings: [{ category: 'construction_leakage_1a', flagged: true, explanation: 'the real explanation' }],
            skipped: {
                reconstruction_leakage: 'not run: reconstruction_spec not provided',
                temporal_overlap_leakage: 'x',
                timing_violation_leakage: 'x',
                persistence_dominance: 'x',
            },
        };
        const cards = (0, wizardModel_1.buildResultCards)(report, enabledAll);
        assert.deepStrictEqual(cards.map((c) => c.id), checks_1.CHECKS.map((c) => c.id));
        const c1 = cards.find((c) => c.id === 'c1');
        assert.strictEqual(c1.status, 'flagged');
        assert.strictEqual(c1.explanation, 'the real explanation');
        assert.ok(c1.fix.length > 0);
        const c2 = cards.find((c) => c.id === 'c2');
        assert.strictEqual(c2.status, 'not-run');
        assert.strictEqual(c2.explanation, 'not run: reconstruction_spec not provided');
    });
    test('a check the user turned off gets its own explanation and fix text, not a blank card', () => {
        const off = { ...enabledAll, c3: false };
        const report = { findings: [], skipped: { temporal_overlap_leakage: 'would say not run, but the user disabled it' } };
        const cards = (0, wizardModel_1.buildResultCards)(report, off);
        const c3 = cards.find((c) => c.id === 'c3');
        assert.strictEqual(c3.status, 'off');
        assert.ok(c3.explanation.length > 0 && !c3.explanation.includes('would say not run'));
        assert.ok(c3.fix.length > 0);
    });
});
suite('status bar text (pure)', () => {
    function stateWith(statuses) {
        return { dataset: null, checks: checks_1.CHECKS.map((c) => ({ id: c.id, name: c.name, question: c.question, status: statuses[c.id] })) };
    }
    const allPending = Object.fromEntries(checks_1.CHECKS.map((c) => [c.id, 'pending']));
    test('before anything has run: Ready', () => {
        const view = (0, state_1.computeStatusBar)(stateWith(allPending));
        assert.strictEqual(view.text, 'SAIL: Ready');
        assert.strictEqual(view.warn, false);
    });
    test('while running: Checking, never a stale Ready or issue count', () => {
        const view = (0, state_1.computeStatusBar)(stateWith({ ...allPending, c1: 'running' }));
        assert.strictEqual(view.text, 'SAIL: Checking…');
    });
    test('after a run with nothing flagged: No issues found, no warning color', () => {
        const view = (0, state_1.computeStatusBar)(stateWith({ c1: 'passed', c2: 'passed', c3: 'not-run', c4: 'off', c5: 'off' }));
        assert.strictEqual(view.text, 'SAIL: No issues found');
        assert.strictEqual(view.warn, false);
    });
    test('after a run with issues: the exact count, singular vs plural, and the warning color', () => {
        const one = (0, state_1.computeStatusBar)(stateWith({ c1: 'flagged', c2: 'passed', c3: 'passed', c4: 'passed', c5: 'passed' }));
        assert.strictEqual(one.text, 'SAIL: 1 issue found');
        assert.strictEqual(one.warn, true);
        const three = (0, state_1.computeStatusBar)(stateWith({ c1: 'flagged', c2: 'flagged', c3: 'flagged', c4: 'passed', c5: 'passed' }));
        assert.strictEqual(three.text, 'SAIL: 3 issues found');
    });
});
suite('plain-language error messages (pure)', () => {
    test('every message is a plain sentence: no exception class names, no stack traces', () => {
        const cases = [
            (0, friendlyError_1.explainPythonMissing)(['python3', 'python']),
            (0, friendlyError_1.explainSailMissing)('/usr/bin/python3', "ModuleNotFoundError: No module named 'sail'"),
            (0, friendlyError_1.explainBridgeError)("FileNotFoundError: [Errno 2] No such file or directory: '/tmp/x.csv'"),
            (0, friendlyError_1.explainBridgeError)('PermissionError: [Errno 13] Permission denied'),
            (0, friendlyError_1.explainBridgeError)("UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff"),
            (0, friendlyError_1.explainBridgeError)('ParserError: Error tokenizing data'),
            (0, friendlyError_1.explainBridgeError)('KeyError: \'no_such_column\''),
        ];
        for (const c of cases) {
            assert.ok(!/Error\b/.test(c.message), `"${c.message}" still reads like a stack trace`);
            assert.ok(!/Traceback/.test(c.message));
            assert.ok(c.message.length > 0);
        }
    });
    test('the raw technical text is never thrown away -- it is always in `detail`', () => {
        const raw = "FileNotFoundError: [Errno 2] No such file or directory: '/tmp/x.csv'";
        const error = (0, friendlyError_1.explainBridgeError)(raw);
        assert.ok(error.detail?.includes(raw));
    });
    test('an unrecognised error still gets a plain-language message plus the raw detail, never crashes', () => {
        const error = (0, friendlyError_1.explainBridgeError)('some brand new exception type nobody has seen before');
        assert.ok(error.message.length > 0);
        assert.ok(error.detail);
    });
    test('the sail-missing message tells the user the actual fix (pip install)', () => {
        const error = (0, friendlyError_1.explainSailMissing)('/usr/bin/python3', "No module named 'sail'");
        assert.ok(error.detail?.includes('pip install sail-leakage'));
    });
});
suite('exported HTML report (pure)', () => {
    const cards = [
        { id: 'c1', name: 'Construction leakage', question: 'Q1?', status: 'flagged', explanation: 'E1 <script>', fix: 'Fix 1' },
        { id: 'c2', name: 'Reconstruction leakage', question: 'Q2?', status: 'passed', explanation: 'E2', fix: 'Fix 2' },
    ];
    test('counts flagged checks correctly in the headline', () => {
        const html = (0, reportHtml_1.buildReportHtml)({ datasetLabel: 'cohort.csv', isExample: false, cards });
        assert.ok(html.includes('1 of 2 checks found leakage'));
    });
    test('every check name and its real explanation appear in the output', () => {
        const html = (0, reportHtml_1.buildReportHtml)({ datasetLabel: 'cohort.csv', isExample: false, cards });
        for (const c of cards) {
            assert.ok(html.includes((0, reportHtml_1.escapeHtml)(c.name)), c.name);
        }
    });
    test('dataset names and explanations are escaped, so a stray "<script>" cannot inject markup', () => {
        const html = (0, reportHtml_1.buildReportHtml)({ datasetLabel: '<img onerror=alert(1)>.csv', isExample: false, cards });
        assert.ok(!html.includes('<img onerror'));
        assert.ok(!html.includes('E1 <script>'));
        assert.ok(html.includes('E1 &lt;script&gt;'));
    });
    test('the example-data disclaimer appears only when isExample is true', () => {
        const withExample = (0, reportHtml_1.buildReportHtml)({ datasetLabel: 'x', isExample: true, cards });
        const without = (0, reportHtml_1.buildReportHtml)({ datasetLabel: 'x', isExample: false, cards });
        assert.ok(withExample.includes('not real results'));
        assert.ok(!without.includes('not real results'));
    });
    test('is self-contained: no external network requests', () => {
        const html = (0, reportHtml_1.buildReportHtml)({ datasetLabel: 'x', isExample: false, cards });
        assert.ok(!/https?:\/\//.test(html), 'the exported report must not reference any external URL');
        assert.ok(!html.includes('<script'), 'the exported report must not run any script');
    });
});
suite('inconclusive findings (pure)', () => {
    test('an inconclusive, unflagged finding is "not-run", never "passed"', () => {
        const s = (0, wizardModel_1.mapReportToStatuses)({ findings: [{ category: 'construction_leakage', flagged: false, inconclusive: true }], skipped: {} }, { c1: true });
        assert.strictEqual(s.c1, 'not-run');
    });
    test('a flagged finding stays flagged even if marked inconclusive', () => {
        const s = (0, wizardModel_1.mapReportToStatuses)({ findings: [{ category: 'construction_leakage', flagged: true, inconclusive: true }], skipped: {} }, { c1: true });
        assert.strictEqual(s.c1, 'flagged');
    });
});
//# sourceMappingURL=wizardModel.test.js.map
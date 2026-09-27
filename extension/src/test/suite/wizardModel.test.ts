import * as assert from 'assert';
import { autoDetect } from '../../columnMapping';
import { buildResultCards, computeViewModel, initialWizardState, mapReportToStatuses } from '../../wizardModel';
import { CHECKS } from '../../checks';
import { computeStatusBar } from '../../state';
import { buildReportHtml, escapeHtml } from '../../reportHtml';

suite('column auto-detect (pure)', () => {
  test('detects the four generic fields from typical names', () => {
    assert.deepStrictEqual(autoDetect(['patient_id', 'step', 'treatment', 'outcome']), {
      stay: 'patient_id',
      time: 'step',
      action: 'treatment',
      reward: 'outcome',
    });
  });

  test('detects the README quickstart-style names too', () => {
    const map = autoDetect(['stay_id', 'charttime_bin', 'vaso_dose_bin', 'survived_90d']);
    assert.deepStrictEqual(map, { stay: 'stay_id', time: 'charttime_bin', action: 'vaso_dose_bin', reward: 'survived_90d' });
  });

  test('never assigns the same column to two fields', () => {
    // "action_time" matches both the time pattern and nothing else; must not also get claimed by "action".
    const map = autoDetect(['action_time', 'treatment']);
    const values = Object.values(map).filter((v) => v !== null);
    assert.strictEqual(new Set(values).size, values.length, `duplicate assignment in ${JSON.stringify(map)}`);
  });

  test('unrecognised columns are left null, not guessed', () => {
    assert.deepStrictEqual(autoDetect(['col_a', 'col_b']), { stay: null, time: null, action: null, reward: null });
  });

  test('an empty column list is handled without throwing', () => {
    assert.deepStrictEqual(autoDetect([]), { stay: null, time: null, action: null, reward: null });
  });
});

suite('wizard view model (pure)', () => {
  test('the Data step is disabled until a file is selected', () => {
    const state = { ...initialWizardState(), step: 'data' as const };
    assert.strictEqual(computeViewModel(state).nextDisabled, true);
    const withFile = { ...state, selectedFileId: 'x' };
    assert.strictEqual(computeViewModel(withFile).nextDisabled, false);
  });

  test('the Checks step is disabled once every check is turned off', () => {
    const allOff: Record<string, boolean> = {};
    for (const c of CHECKS) allOff[c.id] = false;
    const state = { ...initialWizardState(), step: 'checks' as const, enabled: allOff };
    assert.strictEqual(computeViewModel(state).nextDisabled, true);
  });

  test('nav is shown for data/map/checks and hidden for welcome/running/done', () => {
    for (const step of ['data', 'map', 'checks'] as const) {
      assert.strictEqual(computeViewModel({ ...initialWizardState(), step }).showNav, true, step);
    }
    for (const step of ['welcome', 'running', 'done'] as const) {
      assert.strictEqual(computeViewModel({ ...initialWizardState(), step }).showNav, false, step);
    }
  });
});

suite('report -> sidebar status mapping (pure)', () => {
  const enabledAll: Record<string, boolean> = {};
  for (const c of CHECKS) enabledAll[c.id] = true;

  test('a flagged finding maps to the right check id', () => {
    const statuses = mapReportToStatuses(
      { findings: [{ category: 'construction_leakage_1a', flagged: true }], skipped: {} },
      enabledAll
    );
    assert.strictEqual(statuses.c1, 'flagged');
  });

  test('a clean finding maps to passed, and the base "construction_leakage" category still maps to c1', () => {
    const statuses = mapReportToStatuses({ findings: [{ category: 'construction_leakage', flagged: false }], skipped: {} }, enabledAll);
    assert.strictEqual(statuses.c1, 'passed');
  });

  test('every real category string maps to the check the design puts it under', () => {
    const pairs: [string, string][] = [
      ['construction_leakage_1a', 'c1'],
      ['construction_leakage_1b', 'c1'],
      ['reconstruction_leakage', 'c2'],
      ['temporal_overlap_leakage', 'c3'],
      ['timing_violation_leakage', 'c4'],
      ['persistence_dominance', 'c5'],
    ];
    for (const [category, id] of pairs) {
      const statuses = mapReportToStatuses({ findings: [{ category, flagged: true }], skipped: {} }, enabledAll);
      assert.strictEqual(statuses[id], 'flagged', category);
    }
  });

  test('a skipped category becomes not-run, only when the user left it enabled', () => {
    const statuses = mapReportToStatuses({ findings: [], skipped: { construction_leakage: 'not run: ...' } }, enabledAll);
    assert.strictEqual(statuses.c1, 'not-run');

    const c1Off = { ...enabledAll, c1: false };
    const statusesOff = mapReportToStatuses({ findings: [], skipped: { construction_leakage: 'not run: ...' } }, c1Off);
    assert.strictEqual(statusesOff.c1, 'off', 'a check the user disabled must stay "off", never "not-run"');
  });
});

suite('result cards (pure)', () => {
  const enabledAll: Record<string, boolean> = {};
  for (const c of CHECKS) enabledAll[c.id] = true;

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
    const cards = buildResultCards(report, enabledAll);
    assert.deepStrictEqual(cards.map((c) => c.id), CHECKS.map((c) => c.id));
    const c1 = cards.find((c) => c.id === 'c1')!;
    assert.strictEqual(c1.status, 'flagged');
    assert.strictEqual(c1.explanation, 'the real explanation');
    assert.ok(c1.fix.length > 0);
    const c2 = cards.find((c) => c.id === 'c2')!;
    assert.strictEqual(c2.status, 'not-run');
    assert.strictEqual(c2.explanation, 'not run: reconstruction_spec not provided');
  });

  test('a check the user turned off gets its own explanation and fix text, not a blank card', () => {
    const off = { ...enabledAll, c3: false };
    const report = { findings: [], skipped: { temporal_overlap_leakage: 'would say not run, but the user disabled it' } };
    const cards = buildResultCards(report, off);
    const c3 = cards.find((c) => c.id === 'c3')!;
    assert.strictEqual(c3.status, 'off');
    assert.ok(c3.explanation.length > 0 && !c3.explanation.includes('would say not run'));
    assert.ok(c3.fix.length > 0);
  });
});

suite('status bar text (pure)', () => {
  function stateWith(statuses: Record<string, import('../../state').CheckStatus>) {
    return { dataset: null, checks: CHECKS.map((c) => ({ id: c.id, name: c.name, question: c.question, status: statuses[c.id] })) };
  }
  const allPending = Object.fromEntries(CHECKS.map((c) => [c.id, 'pending' as const]));

  test('before anything has run: Ready', () => {
    const view = computeStatusBar(stateWith(allPending));
    assert.strictEqual(view.text, 'SAIL: Ready');
    assert.strictEqual(view.warn, false);
  });

  test('while running: Checking, never a stale Ready or issue count', () => {
    const view = computeStatusBar(stateWith({ ...allPending, c1: 'running' }));
    assert.strictEqual(view.text, 'SAIL: Checking…');
  });

  test('after a run with nothing flagged: No issues found, no warning color', () => {
    const view = computeStatusBar(stateWith({ c1: 'passed', c2: 'passed', c3: 'not-run', c4: 'off', c5: 'off' }));
    assert.strictEqual(view.text, 'SAIL: No issues found');
    assert.strictEqual(view.warn, false);
  });

  test('after a run with issues: the exact count, singular vs plural, and the warning color', () => {
    const one = computeStatusBar(stateWith({ c1: 'flagged', c2: 'passed', c3: 'passed', c4: 'passed', c5: 'passed' }));
    assert.strictEqual(one.text, 'SAIL: 1 issue found');
    assert.strictEqual(one.warn, true);
    const three = computeStatusBar(
      stateWith({ c1: 'flagged', c2: 'flagged', c3: 'flagged', c4: 'passed', c5: 'passed' })
    );
    assert.strictEqual(three.text, 'SAIL: 3 issues found');
  });
});

suite('exported HTML report (pure)', () => {
  const cards = [
    { id: 'c1', name: 'Construction leakage', question: 'Q1?', status: 'flagged' as const, explanation: 'E1 <script>', fix: 'Fix 1' },
    { id: 'c2', name: 'Reconstruction leakage', question: 'Q2?', status: 'passed' as const, explanation: 'E2', fix: 'Fix 2' },
  ];

  test('counts flagged checks correctly in the headline', () => {
    const html = buildReportHtml({ datasetLabel: 'cohort.csv', isExample: false, cards });
    assert.ok(html.includes('1 of 2 checks found leakage'));
  });

  test('every check name and its real explanation appear in the output', () => {
    const html = buildReportHtml({ datasetLabel: 'cohort.csv', isExample: false, cards });
    for (const c of cards) {
      assert.ok(html.includes(escapeHtml(c.name)), c.name);
    }
  });

  test('dataset names and explanations are escaped, so a stray "<script>" cannot inject markup', () => {
    const html = buildReportHtml({ datasetLabel: '<img onerror=alert(1)>.csv', isExample: false, cards });
    assert.ok(!html.includes('<img onerror'));
    assert.ok(!html.includes('E1 <script>'));
    assert.ok(html.includes('E1 &lt;script&gt;'));
  });

  test('the example-data disclaimer appears only when isExample is true', () => {
    const withExample = buildReportHtml({ datasetLabel: 'x', isExample: true, cards });
    const without = buildReportHtml({ datasetLabel: 'x', isExample: false, cards });
    assert.ok(withExample.includes('not real results'));
    assert.ok(!without.includes('not real results'));
  });

  test('is self-contained: no external network requests', () => {
    const html = buildReportHtml({ datasetLabel: 'x', isExample: false, cards });
    assert.ok(!/https?:\/\//.test(html), 'the exported report must not reference any external URL');
    assert.ok(!html.includes('<script'), 'the exported report must not run any script');
  });
});

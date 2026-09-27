import * as assert from 'assert';
import { autoDetect } from '../../columnMapping';
import { computeViewModel, initialWizardState, mapReportToStatuses } from '../../wizardModel';
import { CHECKS } from '../../checks';

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

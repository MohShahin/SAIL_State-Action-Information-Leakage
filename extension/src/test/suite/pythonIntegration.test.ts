import * as assert from 'assert';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import * as vscode from 'vscode';
import type { SailTestApi } from '../../extension';
import { callBridge, CheckReportData, ColumnsData } from '../../sailBridge';
import { resolvePython, verifySail } from '../../pythonRuntime';

const EXTENSION_ID = 'mohshahin.sail-leakage-checks';

/**
 * These tests call a REAL Python process running the REAL, installed `sail-leakage` package -- nothing
 * here is mocked. They need an interpreter that has it installed, which a bare checkout does not have,
 * so the suite looks for one exactly the way the extension itself would (via `sail.pythonPath`, honoring
 * SAIL_TEST_PYTHON if the environment sets it) and SKIPS with a clear message if none is found, rather
 * than failing. To run them: SAIL_TEST_PYTHON=/path/to/python/with/sail-leakage npm test
 */
suite('Python bridge (real sail-leakage, skips if none is configured)', function () {
  this.timeout(60000);
  let pythonPath: string | null = null;
  let bridgeScript: string;

  suiteSetup(async function () {
    const extension = vscode.extensions.getExtension<SailTestApi>(EXTENSION_ID)!;
    bridgeScript = path.join(extension.extensionPath, 'python', 'sail_bridge.py');

    if (process.env.SAIL_TEST_PYTHON) {
      await vscode.workspace
        .getConfiguration('sail')
        .update('pythonPath', process.env.SAIL_TEST_PYTHON, vscode.ConfigurationTarget.Global);
    }
    const found = await resolvePython();
    if (!found) {
      console.log('  (skipping: no Python interpreter found -- set SAIL_TEST_PYTHON to run these tests)');
      this.skip();
      return;
    }
    const probe = await verifySail(found);
    if (!probe.ok) {
      console.log(`  (skipping: sail-leakage not importable under "${found}": ${probe.message})`);
      this.skip();
      return;
    }
    pythonPath = found;
    console.log(`  using Python "${found}" (sail-leakage ${probe.version})`);
  });

  test('check_example reproduces the README quickstart result exactly (3 flagged, 2 not flagged)', async () => {
    const result = await callBridge<CheckReportData>(pythonPath!, bridgeScript, { cmd: 'check_example' });
    assert.ok(result.ok, !result.ok ? result.error : '');
    if (!result.ok) return;
    const flagged = result.data.findings.filter((f) => f.flagged);
    const passed = result.data.findings.filter((f) => !f.flagged);
    assert.strictEqual(flagged.length, 3, JSON.stringify(result.data.findings));
    assert.strictEqual(passed.length, 2, JSON.stringify(result.data.findings));
    assert.deepStrictEqual(Object.keys(result.data.skipped), []);
  });

  test('check_example honors a disabled check: turning c5 off reports it as skipped, not run', async () => {
    const enabled = { c1: true, c2: true, c3: true, c4: true, c5: false };
    const result = await callBridge<CheckReportData>(pythonPath!, bridgeScript, { cmd: 'check_example', checks: enabled });
    assert.ok(result.ok, !result.ok ? result.error : '');
    if (!result.ok) return;
    assert.ok(!result.data.findings.some((f) => f.category === 'persistence_dominance'));
    assert.ok('persistence_dominance' in result.data.skipped);
  });

  test('columns + check on an arbitrary generic file: reads real headers, and honestly reports "not run"', async () => {
    // Synthetic values only, matching the shape the wizard's four generic fields expect.
    const csv = 'patient_id,step,treatment,outcome\n1,0,0,0\n1,1,1,0\n2,0,0,1\n';
    const tmp = path.join(os.tmpdir(), `sail-wizard-test-${Date.now()}.csv`);
    fs.writeFileSync(tmp, csv, 'utf8');
    try {
      const columns = await callBridge<ColumnsData>(pythonPath!, bridgeScript, { cmd: 'columns', path: tmp });
      assert.ok(columns.ok, !columns.ok ? columns.error : '');
      if (columns.ok) {
        assert.deepStrictEqual(columns.data.columns, ['patient_id', 'step', 'treatment', 'outcome']);
        assert.strictEqual(columns.data.nRows, 3);
      }

      const checked = await callBridge<CheckReportData>(pythonPath!, bridgeScript, {
        cmd: 'check',
        path: tmp,
        map: { stay: 'patient_id', time: 'step', action: 'treatment', reward: 'outcome' },
      });
      assert.ok(checked.ok, !checked.ok ? checked.error : '');
      if (checked.ok) {
        // Honest, not impressive: four generic column names are not enough for any of the five
        // categories, and sail.check() must say so rather than guess.
        assert.strictEqual(checked.data.findings.length, 0);
        assert.strictEqual(Object.keys(checked.data.skipped).length, 5);
      }
    } finally {
      fs.unlinkSync(tmp);
    }
  });

  test('end-to-end through the real extension: wizardDispatch("useDemo") updates the shared app state', async () => {
    const extension = vscode.extensions.getExtension<SailTestApi>(EXTENSION_ID)!;
    const api = await extension.activate();
    await api.wizardDispatch('useDemo');

    const deadline = Date.now() + 30000;
    while (Date.now() < deadline) {
      const state = api.appState();
      if (state.checks.every((c) => c.status !== 'running' && c.status !== 'pending')) {
        break;
      }
      await new Promise((r) => setTimeout(r, 200));
    }

    const state = api.appState();
    assert.strictEqual(state.dataset, 'Example data (synthetic)');
    const byId = Object.fromEntries(state.checks.map((c) => [c.id, c.status]));
    // The real, verified quickstart result (matches SAIL_PACKAGE_README.md's own output exactly):
    // construction, reconstruction and persistence-dominance flagged; temporal-overlap and timing not.
    assert.deepStrictEqual(byId, { c1: 'flagged', c2: 'flagged', c3: 'passed', c4: 'passed', c5: 'flagged' });
  });
});

import * as assert from 'assert';
import * as vscode from 'vscode';
import type { SailTestApi } from '../../extension';
import { CHECKS } from '../../checks';

const EXTENSION_ID = 'mohshahin.sail-leakage-checks';

async function waitFor(condition: () => boolean, what: string, timeoutMs = 15000): Promise<void> {
  const start = Date.now();
  while (!condition()) {
    if (Date.now() - start > timeoutMs) {
      throw new Error(`Timed out waiting for ${what}`);
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
}

suite('SAIL extension skeleton', () => {
  let api: SailTestApi;

  suiteSetup(async () => {
    const extension = vscode.extensions.getExtension<SailTestApi>(EXTENSION_ID);
    assert.ok(extension, `extension ${EXTENSION_ID} is not installed in the test host`);
    api = await extension.activate();
  });

  test('the status bar item reads "SAIL: Ready"', () => {
    assert.strictEqual(api.statusText(), 'SAIL: Ready');
  });

  test('contributes a SAIL activity bar container holding the Leakage Checks view', () => {
    const contributes = vscode.extensions.getExtension(EXTENSION_ID)!.packageJSON.contributes;
    const container = contributes.viewsContainers.activitybar.find((c: { id: string }) => c.id === 'sail');
    assert.ok(container, 'no activity bar container with id "sail"');
    assert.strictEqual(container.title, 'SAIL');
    const views = contributes.views.sail;
    assert.deepStrictEqual(
      views.map((v: { id: string }) => v.id),
      ['sail.sidebar']
    );
  });

  test('the "SAIL: Show Leakage Checks" command exists', async () => {
    const commands = await vscode.commands.getCommands(true);
    assert.ok(commands.includes('sail.focus'));
  });

  test('running the command opens the sidebar', async () => {
    await vscode.commands.executeCommand('sail.focus');
    await waitFor(() => api.sidebarResolved(), 'the SAIL sidebar to open');
  });

  test('the five checks are listed in the design order', () => {
    assert.deepStrictEqual(
      CHECKS.map((c) => c.name),
      [
        'Construction leakage',
        'Reconstruction leakage',
        'Temporal overlap',
        'Timing violation',
        'Persistence dominance',
      ]
    );
  });
});

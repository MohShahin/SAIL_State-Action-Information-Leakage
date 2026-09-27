import * as assert from 'assert';
import * as fs from 'fs';
import * as path from 'path';
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
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
}

suite('SAIL extension', () => {
  let api: SailTestApi;
  let root: string;
  let manifest: any;

  suiteSetup(async () => {
    const extension = vscode.extensions.getExtension<SailTestApi>(EXTENSION_ID);
    assert.ok(extension, `extension ${EXTENSION_ID} is not installed in the test host`);
    api = await extension.activate();
    root = extension.extensionPath;
    manifest = extension.packageJSON;
  });

  suite('startup', () => {
    test('is one bundled file, not a tree of modules', () => {
      assert.strictEqual(manifest.main, './dist/extension.js');
      const dist = fs.readdirSync(path.join(root, 'dist')).filter((f) => !f.endsWith('.map'));
      assert.deepStrictEqual(dist, ['extension.js']);
    });

    test('activates in well under a second', () => {
      assert.ok(api.activationMs() < 1000, `activation took ${api.activationMs()} ms`);
    });

    test('activates after startup, so it never delays the extension host', () => {
      assert.deepStrictEqual(manifest.activationEvents, ['onStartupFinished']);
    });
  });

  suite('status bar and icon', () => {
    test('the status bar item shows the sail icon and "SAIL: Ready"', () => {
      assert.strictEqual(api.statusText(), '$(sail-logo) SAIL: Ready');
    });

    test('the sail icon is contributed as a real icon font that exists on disk', () => {
      const icon = manifest.contributes.icons['sail-logo'];
      assert.ok(icon, 'no "sail-logo" icon contributed');
      const font = path.join(root, icon.default.fontPath);
      const header = fs.readFileSync(font).subarray(0, 4).toString('latin1');
      assert.strictEqual(header, 'wOFF', 'the icon font is not a WOFF file');
    });
  });

  suite('sidebar', () => {
    test('is a webview view in a SAIL activity bar container, movable like any view', () => {
      const container = manifest.contributes.viewsContainers.activitybar.find((c: { id: string }) => c.id === 'sail');
      assert.ok(container, 'no activity bar container with id "sail"');
      assert.strictEqual(container.title, 'SAIL');
      assert.deepStrictEqual(
        manifest.contributes.views.sail.map((v: { id: string; type: string }) => [v.id, v.type]),
        [['sail.sidebar', 'webview']]
      );
    });

    test('opening it shows real content (the loading skeleton is replaced)', async () => {
      await vscode.commands.executeCommand('sail.focus');
      await waitFor(() => api.sidebarResolved(), 'the SAIL sidebar to open');
      await waitFor(() => api.sidebarReady(), 'the sidebar page to load and receive its content');
    });

    test('the loading skeleton and the content never show at the same time', () => {
      // Regression: our own "display: flex" on the content once beat the browser's built-in `hidden`
      // behaviour, so the skeleton and the (empty) content were both on screen until the state arrived.
      const css = fs.readFileSync(path.join(root, 'media', 'sidebar.css'), 'utf8');
      assert.match(css, /\[hidden\]\s*\{\s*display:\s*none\s*!important/);
      const js = fs.readFileSync(path.join(root, 'media', 'sidebar.js'), 'utf8');
      assert.ok(js.includes('app.hidden = false') && js.includes('skeleton.remove()'));
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

  suite('commands and menus', () => {
    test('the Command Palette has "SAIL: Check a dataset" and the other SAIL commands', async () => {
      const titles = new Map<string, string>(manifest.contributes.commands.map((c: any) => [c.command, c.title]));
      assert.strictEqual(titles.get('sail.checkDataset'), 'SAIL: Check a dataset');
      assert.ok(titles.has('sail.focus') && titles.has('sail.openWalkthrough') && titles.has('sail.moveToSecondarySideBar'));
      const registered = await vscode.commands.getCommands(true);
      for (const id of titles.keys()) {
        assert.ok(registered.includes(id), `command ${id} is contributed but not registered`);
      }
      // nothing hides them from the Command Palette
      assert.strictEqual(manifest.contributes.menus.commandPalette, undefined);
    });

    test('there is a SAIL button in the editor title bar', () => {
      const items = manifest.contributes.menus['editor/title'];
      assert.ok(items.some((i: any) => i.command === 'sail.checkDataset' && String(i.group).startsWith('navigation')));
      const command = manifest.contributes.commands.find((c: any) => c.command === 'sail.checkDataset');
      assert.strictEqual(command.icon, '$(sail-logo)');
    });
  });

  suite('walkthrough', () => {
    test('has three steps: choose data, confirm columns, read the report', () => {
      const [walkthrough] = manifest.contributes.walkthroughs;
      assert.strictEqual(walkthrough.id, 'sail.gettingStarted');
      assert.deepStrictEqual(
        walkthrough.steps.map((s: any) => s.title),
        ['Choose your data', 'Confirm the columns', 'Read the report']
      );
      for (const step of walkthrough.steps) {
        assert.ok(fs.existsSync(path.join(root, step.media.image)), `missing image for step ${step.id}`);
        assert.ok(step.media.altText, `step ${step.id} has no alt text`);
      }
    });
  });
});

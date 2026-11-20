import * as os from 'os';
import * as path from 'path';
import * as fs from 'fs';
import { runTests } from '@vscode/test-electron';

/**
 * Starts a real VS Code with this extension loaded and runs suite/index.js inside it.
 * Set VSCODE_EXE to use an already-installed VS Code instead of downloading one.
 */
async function main(): Promise<void> {
  const extensionDevelopmentPath = path.resolve(__dirname, '../../');
  const extensionTestsPath = path.resolve(__dirname, 'suite/index');
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'sail-test-'));

  try {
    await runTests({
      vscodeExecutablePath: process.env.VSCODE_EXE || undefined,
      extensionDevelopmentPath,
      extensionTestsPath,
      // A throwaway profile, so a running VS Code (and its settings) is never touched.
      launchArgs: [
        '--disable-extensions',
        '--disable-workspace-trust',
        '--user-data-dir',
        path.join(profile, 'user'),
        '--extensions-dir',
        path.join(profile, 'ext'),
      ],
    });
  } finally {
    fs.rmSync(profile, { recursive: true, force: true });
  }
}

main().catch((err) => {
  console.error('Extension tests failed:', err);
  process.exit(1);
});

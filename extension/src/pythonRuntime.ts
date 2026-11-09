import * as vscode from 'vscode';
import { runProcess } from './procUtil';

/**
 * Finds a Python interpreter to run the bridge with, and checks that `sail-leakage` is importable
 * under it. Order: the `sail.pythonPath` setting, then the Python extension's selected interpreter (if
 * that extension is installed), then `python3`/`python` on PATH. Nothing here ever installs anything.
 */

async function fromPythonExtension(): Promise<string | null> {
  try {
    const ext = vscode.extensions.getExtension('ms-python.python');
    if (!ext) {
      return null;
    }
    const api = ext.isActive ? ext.exports : await ext.activate();
    const uri = vscode.workspace.workspaceFolders?.[0]?.uri;
    // The Python extension's API has changed shape across versions; try the newer one, then the older
    // one, and give up quietly rather than throw if neither is there.
    const envPath = api?.environments?.getActiveEnvironmentPath?.(uri)?.path;
    if (envPath) {
      return envPath;
    }
    const execCommand = api?.settings?.getExecutionDetails?.(uri)?.execCommand;
    if (Array.isArray(execCommand) && execCommand.length > 0) {
      return execCommand[0];
    }
  } catch {
    // Fall through to a PATH search.
  }
  return null;
}

async function onPath(command: string): Promise<boolean> {
  const r = await runProcess(command, ['--version'], undefined, 5000);
  return !r.timedOut && r.code === 0;
}

export async function resolvePython(): Promise<string | null> {
  const configured = vscode.workspace.getConfiguration('sail').get<string>('pythonPath', '').trim();
  if (configured) {
    return configured;
  }
  const fromExtension = await fromPythonExtension();
  if (fromExtension) {
    return fromExtension;
  }
  for (const candidate of ['python3', 'python']) {
    if (await onPath(candidate)) {
      return candidate;
    }
  }
  return null;
}

export interface SailProbe {
  readonly ok: boolean;
  readonly version?: string;
  readonly stage?: 'python' | 'sail';
  readonly message?: string;
}

const PROBE_CODE =
  "import json,sys\n" +
  "try:\n" +
  " import sail\n" +
  "except Exception as e:\n" +
  " print(json.dumps({'ok': False, 'stage': 'sail', 'message': str(e)})); sys.exit(0)\n" +
  "print(json.dumps({'ok': True, 'version': sail.__version__}))\n";

export async function verifySail(pythonPath: string): Promise<SailProbe> {
  const r = await runProcess(pythonPath, ['-c', PROBE_CODE], undefined, 15000);
  if (r.timedOut) {
    return { ok: false, stage: 'python', message: 'Python did not respond within 15s.' };
  }
  if (r.code !== 0 && !r.stdout.trim()) {
    return { ok: false, stage: 'python', message: (r.stderr || `exit code ${r.code}`).trim().slice(0, 500) };
  }
  try {
    const parsed = JSON.parse(r.stdout.trim().split('\n').pop() ?? '');
    return parsed.ok ? { ok: true, version: parsed.version } : { ok: false, stage: 'sail', message: parsed.message };
  } catch {
    return { ok: false, stage: 'python', message: `Unexpected output: ${(r.stdout || r.stderr).slice(0, 300)}` };
  }
}

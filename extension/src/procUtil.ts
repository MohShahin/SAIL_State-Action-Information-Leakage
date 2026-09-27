import * as cp from 'child_process';

export interface ProcResult {
  readonly code: number | null;
  readonly stdout: string;
  readonly stderr: string;
  readonly timedOut: boolean;
}

/** Runs one process to completion, feeding it `input` on stdin (if given) and collecting both streams. */
export function runProcess(
  command: string,
  args: readonly string[],
  input?: string,
  timeoutMs = 60000
): Promise<ProcResult> {
  return new Promise((resolve) => {
    let child: cp.ChildProcess;
    try {
      child = cp.spawn(command, args as string[], { windowsHide: true });
    } catch (err) {
      resolve({ code: null, stdout: '', stderr: String(err), timedOut: false });
      return;
    }
    let stdout = '';
    let stderr = '';
    let timedOut = false;
    const timer = setTimeout(() => {
      timedOut = true;
      child.kill();
    }, timeoutMs);

    child.stdout?.on('data', (d: Buffer) => (stdout += d.toString('utf8')));
    child.stderr?.on('data', (d: Buffer) => (stderr += d.toString('utf8')));
    child.on('error', (err) => {
      clearTimeout(timer);
      resolve({ code: null, stdout, stderr: stderr || String(err), timedOut });
    });
    child.on('close', (code) => {
      clearTimeout(timer);
      resolve({ code, stdout, stderr, timedOut });
    });

    if (input !== undefined) {
      child.stdin?.write(input, 'utf8');
    }
    child.stdin?.end();
  });
}

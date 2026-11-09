import { runProcess } from './procUtil';

/**
 * Calls `python/sail_bridge.py`: writes one JSON request to its stdin, reads one JSON response from
 * its stdout. The bridge prints a marker line before its actual answer so a stray print from a library
 * (pandas, a warning, ...) earlier in stdout can never be mistaken for the response.
 */
const MARKER = '##SAIL_BRIDGE_RESULT##';

export type BridgeResult<T> = { readonly ok: true; readonly data: T } | { readonly ok: false; readonly error: string };

export async function callBridge<T>(
  pythonPath: string,
  bridgeScriptPath: string,
  payload: unknown,
  timeoutMs = 60000
): Promise<BridgeResult<T>> {
  const r = await runProcess(pythonPath, [bridgeScriptPath], JSON.stringify(payload), timeoutMs);
  if (r.timedOut) {
    return { ok: false, error: `Python did not finish within ${Math.round(timeoutMs / 1000)}s.` };
  }
  const idx = r.stdout.lastIndexOf(MARKER);
  if (idx === -1) {
    const detail = (r.stderr || r.stdout).trim();
    return {
      ok: false,
      error: detail ? detail.slice(0, 2000) : `Python exited with code ${r.code} and produced no output.`,
    };
  }
  try {
    const parsed = JSON.parse(r.stdout.slice(idx + MARKER.length).trim());
    return parsed as BridgeResult<T>;
  } catch {
    return { ok: false, error: 'Could not parse the response from Python.' };
  }
}

export interface ColumnsData {
  readonly columns: readonly string[];
  readonly nRows: number;
}

export interface CheckReportData {
  readonly findings: readonly { category: string; flagged: boolean; explanation: string }[];
  readonly skipped: Readonly<Record<string, string>>;
  readonly summary: string;
}

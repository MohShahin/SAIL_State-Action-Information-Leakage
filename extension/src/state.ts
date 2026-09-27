import { CHECKS } from './checks';

/**
 * How one check row is drawn in the sidebar.
 * pending: waiting to run. running: the wizard is running it right now. flagged/passed: it ran and
 * found (or didn't find) leakage. not-run: it was enabled, but sail.check() didn't have enough input
 * to run it -- distinct from off, which means the user disabled it themselves.
 */
export type CheckStatus = 'pending' | 'running' | 'flagged' | 'passed' | 'not-run' | 'off';

export interface CheckRow {
  readonly id: string;
  readonly name: string;
  readonly question: string;
  readonly status: CheckStatus;
}

/** Everything the sidebar shows. The extension owns it; the webview only draws what it is sent. */
export interface SidebarState {
  /** File name of the chosen dataset, or null before one is chosen. */
  readonly dataset: string | null;
  readonly checks: readonly CheckRow[];
}

export function initialState(): SidebarState {
  return {
    dataset: null,
    checks: CHECKS.map((c) => ({ id: c.id, name: c.name, question: c.question, status: 'pending' as const })),
  };
}

/** Messages the webview may send. Anything else is ignored. */
export type WebviewMessage = { readonly type: 'ready' };

export function isWebviewMessage(value: unknown): value is WebviewMessage {
  return typeof value === 'object' && value !== null && (value as { type?: unknown }).type === 'ready';
}

export interface StatusBarView {
  readonly text: string;
  readonly tooltip: string;
  /** True once something has actually run (as opposed to the pristine pre-run state). */
  readonly settled: boolean;
  /** True when at least one check found leakage -- the status bar highlights this. */
  readonly warn: boolean;
}

/**
 * What the status bar item should show for the current app state. Pure: the same state always produces
 * the same text, so this is testable without a running VS Code or status bar item.
 */
export function computeStatusBar(state: SidebarState): StatusBarView {
  const statuses = state.checks.map((c) => c.status);
  if (statuses.some((s) => s === 'running')) {
    return { text: 'SAIL: Checking…', tooltip: 'SAIL is running your checks.', settled: false, warn: false };
  }
  const settledChecks = state.checks.filter((c) => c.status === 'flagged' || c.status === 'passed' || c.status === 'not-run');
  if (settledChecks.length === 0) {
    return {
      text: 'SAIL: Ready',
      tooltip: 'SAIL leakage checks: ready. Click to open.',
      settled: false,
      warn: false,
    };
  }
  const flagged = settledChecks.filter((c) => c.status === 'flagged').length;
  if (flagged === 0) {
    return {
      text: 'SAIL: No issues found',
      tooltip: `None of the ${settledChecks.length} check(s) that ran found leakage. Click to open the report.`,
      settled: true,
      warn: false,
    };
  }
  const noun = flagged === 1 ? 'issue' : 'issues';
  return {
    text: `SAIL: ${flagged} ${noun} found`,
    tooltip: `${flagged} of ${settledChecks.length} check(s) that ran found leakage. Click to open the report.`,
    settled: true,
    warn: true,
  };
}

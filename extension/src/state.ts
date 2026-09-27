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

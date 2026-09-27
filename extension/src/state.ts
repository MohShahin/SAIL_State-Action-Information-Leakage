import { CHECKS } from './checks';

/** How one check row is drawn in the sidebar. Later phases move checks through these as they run. */
export type CheckStatus = 'pending' | 'running' | 'done' | 'flagged' | 'passed' | 'off';

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

import * as vscode from 'vscode';
import { CheckStatus, initialState, SidebarState } from './state';

/**
 * The one place the sidebar's DATASET and CHECKS actually live. Both the sidebar webview and the setup
 * wizard read and write through this, so they can never disagree about what has been chosen or run.
 */
export class AppStateStore {
  private state: SidebarState = initialState();
  private readonly emitter = new vscode.EventEmitter<SidebarState>();
  readonly onDidChange = this.emitter.event;

  get(): SidebarState {
    return this.state;
  }

  setDataset(name: string | null): void {
    this.state = { ...this.state, dataset: name };
    this.emitter.fire(this.state);
  }

  setCheckStatus(id: string, status: CheckStatus): void {
    this.state = {
      ...this.state,
      checks: this.state.checks.map((c) => (c.id === id ? { ...c, status } : c)),
    };
    this.emitter.fire(this.state);
  }

  /** About to run: the given ids go to 'running', everything else to 'off'. */
  markRunning(idsToRun: ReadonlySet<string>): void {
    this.state = {
      ...this.state,
      checks: this.state.checks.map((c) => ({ ...c, status: idsToRun.has(c.id) ? 'running' : 'off' })),
    };
    this.emitter.fire(this.state);
  }
}

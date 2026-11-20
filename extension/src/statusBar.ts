import * as vscode from 'vscode';
import { AppStateStore } from './appState';
import { computeStatusBar } from './state';

/**
 * The status bar item on the right: the sail mark plus a short status. `$(sail-logo)` is the icon this
 * extension contributes (see "icons" in package.json). The text itself comes from `computeStatusBar`,
 * so what shows here is always exactly derivable from the same state the sidebar draws.
 */
export class SailStatusBar implements vscode.Disposable {
  private readonly item: vscode.StatusBarItem;
  private readonly subscription: vscode.Disposable;

  constructor(store: AppStateStore, command: string) {
    this.item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    this.item.name = 'SAIL';
    this.item.command = command;
    this.render(store);
    this.item.show();
    this.subscription = store.onDidChange(() => this.render(store));
  }

  get text(): string {
    return this.item.text;
  }

  private render(store: AppStateStore): void {
    const view = computeStatusBar(store.get());
    this.item.text = `$(sail-logo) ${view.text}`;
    this.item.tooltip = view.tooltip;
    this.item.backgroundColor = view.warn ? new vscode.ThemeColor('statusBarItem.warningBackground') : undefined;
    this.item.accessibilityInformation = { label: `${view.text}. Activate to open the report.`, role: 'button' };
  }

  dispose(): void {
    this.subscription.dispose();
    this.item.dispose();
  }
}

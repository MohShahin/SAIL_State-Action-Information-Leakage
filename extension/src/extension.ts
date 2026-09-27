import * as vscode from 'vscode';
import { SidebarProvider } from './sidebar';
import { SailStatusBar } from './statusBar';

const OPEN_COMMAND = 'sail.focus';

/** What the integration tests can inspect. Not a public API. */
export interface SailTestApi {
  sidebarResolved(): boolean;
  statusText(): string;
}

export function activate(context: vscode.ExtensionContext): SailTestApi {
  const sidebar = new SidebarProvider(context.extensionUri);
  const status = new SailStatusBar(OPEN_COMMAND);

  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(SidebarProvider.viewType, sidebar),
    vscode.commands.registerCommand(OPEN_COMMAND, () =>
      vscode.commands.executeCommand('workbench.view.extension.sail')
    ),
    status
  );

  return {
    sidebarResolved: () => sidebar.isResolved,
    statusText: () => status.text,
  };
}

export function deactivate(): void {}

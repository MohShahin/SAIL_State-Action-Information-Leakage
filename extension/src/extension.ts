import * as vscode from 'vscode';
import { SidebarProvider } from './sidebar';
import { SailStatusBar } from './statusBar';

const EXTENSION_ID = 'mohshahin.sail-leakage-checks';
const FOCUS = 'sail.focus';
const CHECK_DATASET = 'sail.checkDataset';

/** What the integration tests can inspect. Not a public API. */
export interface SailTestApi {
  sidebarResolved(): boolean;
  sidebarReady(): boolean;
  statusText(): string;
  activationMs(): number;
}

export function activate(context: vscode.ExtensionContext): SailTestApi {
  const started = Date.now();
  const log = vscode.window.createOutputChannel('SAIL', { log: true });
  const sidebar = new SidebarProvider(context.extensionUri, log);
  const status = new SailStatusBar(FOCUS);

  const openSidebar = () => vscode.commands.executeCommand('workbench.view.extension.sail');

  context.subscriptions.push(
    log,
    status,
    vscode.window.registerWebviewViewProvider(SidebarProvider.viewType, sidebar),
    vscode.commands.registerCommand(FOCUS, openSidebar),
    vscode.commands.registerCommand(CHECK_DATASET, async () => {
      await openSidebar();
      // The setup wizard arrives in the next phase; be honest about it instead of doing nothing.
      void vscode.window.showInformationMessage(
        'SAIL: the dataset setup wizard is coming in the next build. Nothing was run.'
      );
    }),
    vscode.commands.registerCommand('sail.openWalkthrough', () =>
      vscode.commands.executeCommand('workbench.action.openWalkthrough', `${EXTENSION_ID}#sail.gettingStarted`, false)
    ),
    vscode.commands.registerCommand('sail.moveToSecondarySideBar', async () => {
      // VS Code's own "Move View" flow: first pick the view, then pick where it goes. Say which to choose.
      // (Dragging the SAIL icon from the activity bar to the other side of the window does the same.)
      vscode.window.setStatusBarMessage('SAIL: choose "Leakage Checks", then "Secondary Side Bar"', 15000);
      await vscode.commands.executeCommand('workbench.action.moveView');
    })
  );

  const activationMs = Date.now() - started;
  log.info(`SAIL activated in ${activationMs} ms`);

  return {
    sidebarResolved: () => sidebar.isResolved,
    sidebarReady: () => sidebar.isReady,
    statusText: () => status.text,
    activationMs: () => activationMs,
  };
}

export function deactivate(): void {}

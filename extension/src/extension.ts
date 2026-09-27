import * as vscode from 'vscode';
import { AppStateStore } from './appState';
import { SidebarProvider } from './sidebar';
import { SidebarState } from './state';
import { SailStatusBar } from './statusBar';
import { WizardPanel } from './wizard';

const EXTENSION_ID = 'mohshahin.sail-leakage-checks';
const FOCUS = 'sail.focus';
const CHECK_DATASET = 'sail.checkDataset';

/** What the integration tests can inspect. Not a public API. */
export interface SailTestApi {
  sidebarResolved(): boolean;
  sidebarReady(): boolean;
  statusText(): string;
  activationMs(): number;
  /** Opens the wizard (if not already open) and dispatches one action to it, as if a button had been clicked. */
  wizardDispatch(name: string, payload?: unknown): Promise<void>;
  /** The single shared state the sidebar and the wizard both read and write. */
  appState(): SidebarState;
}

export function activate(context: vscode.ExtensionContext): SailTestApi {
  const started = Date.now();
  const log = vscode.window.createOutputChannel('SAIL', { log: true });
  const store = new AppStateStore();
  const sidebar = new SidebarProvider(context.extensionUri, log, store);
  const status = new SailStatusBar(FOCUS);
  let wizard: WizardPanel | undefined;

  const openSidebar = () => vscode.commands.executeCommand('workbench.view.extension.sail');
  const openWizard = () => {
    wizard = WizardPanel.createOrShow(context.extensionUri, store, log);
    return wizard;
  };

  context.subscriptions.push(
    log,
    status,
    vscode.window.registerWebviewViewProvider(SidebarProvider.viewType, sidebar),
    vscode.commands.registerCommand(FOCUS, openSidebar),
    vscode.commands.registerCommand(CHECK_DATASET, openWizard),
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
    wizardDispatch: async (name, payload) => {
      const w = wizard ?? openWizard();
      await w.dispatchForTest(name, payload);
    },
    appState: () => store.get(),
  };
}

export function deactivate(): void {}

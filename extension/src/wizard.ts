import * as path from 'path';
import * as vscode from 'vscode';
import { AppStateStore } from './appState';
import { autoDetect } from './columnMapping';
import { CHECKS } from './checks';
import {
  buildResultCards,
  computeViewModel,
  DataFile,
  initialWizardState,
  mapReportToStatuses,
  ReportLikeWithText,
  ResultCard,
  WizardState,
} from './wizardModel';
import { resolvePython, verifySail } from './pythonRuntime';
import { BridgeResult, callBridge, CheckReportData, ColumnsData } from './sailBridge';
import { buildReportHtml } from './reportHtml';
import { explainBridgeError, explainPythonError, explainPythonMissing, explainSailMissing, explainSaveError } from './friendlyError';

/**
 * The three-step setup wizard, in an editor tab (a WebviewPanel, not the sidebar). One panel at a time:
 * calling `createOrShow` again reveals the existing one instead of opening a second.
 *
 * Same handshake as the sidebar (webview posts 'ready', extension answers), and the same one-way rule:
 * the webview only draws the view model it is sent and only ever posts back a user action.
 */
export class WizardPanel {
  private static current: WizardPanel | undefined;

  static createOrShow(extensionUri: vscode.Uri, store: AppStateStore, log: vscode.LogOutputChannel): WizardPanel {
    if (WizardPanel.current) {
      WizardPanel.current.panel.reveal();
      return WizardPanel.current;
    }
    const panel = vscode.window.createWebviewPanel('sail.wizard', 'SAIL: New check', vscode.ViewColumn.Active, {
      enableScripts: true,
      retainContextWhenHidden: true,
      localResourceRoots: [vscode.Uri.joinPath(extensionUri, 'media')],
    });
    const instance = new WizardPanel(panel, extensionUri, store, log);
    WizardPanel.current = instance;
    panel.onDidDispose(() => {
      if (WizardPanel.current === instance) {
        WizardPanel.current = undefined;
      }
    });
    return instance;
  }

  /** True and revealed if a wizard panel is already open; false (does nothing) otherwise. */
  static revealIfOpen(): boolean {
    if (WizardPanel.current) {
      WizardPanel.current.panel.reveal();
      return true;
    }
    return false;
  }

  private state: WizardState = initialWizardState();
  private pythonPath: string | null = null;
  // Guards against posting to the webview before its script has attached a message listener (the same
  // race the sidebar's ready-handshake exists to prevent) -- state changes before 'ready' still apply,
  // they just aren't pushed until the page can actually receive them.
  private ready = false;

  private constructor(
    private readonly panel: vscode.WebviewPanel,
    private readonly extensionUri: vscode.Uri,
    private readonly store: AppStateStore,
    private readonly log: vscode.LogOutputChannel
  ) {
    const media = vscode.Uri.joinPath(extensionUri, 'media');
    this.panel.webview.html = this.render(this.panel.webview, media);
    this.panel.webview.onDidReceiveMessage((message: unknown) => {
      void this.handle(message);
    });
  }

  /** Test-only: dispatch an action exactly as if the webview had posted it. Never called by real UI code. */
  dispatchForTest(name: string, payload?: unknown): Promise<void> {
    return this.handle({ type: 'action', name, payload });
  }

  /** Test-only: the real results of the most recent run, for verifying report generation against a
   * real run's actual data without scripting the native save dialog. Never called by real UI code. */
  stateForTest(): Pick<WizardState, 'results' | 'datasetLabel' | 'isExample' | 'error' | 'step' | 'files' | 'selectedFileId'> {
    return {
      results: this.state.results,
      datasetLabel: this.state.datasetLabel,
      isExample: this.state.isExample,
      error: this.state.error,
      step: this.state.step,
      files: this.state.files,
      selectedFileId: this.state.selectedFileId,
    };
  }

  private push(): void {
    if (!this.ready) {
      return;
    }
    void this.panel.webview.postMessage({ type: 'wizardState', viewModel: computeViewModel(this.state) });
  }

  private setState(patch: Partial<WizardState>): void {
    this.state = { ...this.state, ...patch };
    this.push();
  }

  private bridgeScript(): string {
    return path.join(this.extensionUri.fsPath, 'python', 'sail_bridge.py');
  }

  private async ensurePython(): Promise<string | null> {
    if (this.pythonPath) {
      return this.pythonPath;
    }
    const found = await resolvePython();
    if (!found) {
      this.setState({ error: explainPythonMissing(['python3', 'python']) });
      return null;
    }
    const probe = await verifySail(found);
    if (!probe.ok) {
      const error =
        probe.stage === 'sail'
          ? explainSailMissing(found, probe.message ?? '')
          : explainPythonError(found, probe.message ?? '');
      this.setState({ error });
      return null;
    }
    this.log.info(`using Python at "${found}" (sail-leakage ${probe.version})`);
    this.pythonPath = found;
    return found;
  }

  private async discoverFiles(): Promise<DataFile[]> {
    const uris = await vscode.workspace.findFiles('**/*.{csv,parquet}', '**/{node_modules,.git,out,dist}/**', 25);
    return uris.map((u) => ({ id: u.fsPath, name: path.basename(u.fsPath), detail: vscode.workspace.asRelativePath(u) }));
  }

  private async handle(message: unknown): Promise<void> {
    const m = message as { type?: string; name?: string; payload?: any } | undefined;
    if (!m || m.type !== 'action' || typeof m.name !== 'string') {
      return;
    }
    switch (m.name) {
      case 'ready':
        this.ready = true;
        this.push();
        return;
      case 'goData': {
        const files = await this.discoverFiles();
        this.setState({ error: null, step: 'data', files });
        return;
      }
      case 'useDemo': {
        this.setState({ error: null, isExample: true, step: 'running' });
        await this.runExample();
        return;
      }
      case 'browse': {
        const picked = await vscode.window.showOpenDialog({
          canSelectMany: false,
          filters: { 'Data files': ['csv', 'parquet'] },
        });
        if (!picked?.length) {
          return;
        }
        const uri = picked[0];
        const file: DataFile = { id: uri.fsPath, name: path.basename(uri.fsPath), detail: uri.fsPath };
        this.setState({
          error: null,
          files: [file, ...this.state.files.filter((f) => f.id !== file.id)],
          selectedFileId: file.id,
        });
        return;
      }
      case 'pickFile':
        this.setState({ error: null, selectedFileId: m.payload?.id ?? null });
        return;
      case 'back':
        this.goBack();
        return;
      case 'next':
        await this.goNext();
        return;
      case 'changeField':
        this.setState({ error: null, map: { ...this.state.map, [m.payload.field]: m.payload.value } });
        return;
      case 'toggleCheck':
        this.setState({ enabled: { ...this.state.enabled, [m.payload.id]: !this.state.enabled[m.payload.id] } });
        return;
      case 'selectResult':
        this.setState({ selectedResultId: m.payload?.id ?? null });
        return;
      case 'exportReport':
        await this.exportReport();
        return;
      case 'restart':
        this.setState({ ...initialWizardState(), step: 'data', files: this.state.files });
        return;
    }
  }

  private async exportReport(): Promise<void> {
    if (!this.state.results) {
      return;
    }
    const target = await vscode.window.showSaveDialog({
      filters: { 'Web page': ['html'] },
      defaultUri: vscode.Uri.file('sail-report.html'),
    });
    if (!target) {
      return;
    }
    const html = buildReportHtml({
      datasetLabel: this.state.datasetLabel,
      isExample: this.state.isExample,
      cards: this.state.results,
    });
    try {
      await vscode.workspace.fs.writeFile(target, Buffer.from(html, 'utf8'));
    } catch (err) {
      this.setState({ error: explainSaveError(String(err)) });
      return;
    }
    const openIt = 'Open in Browser';
    const choice = await vscode.window.showInformationMessage(`Report saved to ${target.fsPath}`, openIt);
    if (choice === openIt) {
      await vscode.env.openExternal(target);
    }
  }

  private goBack(): void {
    const order: WizardState['step'][] = ['welcome', 'data', 'map', 'checks'];
    const i = order.indexOf(this.state.step);
    if (i > 0) {
      this.setState({ step: order[i - 1], error: null });
    }
  }

  private async goNext(): Promise<void> {
    if (this.state.step === 'data') {
      const file = this.state.files.find((f) => f.id === this.state.selectedFileId);
      if (!file) {
        return;
      }
      const python = await this.ensurePython();
      if (!python) {
        return;
      }
      const result = await callBridge<ColumnsData>(python, this.bridgeScript(), { cmd: 'columns', path: file.id });
      if (!result.ok) {
        this.setState({ error: explainBridgeError(result.error) });
        return;
      }
      this.setState({ error: null, step: 'map', columns: result.data.columns, map: autoDetect(result.data.columns) });
      return;
    }
    if (this.state.step === 'map') {
      this.setState({ error: null, step: 'checks' });
      return;
    }
    if (this.state.step === 'checks') {
      await this.runCustom();
    }
  }

  private async runExample(): Promise<void> {
    const python = await this.ensurePython();
    if (!python) {
      this.setState({ step: 'welcome' });
      return;
    }
    this.store.markRunning(new Set(CHECKS.map((c) => c.id)));
    const result = await callBridge<CheckReportData>(python, this.bridgeScript(), { cmd: 'check_example' }, 30000);
    this.finishRun(result, this.state.enabled, 'Example data (synthetic)');
  }

  private async runCustom(): Promise<void> {
    const python = await this.ensurePython();
    if (!python) {
      return;
    }
    const file = this.state.files.find((f) => f.id === this.state.selectedFileId);
    if (!file) {
      return;
    }
    this.setState({ step: 'running' });
    const enabledIds = new Set(Object.keys(this.state.enabled).filter((id) => this.state.enabled[id]));
    this.store.markRunning(enabledIds);
    const result = await callBridge<CheckReportData>(
      python,
      this.bridgeScript(),
      { cmd: 'check', path: file.id, map: this.state.map, checks: this.state.enabled },
      60000
    );
    this.finishRun(result, this.state.enabled, file.name);
  }

  private finishRun(result: BridgeResult<CheckReportData>, enabled: Record<string, boolean>, datasetLabel: string): void {
    if (!result.ok) {
      this.setState({ step: 'done', error: explainBridgeError(result.error), results: null });
      return;
    }
    const report = result.data as ReportLikeWithText;
    const statuses = mapReportToStatuses(report, enabled);
    for (const [id, status] of Object.entries(statuses)) {
      this.store.setCheckStatus(id, status);
    }
    this.store.setDataset(datasetLabel);
    const results: readonly ResultCard[] = buildResultCards(report, enabled);
    this.setState({
      step: 'done',
      error: null,
      datasetLabel,
      results,
      selectedResultId: results[0]?.id ?? null,
    });
  }

  private render(webview: vscode.Webview, media: vscode.Uri): string {
    const theme = webview.asWebviewUri(vscode.Uri.joinPath(media, 'theme.css'));
    const stylesheet = webview.asWebviewUri(vscode.Uri.joinPath(media, 'wizard.css'));
    const script = webview.asWebviewUri(vscode.Uri.joinPath(media, 'wizard.js'));
    const token = nonce();
    const csp = `default-src 'none'; style-src ${webview.cspSource}; script-src 'nonce-${token}';`;

    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy" content="${csp}">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="${theme}">
  <link rel="stylesheet" href="${stylesheet}">
  <title>SAIL: New check</title>
</head>
<body>
  <div id="root"></div>
  <script nonce="${token}" src="${script}"></script>
</body>
</html>`;
  }
}

function nonce(): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let out = '';
  for (let i = 0; i < 32; i++) {
    out += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return out;
}

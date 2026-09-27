import * as vscode from 'vscode';

/** The status bar item on the right: "SAIL: Ready". Clicking it opens the SAIL sidebar. */
export class SailStatusBar implements vscode.Disposable {
  private readonly item: vscode.StatusBarItem;

  constructor(openCommand: string) {
    this.item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    this.item.command = openCommand;
    this.setReady();
    this.item.show();
  }

  get text(): string {
    return this.item.text;
  }

  setReady(): void {
    this.item.text = 'SAIL: Ready';
    this.item.tooltip = 'SAIL leakage checks: ready. Click to open.';
    this.item.accessibilityInformation = {
      label: 'SAIL leakage checks: ready. Activate to open the SAIL sidebar.',
      role: 'button',
    };
  }

  dispose(): void {
    this.item.dispose();
  }
}

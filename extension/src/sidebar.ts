import * as vscode from 'vscode';
import { CHECKS } from './checks';

/** Shown in the DATASET box until the user chooses one (Phase 3 wires this up). */
const NO_DATASET_LABEL = 'No dataset chosen';
const PRIVACY_NOTE = 'Runs on this computer. Your patient data is never uploaded.';

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

const DATABASE_ICON =
  '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">' +
  '<ellipse cx="12" cy="6" rx="7" ry="3"></ellipse><path d="M5 6v12c0 1.7 3.1 3 7 3s7-1.3 7-3V6"></path>' +
  '<path d="M5 12c0 1.7 3.1 3 7 3s7-1.3 7-3"></path></svg>';

const LOCK_ICON =
  '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">' +
  '<rect x="5" y="11" width="14" height="10" rx="2"></rect><path d="M8 11V8a4 4 0 0 1 8 0v3"></path></svg>';

/**
 * The SAIL sidebar. Static for now: a DATASET box, the five CHECKS all waiting to run, and the
 * privacy note. Scripts are off and the content security policy allows only our own stylesheet.
 */
export class SidebarProvider implements vscode.WebviewViewProvider {
  public static readonly viewType = 'sail.sidebar';

  private view: vscode.WebviewView | undefined;

  constructor(private readonly extensionUri: vscode.Uri) {}

  /** True while the sidebar is on screen. Used by the integration test. */
  get isResolved(): boolean {
    return this.view !== undefined;
  }

  resolveWebviewView(view: vscode.WebviewView): void {
    this.view = view;
    const media = vscode.Uri.joinPath(this.extensionUri, 'media');
    view.webview.options = { enableScripts: false, localResourceRoots: [media] };
    view.webview.html = this.render(view.webview, media);
    view.onDidDispose(() => {
      this.view = undefined;
    });
  }

  private render(webview: vscode.Webview, media: vscode.Uri): string {
    const stylesheet = webview.asWebviewUri(vscode.Uri.joinPath(media, 'sidebar.css'));
    const csp = `default-src 'none'; style-src ${webview.cspSource}; img-src ${webview.cspSource};`;

    const rows = CHECKS.map(
      (check) =>
        `<li class="check" title="${escapeHtml(check.question)}">` +
        `<span class="glyph glyph-pending" aria-hidden="true"></span>` +
        `<span class="check-name">${escapeHtml(check.name)}</span>` +
        `<span class="check-tag"></span></li>`
    ).join('\n        ');

    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy" content="${csp}">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="${stylesheet}">
  <title>SAIL</title>
</head>
<body>
  <main class="sail">
    <section aria-labelledby="dataset-heading">
      <h2 id="dataset-heading" class="eyebrow">DATASET</h2>
      <div class="dataset">
        ${DATABASE_ICON}
        <span class="dataset-label">${escapeHtml(NO_DATASET_LABEL)}</span>
      </div>
    </section>

    <section aria-labelledby="checks-heading">
      <h2 id="checks-heading" class="eyebrow">CHECKS</h2>
      <ul class="checks">
        ${rows}
      </ul>
    </section>

    <aside class="privacy">
      ${LOCK_ICON}
      <p>${escapeHtml(PRIVACY_NOTE)}</p>
    </aside>
  </main>
</body>
</html>`;
  }
}

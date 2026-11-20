"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.SidebarProvider = void 0;
const vscode = __importStar(require("vscode"));
const state_1 = require("./state");
const PRIVACY_NOTE = 'Runs on this computer. Your patient data is never uploaded.';
function escapeHtml(text) {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
function nonce() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let out = '';
    for (let i = 0; i < 32; i++) {
        out += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return out;
}
const DATABASE_ICON = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">' +
    '<ellipse cx="12" cy="6" rx="7" ry="3"></ellipse><path d="M5 6v12c0 1.7 3.1 3 7 3s7-1.3 7-3V6"></path>' +
    '<path d="M5 12c0 1.7 3.1 3 7 3s7-1.3 7-3"></path></svg>';
const LOCK_ICON = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">' +
    '<rect x="5" y="11" width="14" height="10" rx="2"></rect><path d="M8 11V8a4 4 0 0 1 8 0v3"></path></svg>';
/**
 * The SAIL sidebar, a webview view. The page loads with a skeleton already drawn (so the panel is never
 * blank), then the extension sends it the real state and the skeleton fades into the content.
 *
 * Handshake: the page posts {type: 'ready'} once its script has run; the extension answers with the state.
 * The page holds no data of its own and can send nothing except 'ready'.
 */
class SidebarProvider {
    extensionUri;
    log;
    store;
    static viewType = 'sail.sidebar';
    view;
    ready = false;
    constructor(extensionUri, log, store) {
        this.extensionUri = extensionUri;
        this.log = log;
        this.store = store;
    }
    /** True while the sidebar is on screen. */
    get isResolved() {
        return this.view !== undefined;
    }
    /** True once the page has loaded its script and received its content. */
    get isReady() {
        return this.ready;
    }
    resolveWebviewView(view) {
        const started = Date.now();
        this.view = view;
        this.ready = false;
        const media = vscode.Uri.joinPath(this.extensionUri, 'media');
        view.webview.options = { enableScripts: true, localResourceRoots: [media] };
        view.webview.html = this.render(view.webview, media);
        view.webview.onDidReceiveMessage((message) => {
            if (!(0, state_1.isWebviewMessage)(message)) {
                return;
            }
            this.ready = true;
            this.log.info(`sidebar ready ${Date.now() - started} ms after it was opened`);
            this.push();
        });
        // The store outlives any one view: a wizard run started while the sidebar is hidden must still be
        // reflected the moment it is shown again.
        const subscription = this.store.onDidChange(() => this.push());
        view.onDidDispose(() => {
            this.view = undefined;
            this.ready = false;
            subscription.dispose();
        });
        this.log.info('sidebar opened');
    }
    push() {
        if (this.view && this.ready) {
            void this.view.webview.postMessage({ type: 'state', state: this.store.get() });
        }
    }
    render(webview, media) {
        const theme = webview.asWebviewUri(vscode.Uri.joinPath(media, 'theme.css'));
        const stylesheet = webview.asWebviewUri(vscode.Uri.joinPath(media, 'sidebar.css'));
        const script = webview.asWebviewUri(vscode.Uri.joinPath(media, 'sidebar.js'));
        const token = nonce();
        const csp = `default-src 'none'; style-src ${webview.cspSource}; script-src 'nonce-${token}';`;
        // Five placeholder rows, matching the five checks, so nothing jumps when the content arrives.
        const skeletonRows = this.store
            .get()
            .checks.map(() => '<div class="skeleton-row"><span class="skeleton skeleton-dot"></span><span class="skeleton skeleton-line"></span></div>')
            .join('\n        ');
        return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy" content="${csp}">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="${theme}">
  <link rel="stylesheet" href="${stylesheet}">
  <title>SAIL</title>
</head>
<body>
  <main class="sail">
    <div id="skeleton" class="skeleton-wrap" role="status" aria-label="Loading SAIL">
      <div class="skeleton skeleton-eyebrow"></div>
      <div class="skeleton skeleton-box"></div>
      <div class="skeleton skeleton-eyebrow"></div>
      <div class="skeleton-list">
        ${skeletonRows}
      </div>
    </div>

    <div id="app" class="app" hidden>
      <section aria-labelledby="dataset-heading">
        <h2 id="dataset-heading" class="eyebrow">DATASET</h2>
        <div class="dataset">
          ${DATABASE_ICON}
          <span id="dataset-label" class="dataset-label"></span>
        </div>
      </section>

      <section aria-labelledby="checks-heading">
        <h2 id="checks-heading" class="eyebrow">CHECKS</h2>
        <ul id="checks" class="checks"></ul>
      </section>

      <aside class="privacy">
        ${LOCK_ICON}
        <p>${escapeHtml(PRIVACY_NOTE)}</p>
      </aside>
    </div>
  </main>
  <script nonce="${token}" src="${script}"></script>
</body>
</html>`;
    }
}
exports.SidebarProvider = SidebarProvider;
//# sourceMappingURL=sidebar.js.map
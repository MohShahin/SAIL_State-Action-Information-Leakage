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
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const appState_1 = require("./appState");
const sidebar_1 = require("./sidebar");
const statusBar_1 = require("./statusBar");
const wizard_1 = require("./wizard");
const EXTENSION_ID = 'mohshahin.sail-leakage-checks';
const FOCUS = 'sail.focus';
const CHECK_DATASET = 'sail.checkDataset';
function activate(context) {
    const started = Date.now();
    const log = vscode.window.createOutputChannel('SAIL', { log: true });
    const store = new appState_1.AppStateStore();
    const sidebar = new sidebar_1.SidebarProvider(context.extensionUri, log, store);
    let wizard;
    const openSidebar = () => vscode.commands.executeCommand('workbench.view.extension.sail');
    const openWizard = () => {
        wizard = wizard_1.WizardPanel.createOrShow(context.extensionUri, store, log);
        return wizard;
    };
    // The status bar's own command: reopen the wizard if a run's results are still open in a tab,
    // otherwise fall back to the sidebar (which always shows the current per-check status).
    const openReport = () => {
        if (!wizard_1.WizardPanel.revealIfOpen()) {
            void openSidebar();
        }
    };
    const status = new statusBar_1.SailStatusBar(store, 'sail.openReport');
    context.subscriptions.push(log, status, vscode.window.registerWebviewViewProvider(sidebar_1.SidebarProvider.viewType, sidebar), vscode.commands.registerCommand(FOCUS, openSidebar), vscode.commands.registerCommand(CHECK_DATASET, openWizard), vscode.commands.registerCommand('sail.openReport', openReport), vscode.commands.registerCommand('sail.openWalkthrough', () => vscode.commands.executeCommand('workbench.action.openWalkthrough', `${EXTENSION_ID}#sail.gettingStarted`, false)), vscode.commands.registerCommand('sail.moveToSecondarySideBar', async () => {
        // VS Code's own "Move View" flow: first pick the view, then pick where it goes. Say which to choose.
        // (Dragging the SAIL icon from the activity bar to the other side of the window does the same.)
        vscode.window.setStatusBarMessage('SAIL: choose "Leakage Checks", then "Secondary Side Bar"', 15000);
        await vscode.commands.executeCommand('workbench.action.moveView');
    }));
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
        wizardResults: () => wizard?.stateForTest() ?? null,
    };
}
function deactivate() { }
//# sourceMappingURL=extension.js.map
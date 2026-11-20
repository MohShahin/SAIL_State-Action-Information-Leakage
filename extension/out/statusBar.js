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
exports.SailStatusBar = void 0;
const vscode = __importStar(require("vscode"));
const state_1 = require("./state");
/**
 * The status bar item on the right: the sail mark plus a short status. `$(sail-logo)` is the icon this
 * extension contributes (see "icons" in package.json). The text itself comes from `computeStatusBar`,
 * so what shows here is always exactly derivable from the same state the sidebar draws.
 */
class SailStatusBar {
    item;
    subscription;
    constructor(store, command) {
        this.item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
        this.item.name = 'SAIL';
        this.item.command = command;
        this.render(store);
        this.item.show();
        this.subscription = store.onDidChange(() => this.render(store));
    }
    get text() {
        return this.item.text;
    }
    render(store) {
        const view = (0, state_1.computeStatusBar)(store.get());
        this.item.text = `$(sail-logo) ${view.text}`;
        this.item.tooltip = view.tooltip;
        this.item.backgroundColor = view.warn ? new vscode.ThemeColor('statusBarItem.warningBackground') : undefined;
        this.item.accessibilityInformation = { label: `${view.text}. Activate to open the report.`, role: 'button' };
    }
    dispose() {
        this.subscription.dispose();
        this.item.dispose();
    }
}
exports.SailStatusBar = SailStatusBar;
//# sourceMappingURL=statusBar.js.map
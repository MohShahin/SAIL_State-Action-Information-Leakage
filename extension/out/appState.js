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
exports.AppStateStore = void 0;
const vscode = __importStar(require("vscode"));
const state_1 = require("./state");
/**
 * The one place the sidebar's DATASET and CHECKS actually live. Both the sidebar webview and the setup
 * wizard read and write through this, so they can never disagree about what has been chosen or run.
 */
class AppStateStore {
    state = (0, state_1.initialState)();
    emitter = new vscode.EventEmitter();
    onDidChange = this.emitter.event;
    get() {
        return this.state;
    }
    setDataset(name) {
        this.state = { ...this.state, dataset: name };
        this.emitter.fire(this.state);
    }
    setCheckStatus(id, status) {
        this.state = {
            ...this.state,
            checks: this.state.checks.map((c) => (c.id === id ? { ...c, status } : c)),
        };
        this.emitter.fire(this.state);
    }
    /** About to run: the given ids go to 'running', everything else to 'off'. */
    markRunning(idsToRun) {
        this.state = {
            ...this.state,
            checks: this.state.checks.map((c) => ({ ...c, status: idsToRun.has(c.id) ? 'running' : 'off' })),
        };
        this.emitter.fire(this.state);
    }
}
exports.AppStateStore = AppStateStore;
//# sourceMappingURL=appState.js.map
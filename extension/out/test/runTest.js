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
const os = __importStar(require("os"));
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
const test_electron_1 = require("@vscode/test-electron");
/**
 * Starts a real VS Code with this extension loaded and runs suite/index.js inside it.
 * Set VSCODE_EXE to use an already-installed VS Code instead of downloading one.
 */
async function main() {
    const extensionDevelopmentPath = path.resolve(__dirname, '../../');
    const extensionTestsPath = path.resolve(__dirname, 'suite/index');
    const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'sail-test-'));
    try {
        await (0, test_electron_1.runTests)({
            vscodeExecutablePath: process.env.VSCODE_EXE || undefined,
            extensionDevelopmentPath,
            extensionTestsPath,
            // A throwaway profile, so a running VS Code (and its settings) is never touched.
            launchArgs: [
                '--disable-extensions',
                '--disable-workspace-trust',
                '--user-data-dir',
                path.join(profile, 'user'),
                '--extensions-dir',
                path.join(profile, 'ext'),
            ],
        });
    }
    finally {
        fs.rmSync(profile, { recursive: true, force: true });
    }
}
main().catch((err) => {
    console.error('Extension tests failed:', err);
    process.exit(1);
});
//# sourceMappingURL=runTest.js.map
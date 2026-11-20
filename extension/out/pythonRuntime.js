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
exports.resolvePython = resolvePython;
exports.verifySail = verifySail;
const vscode = __importStar(require("vscode"));
const procUtil_1 = require("./procUtil");
/**
 * Finds a Python interpreter to run the bridge with, and checks that `sail-leakage` is importable
 * under it. Order: the `sail.pythonPath` setting, then the Python extension's selected interpreter (if
 * that extension is installed), then `python3`/`python` on PATH. Nothing here ever installs anything.
 */
async function fromPythonExtension() {
    try {
        const ext = vscode.extensions.getExtension('ms-python.python');
        if (!ext) {
            return null;
        }
        const api = ext.isActive ? ext.exports : await ext.activate();
        const uri = vscode.workspace.workspaceFolders?.[0]?.uri;
        // The Python extension's API has changed shape across versions; try the newer one, then the older
        // one, and give up quietly rather than throw if neither is there.
        const envPath = api?.environments?.getActiveEnvironmentPath?.(uri)?.path;
        if (envPath) {
            return envPath;
        }
        const execCommand = api?.settings?.getExecutionDetails?.(uri)?.execCommand;
        if (Array.isArray(execCommand) && execCommand.length > 0) {
            return execCommand[0];
        }
    }
    catch {
        // Fall through to a PATH search.
    }
    return null;
}
async function onPath(command) {
    const r = await (0, procUtil_1.runProcess)(command, ['--version'], undefined, 5000);
    return !r.timedOut && r.code === 0;
}
async function resolvePython() {
    const configured = vscode.workspace.getConfiguration('sail').get('pythonPath', '').trim();
    if (configured) {
        return configured;
    }
    const fromExtension = await fromPythonExtension();
    if (fromExtension) {
        return fromExtension;
    }
    for (const candidate of ['python3', 'python']) {
        if (await onPath(candidate)) {
            return candidate;
        }
    }
    return null;
}
const PROBE_CODE = "import json,sys\n" +
    "try:\n" +
    " import sail\n" +
    "except Exception as e:\n" +
    " print(json.dumps({'ok': False, 'stage': 'sail', 'message': str(e)})); sys.exit(0)\n" +
    "print(json.dumps({'ok': True, 'version': sail.__version__}))\n";
async function verifySail(pythonPath) {
    const r = await (0, procUtil_1.runProcess)(pythonPath, ['-c', PROBE_CODE], undefined, 15000);
    if (r.timedOut) {
        return { ok: false, stage: 'python', message: 'Python did not respond within 15s.' };
    }
    if (r.code !== 0 && !r.stdout.trim()) {
        return { ok: false, stage: 'python', message: (r.stderr || `exit code ${r.code}`).trim().slice(0, 500) };
    }
    try {
        const parsed = JSON.parse(r.stdout.trim().split('\n').pop() ?? '');
        return parsed.ok ? { ok: true, version: parsed.version } : { ok: false, stage: 'sail', message: parsed.message };
    }
    catch {
        return { ok: false, stage: 'python', message: `Unexpected output: ${(r.stdout || r.stderr).slice(0, 300)}` };
    }
}
//# sourceMappingURL=pythonRuntime.js.map
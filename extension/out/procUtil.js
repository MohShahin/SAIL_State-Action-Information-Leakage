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
exports.runProcess = runProcess;
const cp = __importStar(require("child_process"));
/** Runs one process to completion, feeding it `input` on stdin (if given) and collecting both streams. */
function runProcess(command, args, input, timeoutMs = 60000) {
    return new Promise((resolve) => {
        let child;
        try {
            child = cp.spawn(command, args, { windowsHide: true });
        }
        catch (err) {
            resolve({ code: null, stdout: '', stderr: String(err), timedOut: false });
            return;
        }
        let stdout = '';
        let stderr = '';
        let timedOut = false;
        const timer = setTimeout(() => {
            timedOut = true;
            child.kill();
        }, timeoutMs);
        child.stdout?.on('data', (d) => (stdout += d.toString('utf8')));
        child.stderr?.on('data', (d) => (stderr += d.toString('utf8')));
        child.on('error', (err) => {
            clearTimeout(timer);
            resolve({ code: null, stdout, stderr: stderr || String(err), timedOut });
        });
        child.on('close', (code) => {
            clearTimeout(timer);
            resolve({ code, stdout, stderr, timedOut });
        });
        if (input !== undefined) {
            child.stdin?.write(input, 'utf8');
        }
        child.stdin?.end();
    });
}
//# sourceMappingURL=procUtil.js.map
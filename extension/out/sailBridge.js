"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.callBridge = callBridge;
const procUtil_1 = require("./procUtil");
/**
 * Calls `python/sail_bridge.py`: writes one JSON request to its stdin, reads one JSON response from
 * its stdout. The bridge prints a marker line before its actual answer so a stray print from a library
 * (pandas, a warning, ...) earlier in stdout can never be mistaken for the response.
 */
const MARKER = '##SAIL_BRIDGE_RESULT##';
async function callBridge(pythonPath, bridgeScriptPath, payload, timeoutMs = 60000) {
    const r = await (0, procUtil_1.runProcess)(pythonPath, [bridgeScriptPath], JSON.stringify(payload), timeoutMs);
    if (r.timedOut) {
        return { ok: false, error: `Python did not finish within ${Math.round(timeoutMs / 1000)}s.` };
    }
    const idx = r.stdout.lastIndexOf(MARKER);
    if (idx === -1) {
        const detail = (r.stderr || r.stdout).trim();
        return {
            ok: false,
            error: detail ? detail.slice(0, 2000) : `Python exited with code ${r.code} and produced no output.`,
        };
    }
    try {
        const parsed = JSON.parse(r.stdout.slice(idx + MARKER.length).trim());
        return parsed;
    }
    catch {
        return { ok: false, error: 'Could not parse the response from Python.' };
    }
}
//# sourceMappingURL=sailBridge.js.map
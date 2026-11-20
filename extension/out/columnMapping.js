"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.autoDetect = autoDetect;
const PATTERNS = [
    { field: 'stay', pattern: /(stay|patient|subject|encounter|icustay)[_-]?id|^id$/i },
    { field: 'time', pattern: /time|step|hour|bin|chart|timestamp/i },
    { field: 'action', pattern: /action|treatment|vaso|dose|drug/i },
    { field: 'reward', pattern: /reward|outcome|mortality|surviv|label|target/i },
];
function autoDetect(columns) {
    const pool = new Set(columns);
    const map = { stay: null, time: null, action: null, reward: null };
    for (const { field, pattern } of PATTERNS) {
        const match = columns.find((c) => pool.has(c) && pattern.test(c));
        if (match) {
            map[field] = match;
            pool.delete(match);
        }
    }
    return map;
}
//# sourceMappingURL=columnMapping.js.map
/**
 * Guesses which column is which, from column names alone -- the "Auto-detected" step of the wizard.
 * Pure and side-effect free, so it is testable without a dataset or a running VS Code.
 *
 * Each field is matched in a fixed priority order (stay, then time, then action, then reward) and a
 * column already claimed by an earlier field is removed from the pool, so two fields never claim the
 * same column. A field with no matching column is left null -- the user fills it in themselves.
 */
export interface FieldMap {
  stay: string | null;
  time: string | null;
  action: string | null;
  reward: string | null;
}

const PATTERNS: { field: keyof FieldMap; pattern: RegExp }[] = [
  { field: 'stay', pattern: /(stay|patient|subject|encounter|icustay)[_-]?id|^id$/i },
  { field: 'time', pattern: /time|step|hour|bin|chart|timestamp/i },
  { field: 'action', pattern: /action|treatment|vaso|dose|drug/i },
  { field: 'reward', pattern: /reward|outcome|mortality|surviv|label|target/i },
];

export function autoDetect(columns: readonly string[]): FieldMap {
  const pool = new Set(columns);
  const map: FieldMap = { stay: null, time: null, action: null, reward: null };
  for (const { field, pattern } of PATTERNS) {
    const match = columns.find((c) => pool.has(c) && pattern.test(c));
    if (match) {
      map[field] = match;
      pool.delete(match);
    }
  }
  return map;
}

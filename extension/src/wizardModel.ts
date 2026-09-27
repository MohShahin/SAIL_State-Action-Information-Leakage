/**
 * The setup wizard's state and the pure functions that turn it into what the webview draws, and turn a
 * finished report back into sidebar check statuses. No `vscode` import here on purpose: everything in
 * this file runs (and is tested) without a running VS Code.
 */
import { CHECKS } from './checks';
import { CheckStatus } from './state';
import { FieldMap } from './columnMapping';

export type WizardStep = 'welcome' | 'data' | 'map' | 'checks' | 'running' | 'done';

export interface DataFile {
  readonly id: string; // absolute path; also the value sent to the Python bridge
  readonly name: string;
  readonly detail: string; // workspace-relative path, or the full path for a browsed file
}

export interface WizardState {
  readonly step: WizardStep;
  readonly error: string | null;
  readonly files: readonly DataFile[];
  readonly selectedFileId: string | null;
  readonly columns: readonly string[];
  readonly map: FieldMap;
  readonly enabled: Readonly<Record<string, boolean>>;
  readonly isExample: boolean;
  readonly resultSummary: string | null;
}

export function initialWizardState(): WizardState {
  const enabled: Record<string, boolean> = {};
  for (const c of CHECKS) {
    enabled[c.id] = true;
  }
  return {
    step: 'welcome',
    error: null,
    files: [],
    selectedFileId: null,
    columns: [],
    map: { stay: null, time: null, action: null, reward: null },
    enabled,
    isExample: false,
    resultSummary: null,
  };
}

const FIELD_META: { key: keyof FieldMap; label: string; help: string }[] = [
  { key: 'stay', label: 'Patient or stay ID', help: 'Identifies each ICU stay' },
  { key: 'time', label: 'Time step', help: 'When each row was measured' },
  { key: 'action', label: 'Treatment (action)', help: 'What the model decides' },
  { key: 'reward', label: 'Outcome (reward)', help: 'What the model tries to improve' },
];

export interface ViewFile {
  readonly id: string;
  readonly name: string;
  readonly detail: string;
  readonly selected: boolean;
}
export interface ViewField {
  readonly key: keyof FieldMap;
  readonly label: string;
  readonly help: string;
  readonly value: string | null;
  readonly options: readonly string[];
}
export interface ViewCheck {
  readonly id: string;
  readonly name: string;
  readonly question: string;
  readonly on: boolean;
}
export interface ViewModel {
  readonly step: WizardStep;
  readonly error: string | null;
  readonly isWelcome: boolean;
  readonly isData: boolean;
  readonly isMap: boolean;
  readonly isChecks: boolean;
  readonly isRunning: boolean;
  readonly isDone: boolean;
  readonly showNav: boolean;
  readonly files: readonly ViewFile[];
  readonly fields: readonly ViewField[];
  readonly checks: readonly ViewCheck[];
  readonly nextDisabled: boolean;
  readonly nextLabel: string;
  readonly isExample: boolean;
  readonly resultSummary: string | null;
}

export function computeViewModel(state: WizardState): ViewModel {
  const anyEnabled = Object.values(state.enabled).some(Boolean);
  const showNav = state.step === 'data' || state.step === 'map' || state.step === 'checks';
  return {
    step: state.step,
    error: state.error,
    isWelcome: state.step === 'welcome',
    isData: state.step === 'data',
    isMap: state.step === 'map',
    isChecks: state.step === 'checks',
    isRunning: state.step === 'running',
    isDone: state.step === 'done',
    showNav,
    files: state.files.map((f) => ({ ...f, selected: f.id === state.selectedFileId })),
    fields: FIELD_META.map((f) => ({ ...f, value: state.map[f.key], options: state.columns })),
    checks: CHECKS.map((c) => ({ id: c.id, name: c.name, question: c.question, on: state.enabled[c.id] })),
    nextDisabled:
      state.step === 'data' ? !state.selectedFileId : state.step === 'checks' ? !anyEnabled : false,
    nextLabel: state.step === 'checks' ? 'Run checks' : 'Continue',
    isExample: state.isExample,
    resultSummary: state.resultSummary,
  };
}

/** The category strings `sail.check()` actually reports, mapped back to a check's id. */
export function categoryToCheckId(category: string): string | null {
  if (category.startsWith('construction_leakage')) return 'c1';
  if (category === 'reconstruction_leakage') return 'c2';
  if (category === 'temporal_overlap_leakage') return 'c3';
  if (category === 'timing_violation_leakage') return 'c4';
  if (category === 'persistence_dominance') return 'c5';
  return null;
}

export interface ReportLike {
  readonly findings: readonly { category: string; flagged: boolean }[];
  readonly skipped: Readonly<Record<string, string>>;
}

/**
 * Turns one finished `sail.check()` report into a status per check id.
 *
 * A check the user turned off is 'off', full stop -- it never shows as 'not-run' even though it is
 * also absent from the report (sail.check() has no way to tell "disabled" from "no reason to run it"
 * apart from the caller's own enabled/disabled record, which is exactly what `enabled` is here).
 */
export function mapReportToStatuses(
  report: ReportLike,
  enabled: Readonly<Record<string, boolean>>
): Record<string, CheckStatus> {
  const statuses: Record<string, CheckStatus> = {};
  for (const id of Object.keys(enabled)) {
    statuses[id] = enabled[id] ? 'pending' : 'off';
  }
  for (const finding of report.findings) {
    const id = categoryToCheckId(finding.category);
    if (id) {
      statuses[id] = finding.flagged ? 'flagged' : 'passed';
    }
  }
  for (const category of Object.keys(report.skipped)) {
    const id = categoryToCheckId(category);
    if (id && enabled[id] && statuses[id] !== 'flagged' && statuses[id] !== 'passed') {
      statuses[id] = 'not-run';
    }
  }
  return statuses;
}

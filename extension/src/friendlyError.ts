/**
 * Turns the raw, technical error text SAIL can run into (a Python exception, a missing interpreter, a
 * failed save) into one plain-language sentence, with the raw text always kept as a `detail` -- never
 * hidden, just not the first thing a non-programmer has to read. Pure; no vscode, no I/O.
 */
export interface FriendlyError {
  readonly message: string;
  readonly detail?: string;
}

export function explainPythonMissing(checked: readonly string[]): FriendlyError {
  return {
    message: "SAIL couldn't find Python on your computer.",
    detail:
      `Checked: ${checked.join(', ')} on your PATH. If Python is installed somewhere else, set ` +
      '"sail.pythonPath" in Settings, or install the Python extension and select an interpreter there.',
  };
}

export function explainSailMissing(pythonPath: string, rawMessage: string): FriendlyError {
  return {
    message: "Python was found, but the sail-leakage package isn't installed for it.",
    detail: `Interpreter: ${pythonPath}\n${rawMessage}\n\nTo install it, open a terminal and run:\npip install sail-leakage`,
  };
}

export function explainPythonError(pythonPath: string, rawMessage: string): FriendlyError {
  return {
    message: `SAIL couldn't run Python at "${pythonPath}".`,
    detail: rawMessage,
  };
}

/**
 * Patterns matched against the exception text sail_bridge.py returns (`"<ExceptionType>: <message>"`,
 * see its own `except Exception as exc` handler). Checked in order; the first match wins.
 */
const PATTERNS: readonly { readonly test: RegExp; readonly message: string }[] = [
  { test: /FileNotFoundError/, message: "SAIL couldn't find that file. It may have been moved, renamed, or deleted." },
  { test: /PermissionError/, message: "SAIL doesn't have permission to read that file." },
  {
    test: /UnicodeDecodeError/,
    message: "SAIL couldn't read that file as text. It may not actually be a CSV or Parquet file, or it may be corrupted.",
  },
  { test: /EmptyDataError|No columns to parse from file/, message: 'That file appears to be empty.' },
  { test: /ParserError/, message: "SAIL couldn't read that file as a CSV. Check that it's really a CSV file." },
  {
    test: /ArrowInvalid|Parquet magic bytes not found|Could not open Parquet/i,
    message: "SAIL couldn't read that file as Parquet. Check that it's really a Parquet file.",
  },
  { test: /ModuleNotFoundError: No module named 'sail'/, message: "sail-leakage isn't installed for this Python interpreter." },
  { test: /KeyError/, message: 'One of the columns SAIL expected is missing from this file.' },
  { test: /ValueError/, message: 'SAIL was given a combination of inputs it could not use.' },
];

export function explainBridgeError(rawMessage: string): FriendlyError {
  const match = PATTERNS.find((p) => p.test.test(rawMessage));
  return {
    message: match ? match.message : "SAIL ran into a problem it didn't expect while running Python.",
    detail: rawMessage,
  };
}

export function explainSaveError(rawMessage: string): FriendlyError {
  return { message: "SAIL couldn't save the report.", detail: rawMessage };
}

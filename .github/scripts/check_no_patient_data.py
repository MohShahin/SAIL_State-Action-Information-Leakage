"""Fail if a tracked file could carry MIMIC-IV row-level data.

Used by BOTH the pre-commit hook (.pre-commit-config.yaml) and CI (.github/workflows/hygiene.yml),
so the two cannot drift apart. See DATA_ACCESS.md for the policy this enforces.

Two checks, run over every file git tracks (staged files included):

1. Notebook outputs: any tracked .ipynb whose code cells hold saved outputs. Saved outputs are how
   DataFrame heads and printed rows end up in a public repo.
2. MIMIC identifier values: any standalone 8-digit number starting with 1, 2 or 3 in a text file.
   That covers all three MIMIC-IV identifiers (subject_id 1xxxxxxx, hadm_id 2xxxxxxx,
   stay_id 3xxxxxxx). It matches the value itself, not the column name, so an ID in a comment or an
   f-string is caught too. Measured against this repo when written: one hit, zero false positives.

Deliberately NOT covered: binary files (PDF, DOCX, images, video) are not read. A number that is
legitimately in that shape can be allowed by adding "path:number" to
.github/scripts/patient_data_allowlist.txt (that file is itself exempt from the ID scan, since it
has to contain the values it allows).

Exit code 0 = clean, 1 = findings (printed), 2 = could not run.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ID_PATTERN = re.compile(r"(?<![0-9A-Za-z_.\-])([123][0-9]{7})(?![0-9])")
ALLOWLIST = Path(__file__).with_name("patient_data_allowlist.txt")
ALLOWLIST_REL = ".github/scripts/patient_data_allowlist.txt"


def tracked_files(root: Path) -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True
    ).stdout.decode("utf-8", "replace")
    return [p for p in out.split("\0") if p]


def load_allowlist() -> set[str]:
    if not ALLOWLIST.exists():
        return set()
    lines = (l.strip() for l in ALLOWLIST.read_text(encoding="utf-8").splitlines())
    return {l for l in lines if l and not l.startswith("#")}


def notebook_findings(path: Path) -> list[str]:
    try:
        nb = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"{path}: cannot parse notebook ({exc})"]
    bad = [
        i for i, c in enumerate(nb.get("cells", []))
        if c.get("cell_type") == "code" and c.get("outputs")
    ]
    if not bad:
        return []
    return [f"{path}: {len(bad)} code cell(s) have saved outputs (cell index {bad[:8]}"
            f"{'...' if len(bad) > 8 else ''}) -- clear them (nbstripout)"]


def id_findings(path: Path, rel: str, allowed: set[str]) -> list[str]:
    try:
        data = path.read_bytes()
    except OSError:
        return []
    if b"\0" in data[:4096]:  # binary
        return []
    findings = []
    for lineno, line in enumerate(data.decode("utf-8", "replace").splitlines(), 1):
        for m in ID_PATTERN.finditer(line):
            if f"{rel}:{m.group(1)}" in allowed:
                continue
            findings.append(f"{rel}:{lineno}: MIMIC-shaped identifier {m.group(1)}")
    return findings


def main(root: Path) -> int:
    try:
        files = tracked_files(root)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"could not list tracked files: {exc}", file=sys.stderr)
        return 2
    allowed = load_allowlist()
    findings: list[str] = []
    for rel in files:
        path = root / rel
        if not path.is_file():
            continue  # deleted in the working tree but still in the index
        if rel.endswith(".ipynb"):
            findings += notebook_findings(path)
        if rel != ALLOWLIST_REL:
            findings += id_findings(path, rel, allowed)
    if findings:
        print("PATIENT-DATA CHECK FAILED:")
        for f in findings:
            print("  " + f)
        print("\nSee DATA_ACCESS.md. Row-level MIMIC-IV data, including identifiers, must not be committed.")
        return 1
    print(f"patient-data check passed ({len(files)} tracked files scanned)")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()))

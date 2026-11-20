#!/usr/bin/env python3
"""Write or verify results/MANIFEST.json: a SHA-256 for every committed aggregate result file.

    python scripts/make_manifest.py            # (re)write results/MANIFEST.json
    python scripts/make_manifest.py --check    # verify; exit 1 on any mismatch

Only files under results/ that git tracks are listed. The manifest contains hashes and sizes, never data.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "results" / "MANIFEST.json"


def tracked_results() -> list:
    out = subprocess.run(["git", "ls-files", "results"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return sorted(p for p in out.splitlines() if p and p != "results/MANIFEST.json")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def build() -> dict:
    files = {p: {"sha256": sha256(ROOT / p), "bytes": (ROOT / p).stat().st_size} for p in tracked_results()}
    return {"schema_version": "1", "algorithm": "sha256", "n_files": len(files), "files": files}


def main(argv) -> int:
    if "--check" in argv:
        if not MANIFEST.exists():
            print("results/MANIFEST.json is missing; run: python scripts/make_manifest.py")
            return 1
        want = json.loads(MANIFEST.read_text())["files"]
        have = build()["files"]
        bad = [p for p in sorted(set(want) | set(have)) if want.get(p, {}).get("sha256") != have.get(p, {}).get("sha256")]
        if bad:
            print("Manifest mismatch:\n  " + "\n  ".join(bad))
            return 1
        print(f"OK: {len(want)} result files match results/MANIFEST.json")
        return 0
    m = build()
    MANIFEST.write_text(json.dumps(m, indent=2, sort_keys=True) + "\n")
    print(f"wrote results/MANIFEST.json ({m['n_files']} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

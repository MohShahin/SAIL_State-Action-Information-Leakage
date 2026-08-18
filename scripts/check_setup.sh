#!/usr/bin/env bash
# scripts/check_setup.sh
# Run this before anything else, from the repo root:  bash scripts/check_setup.sh
# Verifies gcloud auth, BigQuery access to both your scratch project and the
# credentialed physionet-data project, and that the scratch dataset exists —
# so a broken environment fails fast with a clear message instead of a
# confusing mid-pipeline BigQuery error.

set -u
PROJECT_ID="${PROJECT_ID:-commanding-pier-456419-p8}"
SCRATCH_DATASET_NAME="${SCRATCH_DATASET_NAME:-temp_dataset}"

pass() { echo "  [OK] $1"; }
fail() { echo "  [FAIL] $1"; FAILED=1; }
FAILED=0

echo "== 1. gcloud CLI present =="
if command -v gcloud >/dev/null 2>&1; then pass "gcloud found: $(gcloud --version | head -1)"; else fail "gcloud not installed — https://cloud.google.com/sdk/docs/install"; fi

echo "== 2. Active gcloud auth =="
ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null)
if [ -n "$ACTIVE_ACCOUNT" ]; then pass "logged in as $ACTIVE_ACCOUNT"; else fail "not logged in — run: gcloud auth login && gcloud auth application-default login"; fi

echo "== 3. bq CLI present =="
if command -v bq >/dev/null 2>&1; then pass "bq found"; else fail "bq not found (ships with gcloud) — try: gcloud components install bq"; fi

echo "== 4. Access to your own GCP project ($PROJECT_ID) =="
if bq ls --project_id="$PROJECT_ID" >/dev/null 2>&1; then pass "can list datasets in $PROJECT_ID"; else fail "cannot access $PROJECT_ID — check project id and permissions"; fi

echo "== 5. Scratch dataset exists ($PROJECT_ID.$SCRATCH_DATASET_NAME) =="
if bq show --project_id="$PROJECT_ID" "$SCRATCH_DATASET_NAME" >/dev/null 2>&1; then
  pass "$SCRATCH_DATASET_NAME exists"
else
  fail "$SCRATCH_DATASET_NAME does not exist yet — create it with: bq mk --dataset ${PROJECT_ID}:${SCRATCH_DATASET_NAME}"
fi

echo "== 6. Credentialed access to physionet-data =="
if bq ls --project_id=physionet-data mimiciv_3_1_icu >/dev/null 2>&1; then
  pass "can list mimiciv_3_1_icu tables — MIMIC-IV access confirmed"
else
  fail "cannot access physionet-data — confirm your PhysioNet credentialing is complete and physionet-data is shared to $ACTIVE_ACCOUNT (see DATA_ACCESS.md)"
fi

echo "== 7. Python packages =="
PYBIN=""
for cand in python3 python; do
  if command -v "$cand" >/dev/null 2>&1; then PYBIN="$cand"; break; fi
done
if [ -z "$PYBIN" ]; then
  fail "no python3 or python found on PATH"
else
  "$PYBIN" - <<'PYEOF'
import importlib, sys
mods = ["google.cloud.bigquery", "pandas", "numpy", "sklearn"]
missing = []
for m in mods:
    try:
        importlib.import_module(m)
    except ImportError:
        missing.append(m)
if missing:
    print(f"  [FAIL] missing: {', '.join(missing)} — pip install google-cloud-bigquery pandas numpy scikit-learn")
    sys.exit(1)
else:
    print("  [OK] google-cloud-bigquery, pandas, numpy, scikit-learn all importable")
PYEOF
  if [ "$?" != "0" ]; then FAILED=1; fi
fi

echo ""
if [ "$FAILED" = "1" ]; then
  echo "One or more checks failed — fix those before running the queries or notebook."
  exit 1
else
  echo "All checks passed. Safe to proceed to queries/01_cohort.sql."
fi

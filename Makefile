# Common tasks. Targets marked (no data) run anywhere; the replicate targets need MIMIC-IV access.
PY ?= python

.PHONY: help install test demo verify manifest privacy-check replicate-h3 replicate-all

help:
	@echo "make install        install the package with test dependencies"
	@echo "make test           run the test suite (no data)"
	@echo "make demo           run the checks on a built-in synthetic table (no data)"
	@echo "make verify         check committed results against results/MANIFEST.json (no data)"
	@echo "make privacy-check  scan tracked files for patient-level data (no data)"
	@echo "make manifest       rewrite results/MANIFEST.json after adding a reviewed result file"
	@echo "make replicate-h3   print the steps to reproduce the primary H3 result (needs MIMIC-IV)"

install:
	$(PY) -m pip install -e ".[dev]"

test:
	$(PY) -m pytest -q

demo:
	$(PY) -m sail demo

verify:
	$(PY) scripts/make_manifest.py --check

manifest:
	$(PY) scripts/make_manifest.py

privacy-check:
	$(PY) .github/scripts/check_no_patient_data.py

# The full pipeline needs a credentialed MIMIC-IV v3.1 database and hours of compute, so these
# targets print the steps from REPLICATE.md instead of running them blindly.
replicate-h3 replicate-all:
	@sed -n '/^## Reproduce the primary result/,/^## Expected/p' REPLICATE.md

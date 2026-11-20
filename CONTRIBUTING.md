# Contributing

Thank you for helping. You do not need to write code to contribute: translations, teaching material,
paper screening and bug reports all count.

## Ways to contribute

- **Package and extension:** fix a bug, add a test, improve an error message, propose a detector.
- **Library:** screen papers against the leakage codebook (families A to F).
- **Paper:** reproduce a result, check a claim against its file, improve the write-up.
- **Learn and workshops:** write or review an episode, a synthetic exercise, or a translation.

## Before you open a pull request

1. Open an issue first for anything bigger than a small fix.
2. Run `pip install -e ".[dev]"` then `pytest`. All tests must pass.
3. Run `python .github/scripts/check_no_patient_data.py`. Never commit patient-level data; see
   `DATA_ACCESS.md`. Only reviewed aggregate files may be added under `results/`.
4. Add a line to `CHANGELOG.md` for any change to the package.
5. Keep claims tied to evidence: if you state a number, link the file that produced it.

## Credit

People who make a substantive contribution are credited in the relevant release notes or on the site.
Authorship on a paper follows the criteria in `AUTHORSHIP.md`.

## Conduct

By taking part you agree to `CODE_OF_CONDUCT.md`.

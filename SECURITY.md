# Security policy

SAIL is a research tool that runs locally. It does not upload data, and the `sail-leakage` package
depends only on pandas and numpy.

## Reporting a vulnerability

Please do not open a public issue for a security problem. Use GitHub's private reporting:
**Security tab, then "Report a vulnerability"** on this repository. Include the version, what you
did, and what you expected. We aim to acknowledge a report within 7 days. This is a small research
project without a dedicated security team, so there is no guaranteed fix time.

## Patient data

Never post patient-level data in an issue, pull request or discussion, even de-identified. If you
believe patient-level data was committed to this repository, report it privately as above so it can be
removed from history. See `DATA_ACCESS.md`.

## Supported versions

Only the latest release is supported. The package is alpha (0.x); behavior may change between minor
versions and every change is listed in `CHANGELOG.md`.

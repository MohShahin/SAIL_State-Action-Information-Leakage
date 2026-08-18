#!/usr/bin/env python3
"""
render_query.py — safely substitute __SCRATCH_DATASET__ / __PROJECT_ID__ /
__HORIZON_HOURS__ placeholders in a query file, without touching anything
else (backticks, table identifiers, etc.).

This exists because manual find-replace previously broke queries/02_...sql by
stripping the backticks around the hyphenated `physionet-data` project id —
BigQuery requires that quoted (unquoted hyphens are a syntax error), and it's
an easy thing to lose by hand. Use this instead of editing the .sql files.

Usage:
    python3 render_query.py 02_vitals_labs_fio2.sql \\
        --scratch-dataset my-gcp-project.temp_dataset \\
        --horizon-hours 72

    # Print to stdout (default) or write to a file:
    python3 render_query.py 01_cohort.sql --scratch-dataset my-gcp-project.temp_dataset -o /tmp/out.sql

    # Then paste stdout into the BigQuery console, or:
    bq query --use_legacy_sql=false < /tmp/out.sql
"""
import argparse
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("query_file", help="e.g. 02_vitals_labs_fio2.sql")
    p.add_argument("--scratch-dataset", default=None, help="e.g. my-gcp-project.temp_dataset")
    p.add_argument("--project-id", default=None, help="e.g. my-gcp-project (rarely needed directly in these queries)")
    p.add_argument("--horizon-hours", default=None, help="e.g. 72")
    p.add_argument("-o", "--output", default=None, help="write to this file instead of stdout")
    args = p.parse_args()

    with open(args.query_file, "r") as f:
        sql = f.read()

    replacements = {
        "__SCRATCH_DATASET__": args.scratch_dataset,
        "__PROJECT_ID__": args.project_id,
        "__HORIZON_HOURS__": args.horizon_hours,
    }

    remaining = []
    for placeholder, value in replacements.items():
        if placeholder in sql:
            if value is None:
                remaining.append(placeholder)
            else:
                sql = sql.replace(placeholder, str(value))

    if remaining:
        print(f"warning: {args.query_file} still contains unresolved placeholder(s): "
              f"{', '.join(remaining)} — pass the matching flag to fill them in.",
              file=sys.stderr)

    if args.output:
        with open(args.output, "w") as f:
            f.write(sql)
        print(f"wrote {args.output}", file=sys.stderr)
    else:
        print(sql)


if __name__ == "__main__":
    main()

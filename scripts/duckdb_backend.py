"""DuckDB backend for the SAIL notebook: run the BigQuery notebook unchanged against a local
MIMIC-IV v3.1 built by mimic-code's buildmimic/duckdb/build_mimic.sh (schemas mimiciv_hosp,
mimiciv_icu, mimiciv_derived).

Select it with the environment variable SAIL_BACKEND=duckdb before starting the kernel. The
notebook's SQL strings are rewritten on the fly by bq_to_duckdb(), which covers exactly the
BigQuery constructs the notebook uses (table ids, backticks, UNNEST([STRUCT ...]) literals,
TIMESTAMP_DIFF as unit-boundary counting). The same rewrite, applied by hand, is committed under queries/duckdb/ for review.

Environment:
    SAIL_DUCKDB   path to the database file   (default ~/orcd/scratch/sail/mimic4.db)
    SAIL_THREADS  DuckDB threads              (default 8)
    SAIL_MEM      DuckDB memory limit         (default 24GB)
    SAIL_TMP      DuckDB spill directory      (default <db dir>/duckdb_tmp)
    SAIL_COHORT_STAYS  optional parquet or csv with a stay_id column; when set, notebook cell 5
                  replaces the Sepsis-3 condition of the cohort query with membership of that
                  list (sensitivity cohorts only, see override_sepsis3_stays). Unset = unchanged.

No patient-level data is written by this module except the cohort scratch table inside the
database file itself, which stays on the cluster.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import duckdb

DB_PATH = os.path.expanduser(os.environ.get("SAIL_DUCKDB", "~/orcd/scratch/sail/mimic4.db"))
SCRATCH_SCHEMA = "sail"
# raised by DuckDB when a table is missing; the notebook catches NotFound around the cohort query
NotFound = duckdb.CatalogException

_TABLE_MAP = [
    ("`physionet-data.mimiciv_3_1_icu.", "mimiciv_icu."),
    ("`physionet-data.mimiciv_3_1_hosp.", "mimiciv_hosp."),
    ("`physionet-data.mimiciv_3_1_derived.", "mimiciv_derived."),
]
_SCRATCH_RE = re.compile(r"`[^`]*\.sepsis_cohort`")
_TSDIFF_RE = re.compile(r"TIMESTAMP_DIFF\(\s*([^,]+?)\s*,\s*([^,]+?)\s*,\s*(MINUTE|HOUR)\s*\)")
_UNNEST_RE = re.compile(r"UNNEST\(\[.*?\]\)", re.S)
_STRUCT_RE = re.compile(r"STRUCT\(\s*(\d+)\s+AS\s+itemid\s*,\s*('[^']*')\s+AS\s+label\s*\)")

# The Sepsis-3 source inside notebook cell 5's cohort query, exactly as written there.
_SEPSIS3_SRC = "`physionet-data.mimiciv_3_1_derived.sepsis3`\n  WHERE sepsis3 IS TRUE"

_con: duckdb.DuckDBPyConnection | None = None


def bq_to_duckdb(sql: str) -> str:
    """Rewrite the notebook's BigQuery SQL to DuckDB.

    TIMESTAMP_DIFF(a, b, UNIT) maps to date_diff('unit', b, a), which counts unit boundaries
    crossed. MIMIC-IV's BigQuery columns are DATETIME, and on them the published BigQuery run
    behaved as boundary counting (DATETIME_DIFF semantics), not as the microsecond difference
    truncated toward zero that the TIMESTAMP documentation describes. Evidence on the published
    11,354-stay cohort: boundary counting reproduces the 4,850,246 physiology rows, all three
    Experiment 3 asserts to full precision and every Experiment 7 count; truncation gives
    4,894,707 rows and misses all of those. The two differ only when intime has seconds.
    """
    for a, b in _TABLE_MAP:
        sql = sql.replace(a, b)
    sql = _SCRATCH_RE.sub(f"{SCRATCH_SCHEMA}.sepsis_cohort", sql)
    sql = sql.replace("`", "")
    sql = _TSDIFF_RE.sub(
        lambda m: f"date_diff('{m.group(3).lower()}', {m.group(2)}, {m.group(1)})",
        sql,
    )

    def _unnest(m: re.Match) -> str:
        rows = _STRUCT_RE.findall(m.group(0))
        if not rows:
            raise ValueError("UNNEST literal not in the STRUCT(itemid, label) form the rewriter supports")
        return "(VALUES " + ", ".join(f"({i}, {l})" for i, l in rows) + ") AS t(itemid, label)"

    return _UNNEST_RE.sub(_unnest, sql)


def override_sepsis3_stays(sql: str, stays_path: str) -> str:
    """Replace the cohort query's Sepsis-3 source with an external stay_id list.

    Every other cohort condition (adult, first ICU stay, LOS >= 1 day, vasopressor) is kept, so
    the result is the published cohort query with Sepsis-3 membership taken from the file. This is
    how the BigQuery cohort (whose derived sepsis3 table was built from MIMIC-IV v2.2) is
    reproduced on a v3.1 database: pass the v2.2 sepsis3 stay_ids. The file must be .parquet or
    .csv with a stay_id column; every listed stay counts as Sepsis-3 positive.
    """
    path = Path(os.path.expanduser(stays_path)).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"SAIL_COHORT_STAYS file not found: {path}")
    if "'" in str(path):
        raise ValueError(f"SAIL_COHORT_STAYS path must not contain a quote: {path}")
    readers = {".parquet": "read_parquet", ".csv": "read_csv_auto"}
    if path.suffix.lower() not in readers:
        raise ValueError(f"SAIL_COHORT_STAYS must be .parquet or .csv, got {path.suffix}")
    if sql.count(_SEPSIS3_SRC) != 1:
        raise ValueError("cohort query does not contain exactly one Sepsis-3 source to override")
    return sql.replace(_SEPSIS3_SRC, f"{readers[path.suffix.lower()]}('{path}')")


def connect(db_path: str | None = None, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Open (once) the database with the thread and memory settings from the environment."""
    global _con
    if _con is not None:
        return _con
    path = os.path.expanduser(db_path or DB_PATH)
    if not Path(path).exists():
        raise FileNotFoundError(f"DuckDB database not found: {path} (set SAIL_DUCKDB)")
    tmp = os.environ.get("SAIL_TMP", str(Path(path).parent / "duckdb_tmp"))
    Path(tmp).mkdir(parents=True, exist_ok=True)
    _con = duckdb.connect(path, read_only=read_only)
    _con.execute(f"SET threads = {int(os.environ.get('SAIL_THREADS', '8'))}")
    _con.execute(f"SET memory_limit = '{os.environ.get('SAIL_MEM', '24GB')}'")
    _con.execute(f"SET temp_directory = '{tmp}'")
    if not read_only:
        _con.execute(f"CREATE SCHEMA IF NOT EXISTS {SCRATCH_SCHEMA}")
    return _con


def run_query(sql: str, label: str | None = None):
    """Same signature as the notebook's BigQuery run_query; returns a pandas DataFrame."""
    if label:
        print(f"Running: {label} ...")
    df = connect().execute(bq_to_duckdb(sql)).fetchdf()
    if label:
        print(f"  -> {df.shape[0]:,} rows, {df.shape[1]} cols")
    return df


def save_cohort(cohort_df) -> None:
    """Replace the cohort scratch table (the WRITE_TRUNCATE semantics of the BigQuery upload)."""
    con = connect()
    con.register("_sail_cohort_df", cohort_df)
    con.execute(f"CREATE OR REPLACE TABLE {SCRATCH_SCHEMA}.sepsis_cohort AS SELECT * FROM _sail_cohort_df")
    con.unregister("_sail_cohort_df")
    n = con.execute(f"SELECT COUNT(*) FROM {SCRATCH_SCHEMA}.sepsis_cohort").fetchone()[0]
    print(f"Cohort table saved to DuckDB schema {SCRATCH_SCHEMA} ({n:,} rows).")

"""The BigQuery-to-DuckDB rewriter must reproduce the notebook's SQL semantics on stub tables."""
import sys
from pathlib import Path

import pytest

duckdb = pytest.importorskip("duckdb")  # optional dependency: the DuckDB backend is not part of the sail package

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import duckdb_backend as be  # noqa: E402


def test_table_and_scratch_rewrite():
    sql = "SELECT * FROM `physionet-data.mimiciv_3_1_icu.icustays` JOIN `my-proj.temp_dataset.sepsis_cohort` USING(stay_id)"
    out = be.bq_to_duckdb(sql)
    assert out == "SELECT * FROM mimiciv_icu.icustays JOIN sail.sepsis_cohort USING(stay_id)"


def test_timestamp_diff_counts_unit_boundaries():
    con = duckdb.connect()
    sql = be.bq_to_duckdb("SELECT TIMESTAMP_DIFF(TIMESTAMP '2020-01-02 01:58:00', TIMESTAMP '2020-01-01 23:59:59', HOUR) AS h")
    assert "date_diff('hour', TIMESTAMP '2020-01-01 23:59:59', TIMESTAMP '2020-01-02 01:58:00')" in sql
    assert con.execute(sql).fetchone()[0] == 2          # two hour boundaries crossed (truncation gives 1)
    sql = be.bq_to_duckdb("SELECT TIMESTAMP_DIFF(TIMESTAMP '2020-01-01 23:30:00', TIMESTAMP '2020-01-02 00:00:00', HOUR) AS h")
    assert con.execute(sql).fetchone()[0] == -1         # 30 min before, across midnight: one boundary


def test_timestamp_diff_regression_bigquery_datetime_semantics():
    """Regression: the published BigQuery run behaved as boundary counting on MIMIC's DATETIME
    columns. Truncating instead moved the 11,354-stay physiology extraction from the published
    4,850,246 rows to 4,894,707 and broke the Experiment 3 asserts. The difference appears only
    when intime carries seconds, as MIMIC icustays.intime does; this pins that case."""
    con = duckdb.connect()
    intime = "TIMESTAMP '2150-03-01 10:14:37'"
    for charttime, minutes, hours in [
        ("2150-03-01 10:15:00", 1, 0),     # 23 s later: one minute boundary (truncation gives 0 min)
        ("2150-03-01 11:00:00", 46, 1),    # 45 m 23 s later: 46 minute boundaries, 1 hour boundary
        ("2150-03-04 10:00:00", 4306, 72), # just inside the 72 h horizon under boundary counting
        ("2150-03-04 11:00:00", 4366, 73), # 72 h 45 m later: 73 hour boundaries, outside the horizon
    ]:
        sql = be.bq_to_duckdb(
            f"SELECT TIMESTAMP_DIFF(TIMESTAMP '{charttime}', {intime}, MINUTE) AS m, "
            f"TIMESTAMP_DIFF(TIMESTAMP '{charttime}', {intime}, HOUR) AS h"
        )
        assert con.execute(sql).fetchone() == (minutes, hours), charttime


def test_unnest_struct_literal():
    sql = be.bq_to_duckdb("SELECT * FROM UNNEST([STRUCT(220045 AS itemid, 'heart_rate' AS label), STRUCT(220179 AS itemid, 'sbp' AS label)])")
    assert sql == "SELECT * FROM (VALUES (220045, 'heart_rate'), (220179, 'sbp')) AS t(itemid, label)"
    con = duckdb.connect()
    assert con.execute(sql).fetchall() == [(220045, "heart_rate"), (220179, "sbp")]


def test_unsupported_unnest_raises():
    with pytest.raises(ValueError):
        be.bq_to_duckdb("SELECT * FROM UNNEST([1, 2, 3])")


_COHORT_SQL = """
WITH vasopressor_stays AS (SELECT DISTINCT stay_id FROM `physionet-data.mimiciv_3_1_icu.inputevents`),
sepsis3_stays AS (
  SELECT DISTINCT stay_id
  FROM `physionet-data.mimiciv_3_1_derived.sepsis3`
  WHERE sepsis3 IS TRUE
)
SELECT v.stay_id FROM vasopressor_stays v INNER JOIN sepsis3_stays s USING(stay_id) ORDER BY 1
"""


def _stub_db():
    con = duckdb.connect()
    con.execute("CREATE SCHEMA mimiciv_icu; CREATE SCHEMA mimiciv_derived")
    con.execute("CREATE TABLE mimiciv_icu.inputevents AS SELECT * FROM (VALUES (1), (2), (3), (4)) t(stay_id)")
    con.execute("CREATE TABLE mimiciv_derived.sepsis3 AS SELECT * FROM (VALUES (1, TRUE), (2, FALSE)) t(stay_id, sepsis3)")
    return con


@pytest.mark.parametrize("suffix", [".parquet", ".csv"])
def test_cohort_override_replaces_only_the_sepsis3_source(tmp_path, suffix):
    con = _stub_db()
    assert con.execute(be.bq_to_duckdb(_COHORT_SQL)).fetchall() == [(1,)]
    stays = tmp_path / f"stays{suffix}"
    fmt = "PARQUET" if suffix == ".parquet" else "CSV, HEADER"
    con.execute(f"COPY (SELECT * FROM (VALUES (2), (3), (9)) t(stay_id)) TO '{stays}' (FORMAT {fmt})")
    sql = be.override_sepsis3_stays(_COHORT_SQL, str(stays))
    assert "sepsis3`" not in sql and sql.replace(sql[sql.index("FROM read_"):sql.index("\n)\nSELECT")], "") == \
        _COHORT_SQL.replace(_COHORT_SQL[_COHORT_SQL.index("FROM `physionet-data.mimiciv_3_1_derived"):_COHORT_SQL.index("\n)\nSELECT")], "")
    assert con.execute(be.bq_to_duckdb(sql)).fetchall() == [(2,), (3,)]   # vasopressor stays in the list


def test_cohort_override_rejects_bad_input(tmp_path):
    with pytest.raises(FileNotFoundError):
        be.override_sepsis3_stays(_COHORT_SQL, str(tmp_path / "missing.parquet"))
    other = tmp_path / "stays.txt"
    other.write_text("stay_id\n1\n")
    with pytest.raises(ValueError):
        be.override_sepsis3_stays(_COHORT_SQL, str(other))
    ok = tmp_path / "stays.csv"
    ok.write_text("stay_id\n1\n")
    with pytest.raises(ValueError):
        be.override_sepsis3_stays("SELECT 1", str(ok))

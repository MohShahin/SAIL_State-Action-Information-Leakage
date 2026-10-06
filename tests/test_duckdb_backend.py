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


def test_timestamp_diff_truncates_toward_zero_like_bigquery():
    con = duckdb.connect()
    sql = be.bq_to_duckdb("SELECT TIMESTAMP_DIFF(TIMESTAMP '2020-01-02 01:58:00', TIMESTAMP '2020-01-01 23:59:59', HOUR) AS h")
    assert con.execute(sql).fetchone()[0] == 1          # date_diff('hour') would give 2
    sql = be.bq_to_duckdb("SELECT TIMESTAMP_DIFF(TIMESTAMP '2020-01-01 23:30:00', TIMESTAMP '2020-01-02 00:00:00', HOUR) AS h")
    assert con.execute(sql).fetchone()[0] == 0          # 30 min before: truncates to 0, as BigQuery


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

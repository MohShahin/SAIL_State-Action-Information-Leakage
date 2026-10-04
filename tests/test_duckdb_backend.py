"""The BigQuery-to-DuckDB rewriter must reproduce the notebook's SQL semantics on stub tables."""
import sys
from pathlib import Path

import duckdb
import pytest

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

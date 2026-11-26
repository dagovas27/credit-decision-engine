"""Tests for the Spark-free part of the Bronze layer (names, paths, reader options)."""

import ast
from pathlib import Path

import pytest

from credit_engine.bronze import config
from credit_engine.schemas import ORIGINATION, PERFORMANCE

PIPELINE_SOURCE = Path(__file__).parents[1] / "src/credit_engine/bronze/pipeline.py"


def test_bronze_tables_match_the_architecture():
    assert config.bronze_table("credit", "origination") == "credit.bronze.loan_origination_raw"
    assert config.bronze_table("credit", "performance") == "credit.bronze.loan_performance_raw"


def test_bronze_table_uses_the_given_catalog():
    assert config.bronze_table("workspace", "origination").startswith("workspace.bronze.")


def test_unknown_file_type_raises():
    with pytest.raises(KeyError):
        config.bronze_table("credit", "servicing")


def test_each_file_type_has_its_schema():
    assert config.FILE_TYPES["origination"].schema is ORIGINATION
    assert config.FILE_TYPES["performance"].schema is PERFORMANCE


@pytest.mark.parametrize(
    ("root", "expected"),
    [
        ("/Volumes/credit/bronze/landing/freddie_mac", "/Volumes/credit/bronze/landing/freddie_mac/performance"),
        ("/Volumes/credit/bronze/landing/freddie_mac/", "/Volumes/credit/bronze/landing/freddie_mac/performance"),
    ],
)
def test_landing_path_points_to_one_folder_per_file_type(root, expected):
    assert config.landing_path(root, "performance") == expected


def test_autoloader_reads_headerless_pipe_delimited_csv():
    options = config.autoloader_options()
    assert options["cloudFiles.format"] == "csv"
    assert options["sep"] == "|"
    assert options["header"] == "false"


def test_autoloader_disables_quote_handling():
    # Freddie Mac fields are never quoted; a stray quote in a seller name must not
    # swallow the delimiters that follow it.
    assert config.autoloader_options()["quote"] == ""


def test_autoloader_keeps_unparseable_data_in_rescued_column():
    assert config.autoloader_options()["rescuedDataColumn"] == config.RESCUED_DATA_COLUMN


def test_autoloader_options_are_a_fresh_copy():
    config.autoloader_options()["sep"] = ","
    assert config.autoloader_options()["sep"] == "|"


def test_metadata_columns_are_prefixed_and_distinct_from_data_columns():
    metadata = [config.INGEST_TS_COLUMN, config.SOURCE_FILE_COLUMN, config.VINTAGE_COLUMN]
    assert metadata == ["_ingest_ts", "_source_file", "_vintage"]
    data_columns = set(ORIGINATION.column_names) | set(PERFORMANCE.column_names)
    assert not data_columns & set(metadata)


def test_vintage_expression_reads_the_year_from_loan_id():
    expr = config.vintage_expression()
    assert "substring(loan_id, 2, 2)" in expr
    assert expr.startswith("CAST(")


def test_pipeline_source_is_valid_python():
    # pipeline.py runs only inside Databricks (pyspark.pipelines is not installed
    # locally), so here we only check that it parses.
    ast.parse(PIPELINE_SOURCE.read_text(encoding="utf-8"))

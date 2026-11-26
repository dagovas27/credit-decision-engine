"""Spark-free settings for the Bronze layer: table names, landing paths, reader options.

Kept separate from ``pipeline.py`` so it can be unit-tested without a Spark runtime.
"""

from __future__ import annotations

from dataclasses import dataclass

from credit_engine.schemas import DELIMITER, ORIGINATION, PERFORMANCE, FileSchema

BRONZE_SCHEMA = "bronze"

# Pipeline configuration keys (set in resources/credit_engine_pipeline.yml).
CONF_CATALOG = "credit_engine.catalog"
CONF_LANDING_ROOT = "credit_engine.landing_root"

# Ingestion metadata added to every Bronze row. The leading underscore keeps them apart
# from the Freddie Mac columns.
INGEST_TS_COLUMN = "_ingest_ts"
SOURCE_FILE_COLUMN = "_source_file"
VINTAGE_COLUMN = "_vintage"
RESCUED_DATA_COLUMN = "_rescued_data"


@dataclass(frozen=True)
class FileType:
    schema: FileSchema
    landing_folder: str
    table: str


FILE_TYPES = {
    "origination": FileType(ORIGINATION, "origination", "loan_origination_raw"),
    "performance": FileType(PERFORMANCE, "performance", "loan_performance_raw"),
}

_AUTOLOADER_OPTIONS = {
    "cloudFiles.format": "csv",
    "sep": DELIMITER,
    "header": "false",
    # Freddie Mac never quotes fields. An empty quote character turns quote handling
    # off, so a stray " in a seller name cannot swallow the delimiters after it.
    "quote": "",
    # With an explicit schema, values that do not fit it (e.g. extra columns) are kept
    # here as JSON instead of being dropped.
    "rescuedDataColumn": RESCUED_DATA_COLUMN,
}


def bronze_table(catalog: str, file_type: str) -> str:
    """Fully qualified Bronze table name, e.g. ``credit.bronze.loan_origination_raw``."""
    return f"{catalog}.{BRONZE_SCHEMA}.{FILE_TYPES[file_type].table}"


def landing_path(landing_root: str, file_type: str) -> str:
    """Folder that Auto Loader watches for one file type."""
    return f"{landing_root.rstrip('/')}/{FILE_TYPES[file_type].landing_folder}"


def autoloader_options() -> dict[str, str]:
    """Auto Loader options for the headerless, pipe-delimited Freddie Mac files."""
    return dict(_AUTOLOADER_OPTIONS)


def vintage_expression(loan_id_column: str = "loan_id") -> str:
    """Spark SQL expression for the origination year encoded in the loan id.

    Loan ids follow ``PYYQnXXXXXXX``: characters 2-3 are the origination year. The
    dataset starts in 1999, so ``99`` maps to 1999 and everything else to 20YY.
    """
    yy = f"substring({loan_id_column}, 2, 2)"
    return f"CAST(CONCAT(CASE WHEN {yy} = '99' THEN '19' ELSE '20' END, {yy}) AS INT)"

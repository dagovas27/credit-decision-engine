"""Lakeflow Declarative Pipeline source: Bronze streaming tables fed by Auto Loader.

This file runs only inside a Databricks pipeline, which provides ``spark`` and the
``pyspark.pipelines`` module. The pipeline's ``root_path`` (``src/``) is on ``sys.path``,
so the project package can be imported. All testable logic lives in ``config.py``.

Each table is a streaming table: Auto Loader keeps a checkpoint of the files it has
already ingested, so a new pipeline update reads only files that arrived since the last
one. Re-running an update without new files adds no rows.
"""

from pyspark import pipelines as dp
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from credit_engine.bronze import config

CATALOG = spark.conf.get(config.CONF_CATALOG)  # noqa: F821 - provided by the pipeline
LANDING_ROOT = spark.conf.get(config.CONF_LANDING_ROOT)  # noqa: F821


def _read_landing(file_type: str) -> DataFrame:
    """Stream new files of one type from the landing Volume, as strings plus metadata."""
    file_spec = config.FILE_TYPES[file_type]
    return (
        spark.readStream.format("cloudFiles")  # noqa: F821
        .options(**config.autoloader_options())
        .schema(file_spec.schema.bronze_ddl())
        .load(config.landing_path(LANDING_ROOT, file_type))
        .select(
            "*",
            F.current_timestamp().alias(config.INGEST_TS_COLUMN),
            F.col("_metadata.file_path").alias(config.SOURCE_FILE_COLUMN),
            F.expr(config.vintage_expression()).alias(config.VINTAGE_COLUMN),
        )
    )


@dp.table(
    name=config.bronze_table(CATALOG, "origination"),
    comment="Freddie Mac origination files as delivered (all columns STRING) plus ingestion metadata.",
)
def loan_origination_raw() -> DataFrame:
    return _read_landing("origination")


@dp.table(
    name=config.bronze_table(CATALOG, "performance"),
    comment="Freddie Mac monthly performance files as delivered (all columns STRING) plus ingestion metadata.",
)
def loan_performance_raw() -> DataFrame:
    return _read_landing("performance")

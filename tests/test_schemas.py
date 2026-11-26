"""Tests for the Freddie Mac file schemas.

All sample lines here are synthetic: no real Freddie Mac records are stored in the repo.
"""

import re

import pytest

from credit_engine.schemas import ORIGINATION, PERFORMANCE, Field, FileSchema

SNAKE_CASE = re.compile(r"^[a-z][a-z0-9_]*$")

# Synthetic origination line: 31 fields, values made up but in the documented formats.
SYNTHETIC_ORIGINATION_LINE = "|".join(
    [
        "720", "201003", "N", "204002", "12345", "0", "1", "P", "80", "35",  # 1-10
        "200000", "80", "5.125", "R", "N", "FRM", "CO", "SF", "801",  # 11-19
        "F10Q10000001", "P", "360", "2", "SYNTHETIC LENDER", "", "",  # 20-26
        "9", "N", "9", "N", "9999",  # 27-31
    ]
)  # fmt: skip

# Synthetic performance line: 35 fields; the last one (cramdown costs) is empty,
# which is why real lines end with a pipe.
SYNTHETIC_PERFORMANCE_LINE = "|".join(
    [
        "F10Q10000001", "201003", "200000.00", "00", "0", "360",  # 1-6
        "", "", "", "",  # 7-10: defect date, modification, zero balance code and date
        "5.125", "0.00", "201003",  # 11-13
        "", "", "", "", "", "", "", "", "",  # 14-22: loss components and actual loss
        "0.00", "", "", "80",  # 23-26
        "", "", "", "", "",  # 27-31
        "200000.00", "7", "SYNTHETIC SERVICER", "",  # 32-35
    ]
)  # fmt: skip


@pytest.mark.parametrize(
    ("schema", "expected_columns"),
    [(ORIGINATION, 31), (PERFORMANCE, 35)],
)
def test_column_count_matches_july_2026_layout(schema, expected_columns):
    assert len(schema) == expected_columns


@pytest.mark.parametrize("schema", [ORIGINATION, PERFORMANCE])
def test_positions_are_contiguous_from_one(schema):
    assert [f.position for f in schema.fields] == list(range(1, len(schema) + 1))


@pytest.mark.parametrize("schema", [ORIGINATION, PERFORMANCE])
def test_column_names_are_unique_snake_case(schema):
    names = schema.column_names
    assert len(names) == len(set(names))
    assert all(SNAKE_CASE.match(n) for n in names), names


def test_loan_id_is_the_join_key_in_both_files():
    assert ORIGINATION.position_of("loan_id") == 20
    assert PERFORMANCE.position_of("loan_id") == 1


def test_key_performance_positions():
    assert PERFORMANCE.position_of("reporting_period") == 2
    assert PERFORMANCE.position_of("delinquency_status") == 4
    assert PERFORMANCE.position_of("zero_balance_code") == 9
    assert PERFORMANCE.position_of("payment_deferral_flag") == 25
    assert PERFORMANCE.position_of("disaster_delinquency_flag") == 29
    assert PERFORMANCE.position_of("borrower_assistance_plan") == 30


def test_position_of_unknown_column_raises():
    with pytest.raises(KeyError):
        ORIGINATION.position_of("not_a_column")


@pytest.mark.parametrize("schema", [ORIGINATION, PERFORMANCE])
def test_bronze_ddl_keeps_every_column_as_string(schema):
    ddl = schema.bronze_ddl()
    parts = [p.strip() for p in ddl.split(",")]
    assert parts == [f"{name} STRING" for name in schema.column_names]


def test_parse_line_maps_values_to_column_names():
    record = ORIGINATION.parse_line(SYNTHETIC_ORIGINATION_LINE)
    assert record["fico_score"] == "720"
    assert record["loan_id"] == "F10Q10000001"
    assert record["seller_name"] == "SYNTHETIC LENDER"
    assert record["vantage_score"] == "9999"


def test_parse_line_keeps_trailing_empty_field():
    record = PERFORMANCE.parse_line(SYNTHETIC_PERFORMANCE_LINE)
    assert len(record) == 35
    assert record["servicer_name"] == "SYNTHETIC SERVICER"
    assert record["bankruptcy_cramdown_costs"] == ""


def test_parse_line_rejects_wrong_column_count():
    with pytest.raises(ValueError, match="expected 35 fields, got 34"):
        PERFORMANCE.parse_line(SYNTHETIC_PERFORMANCE_LINE.rsplit("|", 1)[0])


def test_file_schema_rejects_gaps_in_positions():
    fields = (
        Field(1, "a", "A", "Alpha", 1),
        Field(3, "c", "C", "Alpha", 1),
    )
    with pytest.raises(ValueError, match="contiguous"):
        FileSchema("broken", fields)


def test_file_schema_rejects_duplicate_names():
    fields = (
        Field(1, "a", "A", "Alpha", 1),
        Field(2, "a", "A again", "Alpha", 1),
    )
    with pytest.raises(ValueError, match="duplicate"):
        FileSchema("broken", fields)

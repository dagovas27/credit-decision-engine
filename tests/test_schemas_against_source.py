"""Check the schemas against the official layout and the local data files.

The Freddie Mac files are never stored in the repository, so these tests run only on a
machine that has them (default ``~/Documents/data/freddie_mac``, override with the
``FREDDIE_MAC_DATA_DIR`` environment variable). Elsewhere, for example in CI, they skip.
"""

import os
from itertools import islice
from pathlib import Path

import pytest

from credit_engine.schemas import ORIGINATION, PERFORMANCE

DATA_DIR = Path(
    os.environ.get("FREDDIE_MAC_DATA_DIR", Path.home() / "Documents/data/freddie_mac")
)
LAYOUT_FILE = DATA_DIR / "file_layout_july_2026.xlsx"
LINES_PER_FILE = 1000

needs_data = pytest.mark.skipif(
    not DATA_DIR.is_dir(), reason=f"Freddie Mac data not found at {DATA_DIR}"
)


def _layout_rows(sheet_name):
    openpyxl = pytest.importorskip("openpyxl")
    if not LAYOUT_FILE.is_file():
        pytest.skip(f"layout not found at {LAYOUT_FILE}")
    workbook = openpyxl.load_workbook(LAYOUT_FILE, read_only=True, data_only=True)
    rows = []
    for row in workbook[sheet_name].iter_rows(values_only=True):
        if isinstance(row[0], int):  # data rows start with the field position
            position, name, data_type, max_length = row[:4]
            rows.append((position, name.strip(), data_type.strip(), int(max_length)))
    return rows


@needs_data
@pytest.mark.parametrize(
    ("schema", "sheet_name"),
    [
        (ORIGINATION, "Origination Data File"),
        (PERFORMANCE, "Monthly Performance Data File"),
    ],
)
def test_schema_matches_official_layout(schema, sheet_name):
    expected = _layout_rows(sheet_name)
    actual = [(f.position, f.layout_name, f.layout_type, f.max_length) for f in schema.fields]
    assert actual == expected


@needs_data
@pytest.mark.parametrize(
    ("schema", "pattern"),
    [(ORIGINATION, "sample_*/sample_orig_*.txt"), (PERFORMANCE, "sample_*/sample_perf_*.txt")],
)
def test_local_files_have_the_schema_column_count(schema, pattern):
    files = sorted(DATA_DIR.glob(pattern))
    assert files, f"no files match {pattern} in {DATA_DIR}"
    for path in files:
        with path.open(encoding="utf-8") as handle:
            for line in islice(handle, LINES_PER_FILE):
                schema.parse_line(line)  # raises ValueError on a wrong column count

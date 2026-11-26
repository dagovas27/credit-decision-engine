"""Building blocks for the Freddie Mac file layouts.

The source files are pipe-delimited and have no header row, so the column order defined
here is the only link between a value and its meaning.
"""

from __future__ import annotations

from dataclasses import dataclass

DELIMITER = "|"


@dataclass(frozen=True)
class Field:
    """One column of a Freddie Mac file, as described in the official file layout."""

    position: int  # 1-based position in the file
    name: str  # snake_case column name used in the lakehouse
    layout_name: str  # attribute name in file_layout_july_2026.xlsx
    layout_type: str  # data type and format as written in the layout
    max_length: int  # maximum length according to the layout


class FileSchema:
    """Ordered, validated list of fields for one file type."""

    def __init__(self, name: str, fields: tuple[Field, ...]):
        positions = [f.position for f in fields]
        if positions != list(range(1, len(fields) + 1)):
            raise ValueError(f"{name}: positions must be contiguous from 1, got {positions}")
        names = [f.name for f in fields]
        duplicates = sorted({n for n in names if names.count(n) > 1})
        if duplicates:
            raise ValueError(f"{name}: duplicate column names {duplicates}")

        self.name = name
        self.fields = fields
        self._position_by_name = {f.name: f.position for f in fields}

    def __len__(self) -> int:
        return len(self.fields)

    @property
    def column_names(self) -> list[str]:
        return [f.name for f in self.fields]

    def position_of(self, column: str) -> int:
        """1-based position of a column; raises KeyError for unknown columns."""
        return self._position_by_name[column]

    def bronze_ddl(self) -> str:
        """Spark DDL schema for Bronze: every column as STRING.

        Bronze stores the data exactly as delivered. Typing happens in Silver, so a
        malformed value is quarantined there instead of being lost at ingestion.
        """
        return ", ".join(f"{name} STRING" for name in self.column_names)

    def parse_line(self, line: str) -> dict[str, str]:
        """Split one raw line into a {column: value} dict, checking the column count."""
        values = line.rstrip("\r\n").split(DELIMITER)
        if len(values) != len(self.fields):
            raise ValueError(
                f"{self.name}: expected {len(self.fields)} fields, got {len(values)}"
            )
        return dict(zip(self.column_names, values, strict=True))

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass
class ExtractedEmployeeRow:
    row_index: int
    fields: dict[str, Optional[str]]


@dataclass
class ParsedDocument:
    doc_type: str
    parser_name: str
    parser_version: str
    fields: dict[str, Optional[str]]
    rows: list[ExtractedEmployeeRow]


class DocumentParser(Protocol):
    def parse(self, doc_type: str, filename: str) -> ParsedDocument:
        """Parse one document and return aggregate fields plus row-level data."""

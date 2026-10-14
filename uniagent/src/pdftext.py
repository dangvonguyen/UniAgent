"""PDF text that keeps side-by-side blocks apart and table rows together."""

import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

_XHTML = "{http://www.w3.org/1999/xhtml}"
CELL_SEPARATOR = " | "


@dataclass
class _Block:
    x: float
    x_max: float
    y: float
    line_height: float
    lines: list[str]
    line_ys: list[float]


def pdf_text(pdf: Path) -> str:
    xml = subprocess.run(
        ["pdftotext", "-bbox-layout", str(pdf), "-"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    root = ET.fromstring(xml)
    return "\f".join(
        _page_text(_attach_line_cells(_blocks(page)))
        for page in root.iter(f"{_XHTML}page")
    )


def _blocks(page: ET.Element) -> list[_Block]:
    blocks = []
    for block in page.iter(f"{_XHTML}block"):
        lines = [
            (" ".join(word.text or "" for word in line.iter(f"{_XHTML}word")), line)
            for line in block.iter(f"{_XHTML}line")
        ]
        lines = [(text, line) for text, line in lines if text.strip()]
        if not lines:
            continue
        first_line = lines[0][1]
        blocks.append(
            _Block(
                x=float(block.get("xMin")),
                x_max=float(block.get("xMax")),
                y=float(block.get("yMin")),
                line_height=float(first_line.get("yMax"))
                - float(first_line.get("yMin")),
                lines=[text for text, _ in lines],
                line_ys=[float(line.get("yMin")) for _, line in lines],
            )
        )
    return blocks


def _attach_line_cells(blocks: list[_Block]) -> list[_Block]:
    kept = []
    for block in blocks:
        target = None
        if len(block.lines) == 1 and not _continues_column(block, blocks):
            beside = [
                (other, i)
                for other in blocks
                if len(other.lines) > 1
                and other.x_max <= block.x
                and abs(other.line_height - block.line_height) < block.line_height / 10
                for i, y in enumerate(other.line_ys[1:], start=1)
                if abs(y - block.y) < block.line_height / 2
            ]
            if beside:
                target = max(
                    beside, key=lambda pair: pair[0].x_max
                )  # nearest to the left
        if target is None:
            kept.append(block)
        else:
            other, i = target
            other.lines[i] += CELL_SEPARATOR + block.lines[0]
    return kept


def _continues_column(block: _Block, blocks: list[_Block]) -> bool:
    """Whether a multi-line block ends just above this one, overlapping it horizontally."""
    return any(
        len(other.lines) > 1
        and other.x < block.x_max
        and block.x < other.x_max
        and 0 < block.y - other.line_ys[-1] < 2 * block.line_height + other.line_height
        for other in blocks
    )


def _rows(blocks: list[_Block]) -> list[list[_Block]]:
    """Blocks grouped by starting height, top to bottom, each row left to right."""
    rows: list[list[_Block]] = []
    for block in sorted(blocks, key=lambda b: b.y):
        row = rows[-1] if rows else None
        if row and abs(block.y - row[0].y) < row[0].line_height / 2:
            row.append(block)
        else:
            rows.append([block])
    return [sorted(row, key=lambda b: b.x) for row in rows]


def _page_text(blocks: list[_Block]) -> str:
    parts: list[str] = []  # paragraphs: a block, or a run of table rows
    table: list[str] = []
    for row in _rows(blocks):
        if len(row) > 1 and sum(len(b.lines) > 1 for b in row) <= 1:
            table.append(CELL_SEPARATOR.join(" ".join(b.lines) for b in row))
            continue
        if table:
            parts.append("\n".join(table))
            table = []
        parts.extend("\n".join(b.lines) for b in row)
    if table:
        parts.append("\n".join(table))
    return "\n\n".join(parts)

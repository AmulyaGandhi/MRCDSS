"""Read-only parser for HMIS 'Data Item Wise Report' XLSX workbooks.

structure (observed 2020-21 .. 2024-25 files, 0-based row indices):
  r0  : "Data ItemWise Report for <State>"
  r1  : 'Provisional Figures for - <FY> and Month - ...'
  r2  : 'Status As On: <timestamp>'
  r3  : 'Total [(A+B) OR (C+D)] ...' note
  r4  : (blank)
  r5  : 'Districts' label (at column E = index 4)
  r6  : district names, first group = State name (index 4, 9, 14, ...)
  r7  : sub-column headers 'Total [(A+B) or (C+D)]','Public [A]','Private [B]',
        'Urban [C]','Rural [D]' repeating every 5 columns from index 4
  r8+: data items; B=item code, C=item label, then per-district 5-col groups
       (col A is blank on continuation rows)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

import openpyxl

_NUM_RE = re.compile(r"^-?\d+(\.\d+)?$")


def isnum(v) -> bool:
    if isinstance(v, (int, float)):
        return True
    if isinstance(v, str):
        return bool(_NUM_RE.match(v.strip()))
    return False


def _cell_str(v) -> str:
    return "" if v is None else str(v).strip()


@dataclass
class SubCol:
    col: int
    name: str  # Total / Public / Private / Urban / Rural


@dataclass
class DistrictGroup:
    name: str
    total: SubCol
    public: SubCol
    private: SubCol
    urban: SubCol
    rural: SubCol


@dataclass
class Item:
    row: int
    module: Optional[str]
    code: str
    label: str
    values: dict = field(default_factory=dict)  # group name -> Total value
    raw_row: tuple = field(default_factory=tuple)


@dataclass
class WorkSheet:
    path: str
    sheet: str
    title: Optional[str]
    status_row2: Optional[str]
    status_row3: Optional[str]
    note_row4: Optional[str]
    districts_label: Optional[str]
    groups: list[DistrictGroup]  # group 0 = State column
    items: list[Item]
    nrows: int = 0
    ncols: int = 0

    @property
    def districts(self) -> list[str]:
        """District names excluding the leading State-column group (group 0)."""
        return [g.name for g in self.groups[1:]]


def load(path: str, sheet: str = "Data Item Wise Report") -> WorkSheet:
    """Load a workbook; non read_only (HMIS files have no usable <dimension>)."""
    wb = openpyxl.load_workbook(path, read_only=False, data_only=True)
    if sheet not in wb.sheetnames:
        names = wb.sheetnames
        wb.close()
        raise ValueError(f"sheet {sheet!r} not in {path}: {names}")
    ws = wb[sheet]
    rows = list(ws.iter_rows(values_only=True))
    ncols = ws.max_column
    wb.close()

    # --- locate sub-column header row: 'Total...' followed by 'Public [A]' ---
    sub_idx = None
    start_col = None
    for i, row in enumerate(rows[:14]):
        cells = [_cell_str(v) for v in row]
        for c in range(len(cells) - 2):
            if cells[c].startswith("Total") and cells[c + 1].startswith("Public") \
                    and cells[c + 2].startswith("Private"):
                sub_idx = i
                start_col = c
                break
        if sub_idx is not None:
            break
    title = _cell_str(rows[0][0]) if rows else None
    if sub_idx is None:
        return WorkSheet(path, sheet, title,
                         _cell_str(rows[1][0]) if len(rows) > 1 else None,
                         _cell_str(rows[2][0]) if len(rows) > 2 else None,
                         _cell_str(rows[3][0]) if len(rows) > 3 else None,
                         None, [], [], len(rows), ncols)

    name_row = rows[sub_idx - 1]
    sub_row = rows[sub_idx]
    districts_label = _cell_str(rows[sub_idx - 2][0]) if sub_idx >= 2 else None

    groups: list[DistrictGroup] = []
    c = start_col
    while c + 4 < ncols:
        name = _cell_str(name_row[c]) if c < len(name_row) else ""
        sc = [(_cell_str(sub_row[c + k]) if c + k < len(sub_row) else "") for k in range(5)]
        if not name:
            break
        groups.append(DistrictGroup(
            name=name,
            total=SubCol(c, sc[0] or "Total"),
            public=SubCol(c + 1, sc[1] or "Public"),
            private=SubCol(c + 2, sc[2] or "Private"),
            urban=SubCol(c + 3, sc[3] or "Urban"),
            rural=SubCol(c + 4, sc[4] or "Rural"),
        ))
        c += 5

    items: list[Item] = []
    for i in range(sub_idx + 1, len(rows)):
        row = rows[i]
        module = _cell_str(row[0]) if len(row) > 0 else ""
        code = _cell_str(row[1]) if len(row) > 1 else ""
        label = _cell_str(row[2]) if len(row) > 2 else ""
        if not module and not code and not label:
            continue
        it = Item(row=i + 1, module=module or None, code=code, label=label,
                  raw_row=row)
        for g in groups:
            v = None
            if g.total.col < len(row):
                v = row[g.total.col]
            it.values[g.name] = v
        items.append(it)

    return WorkSheet(path, sheet, title,
                     _cell_str(rows[1][0]) if len(rows) > 1 else None,
                     _cell_str(rows[2][0]) if len(rows) > 2 else None,
                     _cell_str(rows[3][0]) if len(rows) > 3 else None,
                     districts_label, groups, items,
                     nrows=len(rows), ncols=ncols)


def find_items(ws: WorkSheet, *patterns: str) -> list[Item]:
    """Find items whose code OR label matches any regex pattern."""
    res = []
    for it in ws.items:
        hay = f"{it.module or ''}|{it.code}|{it.label}"
        if any(re.search(p, hay, re.I) for p in patterns):
            res.append(it)
    return res
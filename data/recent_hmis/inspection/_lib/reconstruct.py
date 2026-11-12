"""Reconstruction helpers for the six MRCDSS indicators from raw HMIS files."""
from __future__ import annotations

import re
from typing import Optional

from hmis_reader import WorkSheet


def num(v) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if re.fullmatch(r"-?\d+(\.\d+)?", s):
        return float(s)
    return None


def item_by_code(ws: WorkSheet, code: str):
    c = code.strip()
    for it in ws.items:
        if it.code.strip(" '") == c:
            return it
    return None


def district_values(it, groups) -> dict:
    """District-name -> numeric Total value (group 0 / state column excluded)."""
    out = {}
    for g in groups[1:]:
        v = num(it.values.get(g.name))
        out[g.name] = v
    return out


def state_value(it) -> Optional[float]:
    if not it:
        return None
    if len(it.values) == 0:
        return None
    return num(it.values.get("TOTAL")) if "TOTAL" in it.values else None


def ratio(n, d) -> Optional[float]:
    if n is None or d is None or d == 0:
        return None
    return n / d * 100.0


def indicator(ws: WorkSheet, num_codes, den_codes, sum_num=False) -> dict:
    """Compute district-level ratio numerator/denominator for a set of codes."""
    num_items = [item_by_code(ws, c) for c in num_codes]
    den_items = [item_by_code(ws, c) for c in den_codes]
    if not num_items or not den_items:
        return {"missing": True}
    # sum numerators at district level (or take single item)
    res = {"missing": any(x is None for x in (num_items + den_items))}
    if res["missing"]:
        return res
    nums = district_values(num_items[0], ws.groups)
    dens = district_values(den_items[0], ws.groups)
    if sum_num or len(num_items) > 1:
        nn = {}
        for d in nums:
            s = 0.0
            has = False
            for it in num_items:
                v = district_values(it, ws.groups).get(d)
                if v is not None:
                    s += v
                    has = True
            nn[d] = s if has else None
        nums = nn
    if len(den_items) > 1:
        dd = {}
        for d in dens:
            s = 0.0
            has = False
            for it in den_items:
                v = district_values(it, ws.groups).get(d)
                if v is not None:
                    s += v
                    has = True
            dd[d] = s if has else None
        dens = dd
    vals = {}
    for d in nums:
        vals[d] = ratio(nums[d], dens.get(d))
    return {"missing": False, "numerators": nums, "denominators": dens, "values": vals}
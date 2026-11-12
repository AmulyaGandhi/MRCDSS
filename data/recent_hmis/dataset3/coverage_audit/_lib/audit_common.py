"""Shared helpers for the Dataset 3 coverage/churn audit.

Read-only on dataset1.csv, dataset2.csv, dataset3_recent_hmis.csv and the
existing Dataset 3 artifacts.
"""
from __future__ import annotations

import os
import re

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
D3 = os.path.join(ROOT, "data", "recent_hmis", "dataset3", "dataset3_recent_hmis.csv")
AUDIT = os.path.join(ROOT, "data", "recent_hmis", "dataset3", "coverage_audit")


def norm(key):
    # same alias-normalisation used across Dataset 3 (see build_reports.norm)
    s = re.sub(r"[&]", "and", (key or "").lower())
    return re.sub(r"[^a-z0-9]", "", s)


def lev(a, b):
    if len(a) < len(b):
        a, b = b, a
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def load_reference():
    d1 = pd.read_csv(os.path.join(ROOT, "dataset1.csv"), dtype=str)
    d2 = pd.read_csv(os.path.join(ROOT, "dataset2.csv"), dtype=str)
    ref = pd.concat([d1[["State", "District", "Year"]],
                     d2[["State", "District", "Year"]]], ignore_index=True)
    ref["Skey"] = [norm(s) for s in ref["State"]]
    ref["Dkey"] = [norm(d) for d in ref["District"]]
    return ref


def load_ds3():
    df = pd.read_csv(D3, dtype=str, na_values=[""])
    df["Skey"] = [norm(s) for s in df["State"]]
    df["Dkey"] = [norm(d) for d in df["District"]]
    return df


def reference_units(ref):
    """(state_norm -> {district_norm: {State, District, First_Hist, Last_Hist, N_Hist}})."""
    out = {}
    gb = ref.groupby(["Skey", "Dkey"])
    for (sk, dk), g in gb:
        out.setdefault(sk, {})[dk] = {
            "State": g["State"].iloc[-1],
            "District": g["District"].iloc[-1],
            "First_Hist": g["Year"].min(),
            "Last_Hist": g["Year"].max(),
            "N_Hist": g["Year"].nunique(),
        }
    return out


def ds3_units(ds):
    """Unique (State,District) -> {First, Last, N, Years, Skey, Dkey}."""
    gb = ds.groupby(["State", "District"])
    out = {}
    for (st, dist), g in gb:
        out[(st, dist)] = {
            "State": st,
            "District": dist,
            "Skey": g["Skey"].iloc[0],
            "Dkey": g["Dkey"].iloc[0],
            "First": g["Year"].min(),
            "Last": g["Year"].max(),
            "N": g["Year"].nunique(),
            "Years": tuple(sorted(g["Year"].unique())),
        }
    return out
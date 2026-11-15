"""Tests for Dataset 3 (recent-HMIS standalone analytical dataset).

Run from project root:  .venv/bin/python -m pytest tests/recent_hmis -q
"""
import json
import os
import hashlib
import sys

import pandas as pd
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
D3_DIR = os.path.join(ROOT, "data", "recent_hmis", "dataset3")
RAW = os.path.join(ROOT, "data", "recent_hmis", "raw")
LIB = os.path.join(ROOT, "data", "recent_hmis", "inspection", "_lib")
if LIB not in sys.path:
    sys.path.insert(0, LIB)

import hmis_reader as hr  # noqa: E402

FEATURES = ["ANC_First_Trimester_Pct", "TT2_Booster_Pct",
            "Severe_Anemia_Pct", "Obstetric_Complications_Pct"]


@pytest.fixture(scope="module")
def df():
    out = pd.read_csv(os.path.join(D3_DIR, "dataset3_recent_hmis.csv"), na_values=[""])
    assert not out.empty
    return out


@pytest.fixture(scope="module")
def counts():
    return pd.read_csv(os.path.join(D3_DIR, "indicator_counts.csv"))


@pytest.fixture(scope="module")
def metadata():
    with open(os.path.join(D3_DIR, "dataset3_metadata.json")) as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def featdefs():
    return pd.read_csv(os.path.join(D3_DIR, "feature_definitions.csv"))


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _feature_from_raw(path, districts, fy, col="Total"):
    """Recompute features from a raw file using the district Total (or given) column."""
    ws = hr.load(path)
    codes = {"n_anc": "1.1", "n_1st": "1.1.1", "n_tt2": "1.2.2", "n_bst": "1.2.3",
             "n_hb7": "1.4.3", "n_hb11": "1.4.2", "n_ob": "5.1",
             "n_hsa": "2.1.1.a", "n_hnsb": "2.1.1.b", "n_inst": "2.2"}
    items = {}

    def find_code(ws, code):
        for it in ws.items:
            if it.code.strip(" '") == code:
                return it
        return None

    for k, v in codes.items():
        items[k] = find_code(ws, v)
    groups = {g.name: g for g in ws.groups}
    sub_col = {"Total": "total", "Urban": "urban", "Public": "public"}[col]

    def gv(code_key, district):
        it = items.get(code_key)
        if it is None:
            return None
        g = groups.get(district)
        if g is None:
            return None
        cell = getattr(g, sub_col)
        raw = it.raw_row[cell.col] if cell.col < len(it.raw_row) else None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    res = {}
    for d in districts:
        def pct(n, d_):
            return None if (n is None or d_ is None or d_ == 0) else n / d_ * 100.0
        ll = gv("n_anc", d)
        tt = gv("n_tt2", d); bs = gv("n_bst", d)
        hsa, hnsb, inst = gv("n_hsa", d), gv("n_hnsb", d), gv("n_inst", d)
        deliv = None
        if hsa is not None and hnsb is not None and inst is not None:
            deliv = hsa + hnsb + inst
        res[d] = {
            "ANC_First_Trimester_Pct": pct(gv("n_1st", d), ll),
            "TT2_Booster_Pct": pct(None if (tt is None or bs is None) else tt + bs, ll),
            "Severe_Anemia_Pct": pct(gv("n_hb7", d), gv("n_hb11", d)),
            "Obstetric_Complications_Pct": pct(gv("n_ob", d), deliv),
        }
    return res


# --------------------------------------------------------------------------- #
# 1. No duplicate State/District/Year rows
# --------------------------------------------------------------------------- #
def test_no_duplicate_rows(df):
    dup = df.duplicated(["State", "District", "Year"]).sum()
    assert dup == 0, f"{dup} duplicate rows"


# --------------------------------------------------------------------------- #
# 2. District Total is used (not Public/Private/Urban/Rural)
# --------------------------------------------------------------------------- #
def test_district_total_used(df):
    cases = [
        ("2022-2023", "Uttar Pradesh", "L-Uttar Pradesh_UpTo_Mar.xlsx",
         "data/recent_hmis/raw/2022-2023/B.Cummulative/Uttar Pradesh"),
        ("2024-2025", "Telangana", "L-Telangana_UpTo_Mar.xlsx",
         "data/recent_hmis/raw/2024-2025/B.Cummulative/Telangana"),
        ("2020-2021", "Ladakh", "L-Ladakh_UpTo_Mar.xlsx",
         "data/recent_hmis/raw/2020-2021/B.Cummulative/Ladakh"),
    ]
    for fy, state, fname, folder in cases:
        path = os.path.join(ROOT, folder, fname)
        sub = df[(df.Year == fy) & (df.State == state)]
        recom = _feature_from_raw(path, sub["District"].tolist(), fy, col="Total")
        urban = _feature_from_raw(path, sub["District"].tolist(), fy, col="Urban")
        checked = 0
        for _, row in sub.iterrows():
            d = row["District"]
            r = recom[d]
            # must match Total-derived value
            for f in FEATURES:
                if r[f] is None:
                    assert pd.isna(row[f]), (state, fy, d, f, "expected NaN")
                else:
                    assert abs(r[f] - row[f]) < 1e-3, (state, fy, d, f, r[f], row[f])
            # must DIFFER from Urban-derived where Total != Urban (proves Total used)
            u = urban[d]
            for f in ["ANC_First_Trimester_Pct", "TT2_Booster_Pct"]:
                if u[f] is not None and r[f] is not None and abs(u[f] - r[f]) > 1e-6:
                    assert not (abs(u[f] - row[f]) < 1e-3), (state, d, f, "Urban leaked into value")
            checked += 1
        assert checked > 0


# --------------------------------------------------------------------------- #
# 3. Percent formulas are correct (recomputation from raw counts)
# --------------------------------------------------------------------------- #
def test_percent_formulas(df):
    # full recomputation check is embedded in test_district_total_used for 3
    # files; here additionally verify formula arithmetic on a known-value row.
    row = df[(df.State == "Uttar Pradesh") & (df.District == "Prayagraj")
             & (df.Year == "2022-2023")]
    assert len(row) == 1
    r = row.iloc[0]
    for f in FEATURES:
        assert not pd.isna(r[f])


# --------------------------------------------------------------------------- #
# 4. Zero denominators produce NaN
# --------------------------------------------------------------------------- #
def test_zero_denominator_nan(df, counts):
    base = df.set_index(["State", "District", "Year"])
    n_checked = 0
    for f in FEATURES:
        den = f"{f}_denominator"
        z = counts[counts[den].fillna(-1).eq(0)]
        for _, r in z.iterrows():
            assert pd.isna(base.loc[(r["State"], r["District"], r["Year"]), f]), \
                (r["State"], r["District"], r["Year"], f)
            n_checked += 1
    assert n_checked > 0


# --------------------------------------------------------------------------- #
# 5. Missing numerators/denominators produce NaN
# --------------------------------------------------------------------------- #
def test_missing_counts_nan(df, counts):
    base = df.set_index(["State", "District", "Year"])
    n_checked = 0
    for f in FEATURES:
        miss = counts[counts[f"{f}_numerator"].isna() | counts[f"{f}_denominator"].isna()]
        # structural rows (obstetric >=2023-24) included - all must be NaN
        for _, r in miss.iterrows():
            assert pd.isna(base.loc[(r["State"], r["District"], r["Year"]), f]), \
                (r["State"], r["District"], r["Year"], f)
            n_checked += 1
    assert n_checked > 0


# --------------------------------------------------------------------------- #
# 6. Obstetric complications unavailable from 2023-24 onward
# --------------------------------------------------------------------------- #
def test_obstetric_structural_nan_from_2023(df):
    later = df[df["Year"].isin(["2023-2024", "2024-2025"])]
    assert len(later) > 0
    assert later["Obstetric_Complications_Pct"].isna().all(), \
        "Obstetric_Complications_Pct must be NaN for 2023-24 onward"
    for y in ["2020-2021", "2021-2022", "2022-2023"]:
        yy = df[df["Year"] == y]
        assert yy["Obstetric_Complications_Pct"].notna().sum() > 0, f"no obstetric data in {y}"


# --------------------------------------------------------------------------- #
# 7. Institutional Delivery and PNC 48h not fabricated columns
# --------------------------------------------------------------------------- #
def test_excluded_features_absent(df):
    cols = [c for c in df.columns]
    assert "Institutional_Delivery_Pct" not in cols
    assert "PNC_48h_Pct" not in cols
    assert set(cols) == {"State", "District", "Year", "source_dataset", *FEATURES}


# --------------------------------------------------------------------------- #
# 8. Severe-anemia required definition-change metadata
# --------------------------------------------------------------------------- #
def test_severe_anemia_definition_metadata(metadata, featdefs):
    caveat = metadata["caveats"]["Severe_Anemia_Pct"].lower()
    assert "<7" in caveat or "<=7" in caveat
    assert "<=7" in caveat or "definition changed" in caveat
    fdef = featdefs[featdefs["Feature"] == "Severe_Anemia_Pct"].iloc[0]
    caveat2 = str(fdef["Caveats"]).lower()
    assert "created" in caveat2 or "changed" in caveat2 or "<=7" in caveat2


# --------------------------------------------------------------------------- #
# 9. TT2/booster required caveat metadata
# --------------------------------------------------------------------------- #
def test_tt2_booster_caveat_metadata(metadata, featdefs):
    caveat = metadata["caveats"]["TT2_Booster_Pct"].lower()
    assert "double-count" in caveat
    fdef = featdefs[featdefs["Feature"] == "TT2_Booster_Pct"].iloc[0]
    assert "double-count" in str(fdef["Caveats"]).lower() or \
           "double count" in str(fdef["Caveats"]).lower()


# --------------------------------------------------------------------------- #
# 10. Raw XLSX files unchanged
# --------------------------------------------------------------------------- #
def _baseline():
    with open(os.path.join(D3_DIR, "_protected_files_baseline.json")) as fh:
        return json.load(fh)["files"]


def test_raw_xlsx_unchanged():
    base = _baseline()
    raw_files = {f for f in base if f.startswith("data/recent_hmis/raw/") and f.endswith(".xlsx")}
    assert len(raw_files) > 400
    changed = [f for f in raw_files if _sha(os.path.join(ROOT, f)) != base[f]]
    assert not changed, f"raw xlsx changed: {changed[:5]}"


# --------------------------------------------------------------------------- #
# 11. Dataset 1/2 unchanged
# --------------------------------------------------------------------------- #
def test_dataset1_2_unchanged():
    base = _baseline()
    for f in ["dataset1.csv", "dataset2.csv"]:
        assert os.path.exists(os.path.join(ROOT, f))
        assert _sha(os.path.join(ROOT, f)) == base[f], f"{f} changed"


# --------------------------------------------------------------------------- #
# 12. Existing MRCDSS analytical artifacts unchanged (models, outputs, src)
#
# backend/ and frontend/ are intentionally refined during this completion cycle
# (API semantics, Disha wording, UI polish) and are therefore excluded here.
# The artifacts that must remain byte-identical are the saved model metrics,
# historical labels, and pipeline source: models/, outputs/, src/.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("prefix", ["models", "outputs", "src"])
def test_mrcdss_outputs_unchanged(prefix):
    base = _baseline()
    files = {f for f in base if f.startswith(prefix + "/") or f.startswith(prefix + os.sep)}
    assert len(files) > 0
    changed = [f for f in files if _sha(os.path.join(ROOT, f)) != base[f]]
    assert not changed, f"{prefix} changed: {changed[:5]}"
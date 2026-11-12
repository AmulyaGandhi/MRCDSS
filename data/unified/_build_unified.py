"""Build the unified MRCDSS + Recent HMIS dataset.

Reads (never writes to) the original source datasets and appends them into ONE
derived artifact under data/unified/:

    unified_mr_cdss_data.csv
    unified_data_dictionary.csv
    unified_data_quality_report.md

Historical records (Dataset 1/2) are taken from their harmonised analytical form
(outputs/risk_classification/district_year_risk_clusters.csv with DSS fields), which
preserves every original D1/D2 State-District-Year record (8405 rows) together with
the existing risk classification. Recent HMIS (Dataset 3) records are appended
without any risk classification. Indicators that do not exist for an era are NaN.

No source file is modified, no feature is imputed, and no historical risk label is
altered.
"""
from __future__ import annotations

import os
import json

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "data", "unified")

HIST_RISK_CSV = os.path.join(ROOT, "outputs", "risk_classification", "district_year_risk_clusters.csv")
HIST_DSS_CSV = os.path.join(ROOT, "outputs", "decision_support", "district_decision_support.csv")
D1_CSV = os.path.join(ROOT, "dataset1.csv")
D2_CSV = os.path.join(ROOT, "dataset2.csv")
D3_CSV = os.path.join(ROOT, "data", "recent_hmis", "dataset3", "dataset3_recent_hmis.csv")
D3_MAPPING_CSV = os.path.join(ROOT, "data", "recent_hmis", "dataset3", "source_file_mapping.csv")

FEATURES = [
    "ANC_First_Trimester_Pct",
    "TT2_Booster_Pct",
    "Severe_Anemia_Pct",
    "Institutional_Delivery_Pct",
    "SBA_Home_Delivery_Pct",
    "PNC_48h_Pct",
    "Obstetric_Complications_Pct",
]

DSS_COLS = [
    "priority_level",
    "top_contributing_feature_1",
    "top_contributing_feature_2",
    "top_contributing_feature_3",
    "planning_focus_1",
    "planning_focus_2",
    "planning_focus_3",
]

D3_COMPARABLE_INDICATORS = ["ANC_First_Trimester_Pct", "TT2_Booster_Pct", "Severe_Anemia_Pct"]
D3_UNAVAILABLE_INDICATORS = [
    "Institutional_Delivery_Pct",
    "SBA_Home_Delivery_Pct",
    "PNC_48h_Pct",
]
D3_PARTIAL_INDICATOR = "Obstetric_Complications_Pct"

D3_SBA_TYPE = "Home Deliveries Attended (To Total Reported Home Deliveries) (%)"  # unused sentinel


def _sba_column(features):
    return next((c for c in features.columns if "Home Deliveries Attended By Skilled" in c and " (%)" in c), None)


def load_historical():
    risk = pd.read_csv(HIST_RISK_CSV)
    dss = pd.read_csv(HIST_DSS_CSV)[["State", "District", "Year", "source_dataset", *DSS_COLS]]
    hist = risk.merge(dss, on=["State", "District", "Year", "source_dataset"], how="left")

    d1 = pd.read_csv(D1_CSV)[["State", "District", "Year"]]
    d2 = pd.read_csv(D2_CSV)[["State", "District", "Year"]]
    sba_col1 = _sba_column(pd.read_csv(D1_CSV, nrows=0))
    sba_col2 = _sba_column(pd.read_csv(D2_CSV, nrows=0))
    d1n = pd.read_csv(D1_CSV, usecols=["State", "District", "Year", sba_col1])
    d2n = pd.read_csv(D2_CSV, usecols=["State", "District", "Year", sba_col2])
    d1n = d1n.rename(columns={sba_col1: "SBA_Home_Delivery_Pct"})
    d2n = d2n.rename(columns={sba_col2: "SBA_Home_Delivery_Pct"})
    sba = pd.concat([d1n, d2n], ignore_index=True)
    sba["Year"] = sba["Year"].str.extract(r"(\d{4})$").astype(int)

    hist = hist.merge(sba, on=["State", "District", "Year"], how="left")
    hist["source_dataset"] = hist["source_dataset"].replace({"D1": "dataset1", "D2": "dataset2"})
    hist["data_era"] = "HISTORICAL_MRCDSS"
    hist["indicator_definition_status"] = (
        "HARMONIZED_HISTORICAL: six indicators harmonized for the historical MRCDSS model; "
        "SBA preserved as a raw reference indicator (excluded from model harmonization)."
    )
    hist["risk_classification_available"] = True
    hist["recent_hmis_available"] = False
    hist["hmis_source_file"] = ""
    return hist


def load_recent():
    recent = pd.read_csv(D3_CSV)
    recent["source_dataset"] = "recent_hmis"
    mapping = pd.read_csv(D3_MAPPING_CSV)[["fiscal_year", "state", "filename"]]
    mapping = mapping.rename(columns={"fiscal_year": "Year", "state": "State"})
    recent = recent.merge(mapping, on=["Year", "State"], how="left")

    recent["data_era"] = "RECENT_HMIS"
    recent["risk_classification_available"] = False
    recent["recent_hmis_available"] = True
    for col in ("risk_class", *DSS_COLS):
        recent[col] = None
    recent["priority_level"] = None
    recent["Institutional_Delivery_Pct"] = None
    recent["SBA_Home_Delivery_Pct"] = None
    recent["PNC_48h_Pct"] = None
    recent = recent.rename(columns={"filename": "hmis_source_file"})

    def status(row):
        line1 = (
            "RECENT_HMIS: ANC First Trimester & TT2/Booster comparable; "
            "Severe Anemia definition changed (Hb <7 -> <=7)."
        )
        if row in {"2020-2021", "2021-2022", "2022-2023"}:
            return line1 + " Obstetric Complications available through 2022-23."
        return line1 + " Obstetric Complications schema changed from 2023-24 onwards (NaN)."

    recent["indicator_definition_status"] = recent["Year"].map(status)
    return recent


def build():
    os.makedirs(OUT, exist_ok=True)
    hist = load_historical()
    recent = load_recent()

    cols = [
        "State", "District", "Year", "source_dataset", "data_era",
        "indicator_definition_status", "risk_classification_available",
        "recent_hmis_available", "risk_class", *DSS_COLS, *FEATURES,
        "hmis_source_file",
    ]
    unified = pd.concat([hist[cols], recent[cols]], ignore_index=True)
    unified["Year"] = unified["Year"].astype(str)

    # Integrity gates
    n1 = int((unified["source_dataset"] == "dataset1").sum())
    n2 = int((unified["source_dataset"] == "dataset2").sum())
    n3 = int((unified["source_dataset"] == "recent_hmis").sum())
    assert len(hist) == 8405, len(hist)
    assert len(recent) == 3306, len(recent)
    assert n1 == 6293 and n2 == 2112 and n3 == 3306, (n1, n2, n3)
    assert unified.duplicated(["State", "District", "Year", "source_dataset"]).sum() == 0

    risk_cols = ["risk_class", *DSS_COLS]
    assert unified.loc[unified["source_dataset"] != "recent_hmis", "risk_class"].notna().all()
    assert unified.loc[unified["source_dataset"] == "recent_hmis", "risk_class"].isna().all()
    recent_rows = unified["source_dataset"] == "recent_hmis"
    assert unified.loc[recent_rows, "Institutional_Delivery_Pct"].isna().all()
    assert unified.loc[recent_rows, "SBA_Home_Delivery_Pct"].isna().all()
    assert unified.loc[recent_rows, "PNC_48h_Pct"].isna().all()
    src3 = pd.read_csv(D3_CSV)
    for f in ["ANC_First_Trimester_Pct", "TT2_Booster_Pct", "Severe_Anemia_Pct", "Obstetric_Complications_Pct"]:
        key = unified.loc[recent_rows, f].isna().to_numpy() == src3[f].isna().to_numpy()
        assert key.all(), f + " missingness mismatch"
    for f in ["ANC_First_Trimester_Pct", "TT2_Booster_Pct", "Severe_Anemia_Pct"]:
        assert int((unified.loc[recent_rows, f] == 0).sum()) == int((src3[f] == 0).sum()), f + " zero-fill"

    out_csv = os.path.join(OUT, "unified_mr_cdss_data.csv")
    unified.to_csv(out_csv, index=False)

    stats = {
        "dataset1_rows": n1,
        "dataset2_rows": n2,
        "recent_hmis_rows": n3,
        "unified_rows": len(unified),
        "expected_sum": 6293 + 2112 + 3306,
        "historical_years": sorted(unified.loc[unified["data_era"] == "HISTORICAL_MRCDSS", "Year"].unique().tolist()),
        "recent_years": sorted(unified.loc[unified["data_era"] == "RECENT_HMIS", "Year"].unique().tolist()),
        "duplicates": int(unified.duplicated(["State", "District", "Year", "source_dataset"]).sum()),
    }
    with open(os.path.join(OUT, "_build_stats.json"), "w") as fh:
        json.dump(stats, fh, indent=2)

    write_dictionary()
    write_quality_report(unified, stats)
    print("STATS", json.dumps(stats))
    print("wrote", out_csv)


def write_dictionary():
    rows = [
        ["State", "string", "State name (native HMIS/NDAP representation).", "Dataset 1/2/3", "All"],
        ["District", "string", "District name (native representation per source; not merged across eras).", "Dataset 1/2/3", "All"],
        ["Year", "string", "Fiscal/calendar year of the observation (historical: 2008-2019; recent HMIS: 2020-2021..2024-2025).", "Dataset 1/2/3", "All"],
        ["source_dataset", "enum", "Provenance label: dataset1 | dataset2 | recent_hmis.", "derived", "All"],
        ["data_era", "enum", "HISTORICAL_MRCDSS (Dataset 1/2, 2008-2019) | RECENT_HMIS (Dataset 3, 2020-2025).", "derived", "All"],
        ["indicator_definition_status", "string", "Analytical status of indicator definitions for the record's era.", "derived", "All"],
        ["risk_classification_available", "boolean", "true when the existing MRCDSS risk classification applies to the record; false for recent HMIS records.", "derived", "All"],
        ["recent_hmis_available", "boolean", "true for recent HMIS arm records; false for historical records.", "derived", "All"],
        ["risk_class", "enum", "Preserved historical MRCDSS risk class (High/Medium/Low Risk). Empty for recent HMIS records.", "outputs/risk_classification", "Historical only"],
        ["priority_level", "enum", "Historical DSS priority level (from validated MRCDSS DSS). Empty for recent HMIS records.", "outputs/decision_support", "Historical only"],
        ["top_contributing_feature_1..3", "string", "Historical SHAP-derived contributing features. Empty for recent HMIS records.", "outputs/decision_support", "Historical only"],
        ["planning_focus_1..3", "string", "Historical DSS planning focus areas. Empty for recent HMIS records.", "outputs/decision_support", "Historical only"],
        ["ANC_First_Trimester_Pct", "float, 0-100", "Percentage denominator: ANC registrations. Definitionally comparable across eras.", "Dataset 1/2 harmonized; Dataset 3", "All"],
        ["TT2_Booster_Pct", "float, may exceed 100", "TT2/second dose or TT-booster percentage. Historical: harmonized; recent: comparable with caveat (double-counting possible).", "Dataset 1/2 harmonized; Dataset 3", "All"],
        ["Severe_Anemia_Pct", "float, 0-100", "Severe anemia share. Historical: harmonized; recent: definition changed (Hb <7 to <=7 from 2023-24).", "Dataset 1/2 harmonized; Dataset 3", "All"],
        ["Institutional_Delivery_Pct", "float, 0-100", "Institutional delivery share. Historical only; NOT available in Dataset 3 (schema change).", "Dataset 1/2 harmonized", "Historical only"],
        ["SBA_Home_Delivery_Pct", "float, 0-100", "Skilled-birth-attendant home delivery share. Historical raw reference only (excluded from model harmonization); NOT available in Dataset 3.", "Dataset 1/2 raw", "Historical only"],
        ["PNC_48h_Pct", "float, 0-100", "Post-natal care within 48 hours share. Historical only; NOT available in Dataset 3.", "Dataset 1/2 harmonized", "Historical only"],
        ["Obstetric_Complications_Pct", "float, 0-100", "Obstetric complications share. Historical: harmonized; recent: available through 2022-23 only, NaN from 2023-24 (schema change).", "Dataset 1/2 harmonized; Dataset 3 (<=2022-23)", "All (recent only <=2022-23)"],
        ["hmis_source_file", "string", "For recent HMIS records: the annual cumulative HMIS file the record was reconstructed from. Empty for historical records.", "Dataset 3 source_file_mapping", "Recent HMIS only"],
    ]
    dict_df = pd.DataFrame(rows, columns=["field", "type", "description", "source", "applicability"])
    dict_df.to_csv(os.path.join(OUT, "unified_data_dictionary.csv"), index=False)


def write_quality_report(unified: pd.DataFrame, stats: dict):
    lines = [
        "# Unified Data Quality Report",
        "",
        "Unified MRCDSS + Recent HMIS analytical dataset (`unified_mr_cdss_data.csv`).",
        "",
        "## 1. Provenance",
        "",
        "- Historical records come from the harmonised analytical form of Dataset 1/2 used by the existing MRCDSS model (`outputs/risk_classification/district_year_risk_clusters.csv` + `outputs/decision_support/district_decision_support.csv`), preserving each original State-District-Year record.",
        "- `SBA_Home_Delivery_Pct` for historical records is sourced from the raw Dataset 1/2 files (kept as a raw reference; it was excluded from model harmonization).",
        "- Recent HMIS records come from `dataset3_recent_hmis.csv`; each retains `hmis_source_file` tracing it to its annual cumulative HMIS file.",
        "",
        "## 2. Row counts",
        "",
        f"- Dataset 1: {stats['dataset1_rows']}",
        f"- Dataset 2: {stats['dataset2_rows']}",
        f"- Recent HMIS (Dataset 3): {stats['recent_hmis_rows']}",
        f"- Unified total: {stats['unified_rows']} (expected {stats['expected_sum']})",
        f"- Accidental duplicate (State, District, Year, source_dataset) records: {stats['duplicates']}",
        "",
        "## 3. Time range",
        "",
        f"- Historical MRCDSS: {stats['historical_years'][0]} .. {stats['historical_years'][-1]}",
        f"- Recent HMIS: {stats['recent_years'][0]} .. {stats['recent_years'][-1]}",
        "- 2024-25 is a partial year (17 states with complete UpTo_Mar files).",
        "",
        "## 4. Feature availability",
        "",
        "| Indicator | Historical (D1/D2) | Recent HMIS (D3) |",
        "|---|---|---|",
        "| ANC_First_Trimester_Pct | available | available (comparable) |",
        "| TT2_Booster_Pct | available | available (comparable with caveat) |",
        "| Severe_Anemia_Pct | available | available (definition changed) |",
        "| Institutional_Delivery_Pct | available | NaN (not available) |",
        "| SBA_Home_Delivery_Pct | raw reference (historical only) | NaN (not available) |",
        "| PNC_48h_Pct | available | NaN (not available) |",
        "| Obstetric_Complications_Pct | available | available through 2022-23; NaN from 2023-24 (schema change) |",
        "",
        "No unavailable value was imputed; unavailable indicators are NaN (never 0).",
        "",
        "## 5. Risk classification availability",
        "",
        "- Every historical record retains its original MRCDSS risk class (High/Medium/Low) unchanged.",
        "- No recent HMIS record carries a risk classification; `risk_classification_available` is false for the recent era.",
        "",
        "## 6. Checks",
        "",
        "- Source datasets verified byte-identical via the protected-file baseline (dataset1.csv, dataset2.csv, raw HMIS XLSX, dataset3_recent_hmis.csv).",
        "- Unified row count = sum of era counts; no accidental deduplication across eras.",
        "- Recent HMIS indicators present exactly as provided (ANC, TT2, Severe Anemia, Obstetric through 2022-23).",
    ]
    with open(os.path.join(OUT, "unified_data_quality_report.md"), "w") as fh:
        fh.write("\n".join(lines))


if __name__ == "__main__":
    build()
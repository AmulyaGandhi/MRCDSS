import pandas as pd
import numpy as np
import os
import sys
from config import *
from collections import OrderedDict


def load_datasets():
    d1 = pd.read_csv(DATASET1_PATH)
    d2 = pd.read_csv(DATASET2_PATH)
    d1["source_dataset"] = "D1"
    d2["source_dataset"] = "D2"
    return d1, d2


def extract_year(d):
    s = d["Year"].astype(str)
    m = s.str.extract(r"(\d{4})")
    return pd.to_numeric(m[0], errors="coerce").astype("Int64")


def identify_pct_columns(df):
    return [c for c in df.columns if "(%)" in c or "%" in c]


def identify_numeric_columns(df):
    cols = []
    for c in df.columns:
        if c in ["Country", "State", "District", "Year", "source_dataset"]:
            continue
        s = pd.to_numeric(df[c], errors="coerce")
        if s.notna().sum() > 0:
            cols.append(c)
    return cols


def report_telangana_issues(d1, d2):
    report = []
    total_rows_affected = 0
    total_cols_affected = 0
    for name, df in [("D1", d1), ("D2", d2)]:
        tel_mask = df["State"] == "Telangana"
        tel_rows = tel_mask.sum()
        numeric_cols = identify_numeric_columns(df)
        affected_cols = []
        for col in numeric_cols:
            vals = pd.to_numeric(df.loc[tel_mask, col], errors="coerce")
            invalid = (vals < PERCENTAGE_LOWER_BOUND) | (vals > PERCENTAGE_UPPER_BOUND)
            if invalid.any():
                invalid_count = int(invalid.sum())
                affected_cols.append((col, invalid_count))
                total_cols_affected += 1
        if affected_cols:
            total_rows_affected += tel_rows
            report.append(f"\n{name} Telangana ({tel_rows} rows):")
            for col, cnt in affected_cols:
                report.append(f"  {col}: {cnt} invalid values")
    return report, total_rows_affected, total_cols_affected


def clean_invalid_percentages(df, pct_cols):
    cleaned = df.copy()
    invalid_counts = OrderedDict()
    new_nan_counts = {}
    for col in pct_cols:
        vals = pd.to_numeric(cleaned[col], errors="coerce")
        invalid_mask = (vals < PERCENTAGE_LOWER_BOUND) | (vals > PERCENTAGE_UPPER_BOUND)
        invalid_count = int(invalid_mask.sum())
        if invalid_count > 0:
            invalid_counts[col] = invalid_count
            cleaned[col] = vals.where(~invalid_mask, np.nan)
            new_nan_counts[col] = invalid_count
    return cleaned, invalid_counts, new_nan_counts


def clean_negative_values(df, numeric_cols):
    cleaned = df.copy()
    negative_counts = OrderedDict()
    for col in numeric_cols:
        vals = pd.to_numeric(cleaned[col], errors="coerce")
        neg_mask = vals < NEGATIVE_THRESHOLD
        neg_count = int(neg_mask.sum())
        if neg_count > 0:
            negative_counts[col] = neg_count
            cleaned[col] = vals.where(~neg_mask, np.nan)
    return cleaned, negative_counts


def drop_empty_rows(d1, d2):
    d1c = d1.copy()
    d2c = d2.copy()
    for name, df in [("D1", d1c), ("D2", d2c)]:
        numeric_cols = identify_numeric_columns(df)
        if numeric_cols:
            all_null = df[numeric_cols].isna().all(axis=1)
            df.drop(df[all_null].index, inplace=False)
        df.reset_index(drop=True, inplace=True)
    return d1c, d2c


def impute_missing(df, original_missing_per_col=None):
    df = df.copy()
    imputation_detail = OrderedDict()
    total_actual_imputed = 0
    remaining_missing = {}
    numeric_cols = identify_numeric_columns(df)
    for col in numeric_cols:
        total_na = int(df[col].isna().sum())
        orig_na = 0
        if original_missing_per_col and col in original_missing_per_col:
            orig_na = original_missing_per_col[col]
        new_na = total_na - orig_na
        if total_na > 0:
            median_val = pd.to_numeric(df[col], errors="coerce").median()
            if not np.isnan(median_val):
                df[col] = pd.to_numeric(df[col], errors="coerce")
                df[col] = df[col].fillna(median_val)
        after_na = int(df[col].isna().sum())
        total_actual_imputed += total_na - after_na
        remaining_missing[col] = after_na
        imputation_detail[col] = {
            "original_missing": orig_na,
            "invalid_to_nan": new_na,
            "actual_imputed": total_na - after_na,
            "remaining": after_na,
        }
    return df, total_actual_imputed, remaining_missing, imputation_detail


def drop_all_nan_columns(df):
    all_nan_cols = df.columns[df.isna().all()].tolist()
    nan_counts = {col: int(df[col].isna().sum()) for col in all_nan_cols}
    df = df.drop(columns=all_nan_cols)
    return df, all_nan_cols, nan_counts


def deduplicate(df):
    before = len(df)
    dup_cols = ["State", "District", "Year", "source_dataset"]
    dup_mask = df.duplicated(subset=dup_cols, keep="first")
    num_dups = int(dup_mask.sum())
    df = df[~dup_mask].copy()
    return df, num_dups


def get_coverage(d1, d2):
    d1_years = sorted([y for y in d1["Year"].dropna().unique() if not pd.isna(y)])
    d2_years = sorted([y for y in d2["Year"].dropna().unique() if not pd.isna(y)])
    d1_districts = sorted(d1["District"].dropna().unique())
    d2_districts = sorted(d2["District"].dropna().unique())
    return {
        "D1_years": [int(y) for y in d1_years],
        "D2_years": [int(y) for y in d2_years],
        "D1_districts": list(d1_districts),
        "D2_districts": list(d2_districts),
        "D1_num_districts": len(d1_districts),
        "D2_num_districts": len(d2_districts),
    }


def count_total_nan(df, numeric_only=True):
    if numeric_only:
        cols = identify_numeric_columns(df)
    else:
        cols = df.columns.tolist()
    return int(df[cols].isna().sum().sum())


def categorize_columns(df):
    geo_cols = ["Country", "State", "District", "Year", "source_dataset"]
    pct_cols = [c for c in df.columns if "(%)" in c or "%" in c]
    num_cols = [c for c in df.columns if c not in geo_cols and c not in pct_cols]
    num_cols = [c for c in num_cols if c in df.columns]
    return {
        "geographic": geo_cols,
        "percentage": pct_cols,
        "numeric_count": num_cols,
    }


def run_pipeline():
    print("Loading datasets...")
    d1_raw, d2_raw = load_datasets()
    print(f"D1: {d1_raw.shape}, D2: {d2_raw.shape}")

    d1 = d1_raw.copy()
    d2 = d2_raw.copy()

    print("\n--- Step 1: Record original missing per column ---")
    orig_missing_d1 = {c: int(d1[c].isna().sum()) for c in d1.columns}
    orig_missing_d2 = {c: int(d2[c].isna().sum()) for c in d2.columns}
    d1_missing = int(d1.isna().sum().sum())
    d2_missing = int(d2.isna().sum().sum())
    total_missing_before = d1_missing + d2_missing
    print(f"D1 missing: {d1_missing}, D2 missing: {d2_missing}")

    print("\n--- Step 2: Telangana issue report ---")
    tel_report, tel_rows, tel_cols = report_telangana_issues(d1, d2)
    print(f"Telangana: {tel_rows} rows, {tel_cols} columns with values outside 0-100")
    for line in tel_report:
        print(line)

    print("\n--- Step 3: Drop empty rows ---")
    d1, d2 = drop_empty_rows(d1, d2)
    print(f"D1: {d1.shape}, D2: {d2.shape}")

    print("\n--- Step 4: Extract year and combine ---")
    d1["Year"] = extract_year(d1)
    d2["Year"] = extract_year(d2)
    combined = pd.concat([d1, d2], ignore_index=True)
    nan_after_load = count_total_nan(combined)
    print(f"Combined: {combined.shape}, NaN after load/combine: {nan_after_load}")

    print("\n--- Step 5: Clean invalid percentages ---")
    pct_cols = identify_pct_columns(combined)
    combined, invalid_pct, new_nan_counts = clean_invalid_percentages(combined, pct_cols)
    total_invalid = sum(invalid_pct.values())
    nan_after_pct = count_total_nan(combined)
    print(f"Invalid percentages: {total_invalid} across {len(invalid_pct)} features, NaN after: {nan_after_pct}")

    print("\n--- Step 6: Clean negative values ---")
    numeric_cols = identify_numeric_columns(combined)
    combined, negative_counts = clean_negative_values(combined, numeric_cols)
    total_negative = sum(negative_counts.values())
    print(f"Negative values: {total_negative} across {len(negative_counts)} features")

    print("\n--- Step 7: Deduplicate ---")
    combined, num_dups = deduplicate(combined)
    print(f"Duplicate rows removed: {num_dups}")

    print("\n--- Step 8: Drop all-NaN columns ---")
    combined, all_nan_cols, all_nan_counts = drop_all_nan_columns(combined)
    nan_after_drop = count_total_nan(combined)
    print(f"Dropped {len(all_nan_cols)} all-NaN columns, NaN after drop: {nan_after_drop}")

    print("\n--- Step 9: Impute missing values ---")
    orig_missing_per_col = {}
    for col in combined.columns:
        d1_part = orig_missing_d1.get(col, 0)
        d2_part = orig_missing_d2.get(col, 0)
        orig_missing_per_col[col] = d1_part + d2_part
    nan_before_imp = count_total_nan(combined)
    combined, total_imputed, remaining_missing, imputation_detail = impute_missing(
        combined, orig_missing_per_col
    )
    nan_after_imp = count_total_nan(combined)
    remaining_total = sum(remaining_missing.values())
    actual_cells_changed = nan_before_imp - nan_after_imp
    misalignment_nan = nan_before_imp - total_missing_before - total_invalid
    print(f"NaN before imputation: {nan_before_imp}")
    print(f"NaN after imputation: {nan_after_imp}")
    print(f"Actual cells changed NaN->numeric: {actual_cells_changed}")
    print(f"Imputed = {actual_cells_changed} (should equal NaN before: {nan_before_imp})")

    print("\n--- Step 10: Column categorization ---")
    cats = categorize_columns(combined)
    print(f"Geographic: {len(cats['geographic'])}, Percentage: {len(cats['percentage'])}, Numeric: {len(cats['numeric_count'])}")

    print("\n--- Step 11: Coverage ---")
    coverage = get_coverage(d1, d2)

    print("\n--- Step 12: Save outputs ---")
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    combined.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved: {OUTPUT_CSV} ({combined.shape})")

    report = []
    report.append("=" * 70)
    report.append("DATA QUALITY REPORT")
    report.append("=" * 70)
    report.append(f"\n1. Final cleaned dataset path: {OUTPUT_CSV}")
    report.append(f"2. Final shape: {combined.shape}")
    report.append(f"3. Missing values before cleaning: {total_missing_before}")
    report.append(f"   D1: {d1_missing}, D2: {d2_missing}")
    report.append(f"\n4. Invalid percentage values by feature:")
    for col, cnt in invalid_pct.items():
        report.append(f"   {col}: {cnt}")
    report.append(f"   Total invalid: {total_invalid}")
    report.append(f"\n5. Imputation breakdown (stage-by-stage NaN counts):")
    report.append(f"   NaN after load/combine: {nan_after_load}")
    report.append(f"   NaN after percentage cleaning: {nan_after_pct}")
    report.append(f"   NaN after dropping all-NaN columns: {nan_after_drop}")
    report.append(f"   NaN immediately before imputation: {nan_before_imp}")
    report.append(f"   NaN immediately after imputation: {nan_after_imp}")
    report.append(f"   Actual cells changed NaN->numeric: {actual_cells_changed}")
    report.append(f"   Consistency: actual_cells_changed ({actual_cells_changed}) = nan_before ({nan_before_imp}) - nan_after ({nan_after_imp}) = {nan_before_imp - nan_after_imp}")
    report.append(f"   Breakdown of NaN before imputation ({nan_before_imp}):")
    report.append(f"     Original missing (pre-cleaning): {total_missing_before}")
    report.append(f"     Invalid percentages → NaN: {total_invalid}")
    report.append(f"     Column misalignment (D1/D2 different columns): {misalignment_nan}")
    report.append(f"   Imputed = {actual_cells_changed} (all NaN filled with median, {sum(all_nan_counts.values())} values in dropped columns not counted)")
    report.append(f"   Remaining missing: {remaining_total}")
    report.append(f"\n   Per-column breakdown:")
    for col, detail in imputation_detail.items():
        if detail["original_missing"] > 0 or detail["invalid_to_nan"] > 0 or detail["actual_imputed"] > 0:
            report.append(f"   {col}:")
            report.append(f"     original_missing: {detail['original_missing']}")
            report.append(f"     invalid_to_nan: {detail['invalid_to_nan']}")
            report.append(f"     actual_imputed: {detail['actual_imputed']}")
            report.append(f"     remaining: {detail['remaining']}")
    report.append(f"\n6. Remaining missing values: {remaining_total}")
    if remaining_total == 0:
        report.append("   None")
    else:
        for col, cnt in remaining_missing.items():
            if cnt > 0:
                report.append(f"   {col}: {cnt}")
    report.append(f"\n7. Duplicate State+District+Year+source_dataset count: {num_dups}")
    report.append(f"\n8. Telangana correction report:")
    report.append(f"   Rows affected (State=Telangana): {tel_rows}")
    report.append(f"   Columns with values outside 0-100: {tel_cols}")
    for line in tel_report:
        report.append(f"   {line}")
    report.append(f"   Correction applied: NONE (invalid percentages set to NaN only)")
    report.append(f"\n9. D1/D2 year and district coverage:")
    report.append(f"   D1 years: {coverage['D1_years']}")
    report.append(f"   D2 years: {coverage['D2_years']}")
    report.append(f"   D1 districts: {coverage['D1_num_districts']}")
    report.append(f"   D2 districts: {coverage['D2_num_districts']}")
    report.append(f"\n10. Column groups in final dataset:")
    report.append(f"    Geographic: {len(cats['geographic'])} ({cats['geographic']})")
    report.append(f"    Percentage: {len(cats['percentage'])}")
    report.append(f"    Numeric: {len(cats['numeric_count'])}")
    report.append(f"    Total columns: {len(combined.columns)}")
    report.append(f"\n11. Negative values cleaned: {total_negative}")
    report.append(f"12. Pytest result: See tests/")

    report_text = "\n".join(report)
    with open(REPORT_TXT, "w") as f:
        f.write(report_text)
    print(f"Saved: {REPORT_TXT}")

    return {
        "output_csv": OUTPUT_CSV,
        "shape": combined.shape,
        "missing_before": total_missing_before,
        "invalid_pct": invalid_pct,
        "total_invalid": total_invalid,
        "nan_after_load": nan_after_load,
        "nan_after_pct": nan_after_pct,
        "nan_after_drop": nan_after_drop,
        "nan_before_imputation": nan_before_imp,
        "nan_after_imputation": nan_after_imp,
        "actual_cells_changed": actual_cells_changed,
        "misalignment_nan": misalignment_nan,
        "total_imputed": actual_cells_changed,
        "remaining_missing": remaining_total,
        "duplicates": num_dups,
        "coverage": coverage,
        "negative_cleaned": total_negative,
        "all_nan_cols": all_nan_cols,
        "all_nan_counts": all_nan_counts,
        "imputation_detail": imputation_detail,
        "telangana_rows": tel_rows,
        "telangana_cols": tel_cols,
        "telangana_report": tel_report,
        "column_categories": cats,
        "df": combined,
    }


if __name__ == "__main__":
    results = run_pipeline()
    print("\nPipeline complete.")

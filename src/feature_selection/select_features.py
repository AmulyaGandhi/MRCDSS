import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PREPROCESSED_PATH = os.path.join(BASE_DIR, "outputs", "preprocessed_output.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs", "selected_features")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "maternal_model_features.csv")

FEATURE_COLUMNS = [
    "ANC_First_Trimester_Pct",
    "TT2_Booster_Pct",
    "IFA_Pct",
    "Severe_Anemia_Pct",
    "Institutional_Delivery_Pct",
    "SBA_Home_Delivery_Pct",
    "PNC_48h_Pct",
    "Obstetric_Complications_Pct",
]

KEEP_COLUMNS = ["State", "District", "Year", "source_dataset"]

SOURCE_COLUMN_MAP = {
    "ANC_First_Trimester_Pct": {
        "D1": "Registrations For  Ante Natal Care (Anc) In The First Trimester (To Total Anc Registrations) (%) (UOM:%(Percentage)), Scaling Factor:1",
        "D2": "Registrations For Ante Natal Care (Anc) In The First Trimester (To Total Anc Registrations) (%) (UOM:%(Percentage)), Scaling Factor:1",
    },
    "TT2_Booster_Pct": {
        "D1": "Pregnant Women Received The Second Dose Of Tetanus-Toxoid Vaccine (Tt2) Or Booster (To Total Anc Registrations) (%) (UOM:%(Percentage)), Scaling Factor:1",
        "D2": "Pregnant Women Received Tetanus-Toxoid Vaccine (Tt2) Or Tetanus-Toxoid (Tt)  Booster (To Total Anc Registrations) (%) (UOM:%(Percentage)), Scaling Factor:1",
    },
    "IFA_Pct": {
        "D1": "Women Received 100 Ifa Tablets (To Total Anc Registrations) (%) (UOM:%(Percentage)), Scaling Factor:1",
        "D2": "Women Received 180 Ifa Tablets (To Total Anc Registrations) (%) (UOM:%(Percentage)), Scaling Factor:1",
    },
    "Severe_Anemia_Pct": {
        "D1": "Pregnant Women With Hemoglobin (Hb) Levels<7 (Severe Anemia) (To Women With Hemoglobin (Hb) Levels<11 (Moderate Anemia)) (UOM:%(Percentage)), Scaling Factor:1",
        "D2": "Pregnant Women With Hemoglobin (Hb) Levels<7 (Severe Anemia) (To Women With Hemoglobin (Hb) Levels<11 (Moderate Anemia)) (%) (UOM:%(Percentage)), Scaling Factor:1",
    },
    "Institutional_Delivery_Pct": {
        "D1": "Institutional Deliveries (To Total Anc Registrations) (%) (UOM:%(Percentage)), Scaling Factor:1",
        "D2": "Institutional Deliveries (To Total Anc Registrations) (%) (UOM:%(Percentage)), Scaling Factor:1",
    },
    "SBA_Home_Delivery_Pct": {
        "D1": "Home Deliveries Attended By Skilled Birth Attendants (Sba) (To Total Reported Home Deliveries) (%) (UOM:%(Percentage)), Scaling Factor:1",
        "D2": "Home Deliveries Attended By Skilled Birth Attendants (%) (UOM:%(Percentage)), Scaling Factor:1",
    },
    "PNC_48h_Pct": {
        "D1": "Women Received Post Partum Check Up Within 48 Hours Of Delivery (To Total Reported Deliveries) (%) (UOM:%(Percentage)), Scaling Factor:1",
        "D2": "Women Received Post Partum Check Up Within 48 Hours Of Delivery (To Total Reported Deliveries) (%) (UOM:%(Percentage)), Scaling Factor:1",
    },
    "Obstetric_Complications_Pct": {
        "D1": "Pregnant Women With Obstetric Complications (Who Were Attended To) (To Total Reported Deliveries) (%) (UOM:%(Percentage)), Scaling Factor:1",
        "D2": "Pregnant Women With Obstetric Complications (Who Were Attended To) (To Total Reported Deliveries) (%) (UOM:%(Percentage)), Scaling Factor:1",
    },
}

RISK_DIRECTION = {
    "ANC_First_Trimester_Pct": "lower = higher risk",
    "TT2_Booster_Pct": "lower = higher risk",
    "IFA_Pct": "lower = higher risk",
    "Severe_Anemia_Pct": "higher = higher risk",
    "Institutional_Delivery_Pct": "lower = higher risk",
    "SBA_Home_Delivery_Pct": "lower = higher risk",
    "PNC_48h_Pct": "lower = higher risk",
    "Obstetric_Complications_Pct": "higher = higher risk",
}


def load_preprocessed():
    return pd.read_csv(PREPROCESSED_PATH)


def harmonize_features(df):
    result = df[KEEP_COLUMNS].copy()
    for feat in FEATURE_COLUMNS:
        d1_col = SOURCE_COLUMN_MAP[feat]["D1"]
        d2_col = SOURCE_COLUMN_MAP[feat]["D2"]
        mask_d1 = df["source_dataset"] == "D1"
        mask_d2 = df["source_dataset"] == "D2"
        harmonized = pd.Series(float("nan"), index=df.index, dtype="float64")
        if d1_col in df.columns:
            harmonized.loc[mask_d1] = df.loc[mask_d1, d1_col]
        if d2_col in df.columns:
            harmonized.loc[mask_d2] = df.loc[mask_d2, d2_col]
        result[feat] = harmonized
    return result


def run_feature_selection():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df = load_preprocessed()
    selected = harmonize_features(df)
    selected.to_csv(OUTPUT_PATH, index=False)
    print(f"Selected features saved to {OUTPUT_PATH}")
    print(f"Shape: {selected.shape}")
    print(f"Columns: {list(selected.columns)}")
    return selected


if __name__ == "__main__":
    run_feature_selection()
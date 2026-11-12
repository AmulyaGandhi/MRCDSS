import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_PATH = os.path.join(BASE_DIR, "outputs", "selected_features", "maternal_model_features.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "outputs", "selected_features", "final_model_features.csv")

FINAL_FEATURES = [
    "ANC_First_Trimester_Pct",
    "TT2_Booster_Pct",
    "Severe_Anemia_Pct",
    "Institutional_Delivery_Pct",
    "PNC_48h_Pct",
    "Obstetric_Complications_Pct",
]

KEEP_COLUMNS = ["State", "District", "Year", "source_dataset"]


def create_final_features():
    df = pd.read_csv(INPUT_PATH)
    columns = KEEP_COLUMNS + FINAL_FEATURES
    final = df[columns].copy()
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    final.to_csv(OUTPUT_PATH, index=False)
    print(f"Final features saved to {OUTPUT_PATH}")
    print(f"Shape: {final.shape}")
    print(f"Columns: {list(final.columns)}")
    return final


if __name__ == "__main__":
    create_final_features()
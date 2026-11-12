import pandas as pd

FILES = {
    "D1": "dataset1.csv",
    "D2": "dataset2.csv"
}

CANDIDATE_KEYWORDS = [
    "First Trimester",
    "TT2",
    "Tetanus",
    "IFA",
    "Moderate Anaemia",
    "Moderate Anemia",
    "Severe Anaemia",
    "Severe Anemia",
    "Home Deliveries",
    "Institutional Deliveries",
    "Safe Deliveries",
    "Post Partum",
    "Still Birth",
    "Stillbirth",
    "Breast Feeding",
    "Breastfeeding",
    "Obstetric Complications",
    "Blood Transfusion"
]

for dataset_name, filename in FILES.items():
    print("\n" + "=" * 80)
    print(dataset_name, filename)
    print("=" * 80)

    df = pd.read_csv(filename)

    for col in df.columns:
        name = str(col)

        if any(k.lower() in name.lower() for k in CANDIDATE_KEYWORDS):
            if pd.api.types.is_numeric_dtype(df[col]):
                s = pd.to_numeric(df[col], errors="coerce")

                print(f"\n{name}")
                print(f"  Missing: {s.isna().mean()*100:.2f}%")
                print(f"  Min: {s.min()}")
                print(f"  Median: {s.median()}")
                print(f"  Max: {s.max()}")
                print(f"  < 0: {(s < 0).sum()}")
                print(f"  > 100: {(s > 100).sum()}")

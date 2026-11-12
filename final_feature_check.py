import pandas as pd

FILES = {
    "D1": "dataset1.csv",
    "D2": "dataset2.csv"
}

FEATURE_KEYWORDS = [
    "First Trimester",
    "TT2",
    "Tetanus-Toxoid Vaccine (Tt2)",
    "180 Ifa",
    "100 Ifa",
    "Severe Anemia",
    "Home Deliveries (To Total",
    "Institutional Deliveries (To Total Reported Deliveries)",
    "Safe Deliveries",
    "Home Deliveries Attended By Skilled Birth Attendants",
    "Post Partum Check Up Within 48 Hours Of Delivery (To Total Reported Deliveries)",
    "Obstetric Complications (Who Were Attended To)"
]

for dataset_name, filename in FILES.items():

    print("\n" + "=" * 100)
    print(f"{dataset_name}: {filename}")
    print("=" * 100)

    df = pd.read_csv(filename)

    selected = []

    for col in df.columns:
        name = str(col)

        if any(k.lower() in name.lower() for k in FEATURE_KEYWORDS):
            if "(%)" in name:
                selected.append(col)

    print(f"\nCandidate percentage features found: {len(selected)}")

    for col in selected:
        s = pd.to_numeric(df[col], errors="coerce")

        valid = s.dropna()

        print("\n" + "-" * 80)
        print(col)
        print(f"Missing: {s.isna().mean()*100:.2f}%")
        print(f"Valid observations: {len(valid)}")
        print(f"Min: {valid.min()}")
        print(f"25%: {valid.quantile(.25)}")
        print(f"Median: {valid.median()}")
        print(f"75%: {valid.quantile(.75)}")
        print(f"Max: {valid.max()}")
        print(f"Below 0: {(s < 0).sum()}")
        print(f"Above 100: {(s > 100).sum()}")
        print(f"Unique values: {s.nunique()}")

    print("\nDataset shape:", df.shape)

import pandas as pd

datasets = {
    "D1": pd.read_csv("dataset1.csv"),
    "D2": pd.read_csv("dataset2.csv"),
}

for name, df in datasets.items():

    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    # Negative values
    numeric = df.select_dtypes(include="number")
    negative = (numeric < 0).sum()
    negative = negative[negative > 0].sort_values(ascending=False)

    print("\n--- NEGATIVE VALUES ---")
    if len(negative):
        print(negative.to_string())
    else:
        print("None")

    # Percentage columns outside 0-100
    print("\n--- PERCENTAGE COLUMNS OUTSIDE 0-100 ---")

    percentage_columns = [c for c in df.columns if "%" in c]

    for col in percentage_columns:
        values = pd.to_numeric(df[col], errors="coerce")
        invalid = ((values < 0) | (values > 100)).sum()

        if invalid > 0:
            print(
                f"{col}\n"
                f"  Invalid: {invalid}\n"
                f"  Min: {values.min()}\n"
                f"  Max: {values.max()}"
            )

    # High missingness
    print("\n--- HIGH MISSINGNESS (>50%) ---")

    missing = df.isna().mean() * 100
    high_missing = missing[missing > 50].sort_values(ascending=False)

    if len(high_missing):
        print(high_missing.to_string())
    else:
        print("None")

    # Low variance
    print("\n--- LOW VARIANCE (<=5 UNIQUE VALUES) ---")

    unique_counts = numeric.nunique()
    low_variance = unique_counts[unique_counts <= 5].sort_values()

    if len(low_variance):
        print(low_variance.to_string())
    else:
        print("None")

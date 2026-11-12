import pandas as pd

FILES = {
    "D1": "dataset1.csv",
    "D2": "dataset2.csv"
}

FEATURES = {
    "D1": {
        "ANC_First_Trimester":
            "Registrations For\u00a0 Ante Natal Care (Anc) In The First Trimester (To Total Anc Registrations) (%) (UOM:%(Percentage)), Scaling Factor:1",

        "TT2_Booster":
            "Pregnant Women Received The Second Dose Of Tetanus-Toxoid Vaccine (Tt2) Or Booster (To Total Anc Registrations) (%) (UOM:%(Percentage)), Scaling Factor:1",

        "Institutional_Delivery":
            "Institutional Deliveries (To Total Reported Deliveries) (%) (UOM:%(Percentage)), Scaling Factor:1",

        "Safe_Delivery":
            "Safe Deliveries (To Total Reported Deliveries) (%) (UOM:%(Percentage)), Scaling Factor:1",

        "Home_Delivery":
            "Home Deliveries (To Total Reported Deliveries) (%) (UOM:%(Percentage)), Scaling Factor:1",

        "SBA_Home":
            "Home Deliveries Attended By Skilled Birth Attendants (Sba) (To Total Reported Home Deliveries) (%) (UOM:%(Percentage)), Scaling Factor:1",

        "PNC_48h":
            "Women Received Post Partum Check Up Within 48 Hours Of Delivery (To Total Reported Deliveries) (%) (UOM:%(Percentage)), Scaling Factor:1",

        "Obstetric_Complications":
            "Pregnant Women With Obstetric Complications (Who Were Attended To) (To Total Reported Deliveries) (%) (UOM:%(Percentage)), Scaling Factor:1",
    },

    "D2": {
        "ANC_First_Trimester":
            "Registrations For Ante Natal Care (Anc) In The First Trimester (To Total Anc Registrations) (%) (UOM:%(Percentage)), Scaling Factor:1",

        "TT2_Booster":
            "Pregnant Women Received Tetanus-Toxoid Vaccine (Tt2) Or Tetanus-Toxoid (Tt)  Booster (To Total Anc Registrations) (%) (UOM:%(Percentage)), Scaling Factor:1",

        "Institutional_Delivery":
            "Institutional Deliveries (To Total Reported Deliveries) (%) (UOM:%(Percentage)), Scaling Factor:1",

        "Safe_Delivery":
            "Safe Deliveries (To Total Reported Deliveries) (%) (UOM:%(Percentage)), Scaling Factor:1",

        "Home_Delivery":
            "Home Deliveries (To Total Reported Deliveries) (%) (UOM:%(Percentage)), Scaling Factor:1",

        "SBA_Home":
            "Home Deliveries Attended By Skilled Birth Attendants (%) (UOM:%(Percentage)), Scaling Factor:1",

        "PNC_48h":
            "Women Received Post Partum Check Up Within 48 Hours Of Delivery (To Total Reported Deliveries) (%) (UOM:%(Percentage)), Scaling Factor:1",

        "Obstetric_Complications":
            "Pregnant Women With Obstetric Complications (Who Were Attended To) (To Total Reported Deliveries) (%) (UOM:%(Percentage)), Scaling Factor:1",
    }
}

for dataset, filename in FILES.items():

    print("\n" + "=" * 90)
    print(dataset)
    print("=" * 90)

    df = pd.read_csv(filename)

    selected = pd.DataFrame()

    for short_name, column in FEATURES[dataset].items():
        if column in df.columns:
            selected[short_name] = pd.to_numeric(df[column], errors="coerce")

    # Treat impossible percentages as missing for correlation analysis.
    selected = selected.mask((selected < 0) | (selected > 100))

    print("\nFeature correlation matrix:\n")
    print(selected.corr().round(2).to_string())

    print("\n\nHighly correlated pairs (|r| >= 0.80):")

    corr = selected.corr()

    for i in range(len(corr.columns)):
        for j in range(i + 1, len(corr.columns)):
            value = corr.iloc[i, j]

            if abs(value) >= 0.80:
                print(
                    f"{corr.columns[i]} <-> "
                    f"{corr.columns[j]} : {value:.2f}"
                )

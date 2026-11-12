import os
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_PATH = os.path.join(BASE_DIR, "outputs", "selected_features", "final_model_features.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs", "risk_classification", "sensitivity_without_severe_anemia")

FEATURES_5 = [
    "ANC_First_Trimester_Pct",
    "TT2_Booster_Pct",
    "Institutional_Delivery_Pct",
    "PNC_48h_Pct",
    "Obstetric_Complications_Pct",
]

FEATURES_6 = [
    "ANC_First_Trimester_Pct",
    "TT2_Booster_Pct",
    "Severe_Anemia_Pct",
    "Institutional_Delivery_Pct",
    "PNC_48h_Pct",
    "Obstetric_Complications_Pct",
]

KEEP_COLUMNS = ["State", "District", "Year", "source_dataset"]
RANDOM_STATE = 42
N_INIT = 10
K = 3
RISK_CLASSES = ["Low Risk", "Medium Risk", "High Risk"]


def run_experiment(features, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(INPUT_PATH)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[features])

    km = KMeans(n_clusters=K, random_state=RANDOM_STATE, n_init=N_INIT)
    labels = km.fit_predict(X_scaled)

    df["cluster_id"] = labels

    profiles = []
    for c in range(K):
        subset = df[df["cluster_id"] == c]
        profile = {"cluster_id": c, "cluster_size": len(subset)}
        for feat in features:
            profile[f"{feat}_mean"] = subset[feat].mean()
            profile[f"{feat}_median"] = subset[feat].median()
        profiles.append(profile)
    profiles_df = pd.DataFrame(profiles)

    centroids_scaled = pd.DataFrame(
        km.cluster_centers_,
        columns=[f"{f}_scaled" for f in features],
    )
    centroids_scaled.index.name = "cluster_id"
    centroids_original = pd.DataFrame(
        scaler.inverse_transform(km.cluster_centers_),
        columns=[f"{f}_original" for f in features],
    )
    centroids_original.index.name = "cluster_id"
    centroids = pd.concat([centroids_scaled, centroids_original], axis=1)

    metrics = {
        "silhouette_score": round(silhouette_score(X_scaled, labels), 6),
        "davies_bouldin_index": round(davies_bouldin_score(X_scaled, labels), 6),
        "calinski_harabasz_index": round(calinski_harabasz_score(X_scaled, labels), 6),
    }

    ranking = []
    for _, row in profiles_df.iterrows():
        score = 0.0
        for feat in ["ANC_First_Trimester_Pct", "TT2_Booster_Pct", "Institutional_Delivery_Pct", "PNC_48h_Pct"]:
            score -= row[f"{feat}_median"]
        for feat in ["Obstetric_Complications_Pct"]:
            score += row[f"{feat}_median"]
        ranking.append((row["cluster_id"], score))
    ranking.sort(key=lambda x: x[1])

    rank_map = {}
    for rank, (cid, _) in enumerate(ranking):
        rank_map[cid] = RISK_CLASSES[rank]
    df["risk_class"] = df["cluster_id"].map(rank_map)

    main_cols = KEEP_COLUMNS + features + ["cluster_id", "risk_class"]
    df[main_cols].to_csv(os.path.join(output_dir, "district_year_risk_clusters.csv"), index=False)
    profiles_df.to_csv(os.path.join(output_dir, "cluster_profiles.csv"), index=False)
    centroids.to_csv(os.path.join(output_dir, "cluster_centroids.csv"))

    with open(os.path.join(output_dir, "clustering_metrics.txt"), "w") as f:
        f.write("Clustering Metrics\n")
        f.write("=" * 50 + "\n")
        f.write(f"Features: {features}\n")
        f.write(f"K: {K}\n")
        f.write(f"random_state: {RANDOM_STATE}\n")
        f.write(f"n_init: {N_INIT}\n")
        f.write(f"Silhouette Score: {metrics['silhouette_score']}\n")
        f.write(f"Davies-Bouldin Index: {metrics['davies_bouldin_index']}\n")
        f.write(f"Calinski-Harabasz Index: {metrics['calinski_harabasz_index']}\n")
        f.write("\nCluster Sizes:\n")
        for _, row in profiles_df.iterrows():
            f.write(f"  Cluster {int(row['cluster_id'])}: {int(row['cluster_size'])} rows\n")

    return df, profiles_df, centroids, metrics


if __name__ == "__main__":
    result = run_experiment(FEATURES_5, OUTPUT_DIR)
    df, profiles, centroids, metrics = result
    print(f"Saved to {OUTPUT_DIR}")
    print(f"Shape: {df.shape}")
    print(f"Clusters: {df['cluster_id'].value_counts().sort_index().to_dict()}")
    print(f"Risk classes: {df['risk_class'].value_counts().to_dict()}")
    print(f"Metrics: {metrics}")

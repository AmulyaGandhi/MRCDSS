import os
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_PATH = os.path.join(BASE_DIR, "outputs", "selected_features", "final_model_features.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs", "risk_classification")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "district_year_risk_clusters.csv")

FEATURES = [
    "ANC_First_Trimester_Pct",
    "TT2_Booster_Pct",
    "Severe_Anemia_Pct",
    "Institutional_Delivery_Pct",
    "PNC_48h_Pct",
    "Obstetric_Complications_Pct",
]

PROTECTIVE = [
    "ANC_First_Trimester_Pct",
    "TT2_Booster_Pct",
    "Institutional_Delivery_Pct",
    "PNC_48h_Pct",
]

RISK = [
    "Severe_Anemia_Pct",
    "Obstetric_Complications_Pct",
]

KEEP_COLUMNS = ["State", "District", "Year", "source_dataset"]

CLUSTER_COL = "cluster_id"
RISK_CLASS_COL = "risk_class"
RISK_CLASSES = ["Low Risk", "Medium Risk", "High Risk"]

RANDOM_STATE = 42
N_INIT = 10
K = 3


def load_data():
    return pd.read_csv(INPUT_PATH)


def standardize(df):
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[FEATURES])
    return pd.DataFrame(X_scaled, columns=FEATURES), scaler


def run_clustering(X_scaled):
    km = KMeans(n_clusters=K, random_state=RANDOM_STATE, n_init=N_INIT)
    labels = km.fit_predict(X_scaled)
    return labels, km


def build_profiles(df, labels):
    df = df.copy()
    df[CLUSTER_COL] = labels
    profiles = []
    for c in range(K):
        subset = df[df[CLUSTER_COL] == c]
        profile = {"cluster_id": c, "cluster_size": len(subset)}
        for feat in FEATURES:
            profile[f"{feat}_mean"] = subset[feat].mean()
            profile[f"{feat}_median"] = subset[feat].median()
        profiles.append(profile)
    return pd.DataFrame(profiles), df


def compute_centroids(X_scaled, scaler, df):
    km_centroids_scaled = pd.DataFrame(
        KMeans(n_clusters=K, random_state=RANDOM_STATE, n_init=N_INIT).fit(X_scaled).cluster_centers_,
        columns=[f"{feat}_scaled" for feat in FEATURES],
    )
    km_centroids_scaled.index.name = "cluster_id"

    km = KMeans(n_clusters=K, random_state=RANDOM_STATE, n_init=N_INIT).fit(X_scaled)
    centroids_original = km.cluster_centers_
    centroids_original = scaler.inverse_transform(centroids_original)
    centroids_original = pd.DataFrame(
        centroids_original,
        columns=[f"{feat}_original" for feat in FEATURES],
    )
    centroids_original.index.name = "cluster_id"

    combined = pd.concat(
        [km_centroids_scaled, centroids_original], axis=1
    )
    return combined, km


def compute_metrics(X_scaled, labels):
    metrics = {}
    metrics["silhouette_score"] = round(silhouette_score(X_scaled, labels), 6)
    metrics["davies_bouldin_index"] = round(davies_bouldin_score(X_scaled, labels), 6)
    metrics["calinski_harabasz_index"] = round(calinski_harabasz_score(X_scaled, labels), 6)
    return metrics


def rank_clusters_by_risk(profiles_df):
    risk_scores = []
    for _, row in profiles_df.iterrows():
        score = 0.0
        for feat in PROTECTIVE:
            score -= row[f"{feat}_median"]
        for feat in RISK:
            score += row[f"{feat}_median"]
        risk_scores.append((row["cluster_id"], score))
    risk_scores.sort(key=lambda x: x[1])
    return risk_scores


def assign_risk_classes(df, profiles_df, risk_ranking):
    rank_map = {}
    for rank, (cluster_id, _) in enumerate(risk_ranking):
        rank_map[cluster_id] = RISK_CLASSES[rank]
    df = df.copy()
    df[RISK_CLASS_COL] = df[CLUSTER_COL].map(rank_map)
    return df


def run_clustering_pipeline():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df = load_data()
    X_scaled, scaler = standardize(df)
    labels, km = run_clustering(X_scaled)

    profiles_df, df_clustered = build_profiles(df, labels)
    centroids_df, km_fitted = compute_centroids(X_scaled, scaler, df)
    metrics = compute_metrics(X_scaled, labels)

    risk_ranking = rank_clusters_by_risk(profiles_df)
    df_classified = assign_risk_classes(df_clustered, profiles_df, risk_ranking)

    cluster_centroids_path = os.path.join(OUTPUT_DIR, "cluster_centroids.csv")
    centroids_df.to_csv(cluster_centroids_path)

    cluster_profiles_path = os.path.join(OUTPUT_DIR, "cluster_profiles.csv")
    profiles_df.to_csv(cluster_profiles_path, index=False)

    main_output_path = os.path.join(OUTPUT_DIR, "district_year_risk_clusters.csv")
    output_cols = KEEP_COLUMNS + FEATURES + [CLUSTER_COL, RISK_CLASS_COL]
    df_classified[output_cols].to_csv(main_output_path, index=False)

    metrics_path = os.path.join(OUTPUT_DIR, "clustering_metrics.txt")
    with open(metrics_path, "w") as f:
        f.write("Clustering Metrics\n")
        f.write("=" * 50 + "\n")
        f.write(f"K: {K}\n")
        f.write(f"random_state: {RANDOM_STATE}\n")
        f.write(f"n_init: {N_INIT}\n")
        f.write(f"Silhouette Score: {metrics['silhouette_score']}\n")
        f.write(f"Davies-Bouldin Index: {metrics['davies_bouldin_index']}\n")
        f.write(f"Calinski-Harabasz Index: {metrics['calinski_harabasz_index']}\n")
        f.write("\nCluster Sizes:\n")
        for _, row in profiles_df.iterrows():
            f.write(f"  Cluster {int(row['cluster_id'])}: {int(row['cluster_size'])} rows\n")

    return df_classified, profiles_df, centroids_df, metrics


if __name__ == "__main__":
    result = run_clustering_pipeline()
    df_classified = result[0]
    print(f"Main output: {os.path.join(OUTPUT_DIR, 'district_year_risk_clusters.csv')}")
    print(f"Shape: {df_classified.shape}")
    print(f"Cluster distribution:")
    print(df_classified["cluster_id"].value_counts().sort_index())
    print(f"Risk class distribution:")
    print(df_classified["risk_class"].value_counts())

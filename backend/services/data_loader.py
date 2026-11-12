import os
import pandas as pd

from config import (
    RISK_CLUSTERS_CSV,
    FINAL_FEATURES_CSV,
    DECISION_SUPPORT_CSV,
    CLUSTER_PROFILES_CSV,
    CLUSTERING_METRICS_TXT,
    MODEL_COMPARISON_CSV,
    BEST_MODEL_METRICS_JSON,
    SENSITIVITY_METRICS_TXT,
    SENSITIVITY_PROFILES_CSV,
    FEATURE_IMPORTANCE_CSV,
    PRIORITY_SUMMARY_CSV,
    PLANNING_RULES_CSV,
    PREPROCESSED_CSV,
)


def load_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)


def get_record_count(df: pd.DataFrame) -> int:
    return len(df) if df is not None else 0


def get_risk_distribution(df: pd.DataFrame) -> dict:
    if df is None:
        return {}
    counts = df["risk_class"].value_counts().to_dict()
    return {k: int(v) for k, v in counts.items()}


def get_priority_distribution(df: pd.DataFrame) -> dict:
    if df is None:
        return {}
    counts = df["priority_level"].value_counts().to_dict()
    return {k: int(v) for k, v in counts.items()}

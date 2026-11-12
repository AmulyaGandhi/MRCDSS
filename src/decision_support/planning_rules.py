import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FEATURES = [
    "ANC_First_Trimester_Pct",
    "TT2_Booster_Pct",
    "Severe_Anemia_Pct",
    "Institutional_Delivery_Pct",
    "PNC_48h_Pct",
    "Obstetric_Complications_Pct",
]

FEATURE_PLANNING_MAP = {
    "ANC_First_Trimester_Pct": "Strengthen early ANC registration and outreach",
    "TT2_Booster_Pct": "Strengthen antenatal TT/booster coverage",
    "Severe_Anemia_Pct": "Prioritize anemia screening, prevention and program coverage",
    "Institutional_Delivery_Pct": "Improve institutional-delivery access and service capacity",
    "PNC_48h_Pct": "Strengthen postnatal follow-up within 48 hours",
    "Obstetric_Complications_Pct": "Strengthen referral and emergency obstetric service planning",
}

RISK_TO_PRIORITY = {
    "High Risk": "High Priority",
    "Medium Risk": "Medium Priority",
    "Low Risk": "Low Priority",
}

INPUT_PATH = os.path.join(BASE_DIR, "outputs", "risk_classification", "district_year_risk_clusters.csv")
SHAP_PATH = os.path.join(BASE_DIR, "outputs", "explainability", "shap_values_test.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs", "decision_support")
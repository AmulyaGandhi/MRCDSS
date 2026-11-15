from pydantic import BaseModel
from typing import Optional, List, Dict


class HealthResponse(BaseModel):
    status: str
    version: str


class OverviewResponse(BaseModel):
    total_records: int
    state_district_units: int
    state_count: int
    year_coverage: dict
    risk_distribution: dict
    priority_distribution: dict
    feature_ranking: list


class ClusterProfile(BaseModel):
    cluster_id: int
    cluster_size: int
    risk_class: str
    ANC_First_Trimester_Pct: float
    TT2_Booster_Pct: float
    Severe_Anemia_Pct: float
    Institutional_Delivery_Pct: float
    PNC_48h_Pct: float
    Obstetric_Complications_Pct: float


class ClusteringMetrics(BaseModel):
    silhouette_score: float
    davies_bouldin_index: float
    calinski_harabasz_index: float


class ModelMetrics(BaseModel):
    model: str
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    selected: Optional[bool] = None


class ConfusionMatrixRow(BaseModel):
    actual: str
    predicted_high: int
    predicted_low: int
    predicted_medium: int


class SensitivityAnalysis(BaseModel):
    primary_features: int
    sensitivity_features: int
    primary_silhouette: float
    sensitivity_silhouette: float
    primary_high_risk_size: int
    sensitivity_high_risk_size: int
    risk_class_changed: int
    risk_class_change_proportion: float
    risk_class_agreement: float


class RiskAnalysisResponse(BaseModel):
    risk_counts: dict
    cluster_profiles: list
    clustering_metrics: ClusteringMetrics
    clustering_notes: dict
    model_comparison: list
    confusion_matrix: list
    evaluation_design: dict
    shap_summary: dict
    sensitivity_analysis: SensitivityAnalysis


class DistrictRecordResponse(BaseModel):
    state: str
    district: str
    year: int
    risk_class: str
    priority: str
    top_planning_focus: str


class DistrictRecordDetail(BaseModel):
    state: str
    district: str
    year: int
    risk_class: str
    priority: str
    ANC_First_Trimester_Pct: float
    TT2_Booster_Pct: float
    Severe_Anemia_Pct: float
    Institutional_Delivery_Pct: float
    PNC_48h_Pct: float
    Obstetric_Complications_Pct: float
    top_contributing_feature_1: str
    top_contributing_feature_2: str
    top_contributing_feature_3: str
    planning_focus_1: str
    planning_focus_2: str
    planning_focus_3: str


class DistrictDetailResponse(BaseModel):
    state: str
    district: str
    record_count: int
    years: list
    records: list


class ContributingFactor(BaseModel):
    feature: str
    value: float
    direction: str
    explanation: str


class DistrictProfileResponse(BaseModel):
    state: str
    district: str
    years_observed: int
    high_risk_years: int
    medium_risk_years: int
    low_risk_years: int
    high_risk_proportion: float
    latest_year: int
    latest_risk_class: str
    repeated_priority: str
    indicators: Optional[list] = None
    contributing_factors: Optional[list] = None
    planning_focus: Optional[list] = None


class PlanningRule(BaseModel):
    feature: str
    planning_focus: str
    feature_direction: str


class PlanningPrioritiesResponse(BaseModel):
    priority_distribution: dict
    latest_priority_distribution: dict
    repeated_priority_info: dict
    priority_semantics: dict
    planning_focus_label: str
    planning_focus_note: str
    planning_rules: list
    feature_planning_focus_counts: list
    feature_planning_focus_note: str


class MethodologyItem(BaseModel):
    category: str
    title: str
    value: str
    details: Optional[str] = None


class MethodologyResponse(BaseModel):
    items: list


class RecentHmisOverviewResponse(BaseModel):
    dataset: str
    total_observations: int
    observations_by_year: Dict[str, int]
    n_state_district_units: int
    n_states: int
    years: List[str]
    notes: Dict[str, str]
    year_availability: List[Dict]


class RecentHmisCoverageResponse(BaseModel):
    years_coverage: List[Dict]
    district_coverage: Dict


class RecentHmisIndicatorsResponse(BaseModel):
    indicators: List[Dict]
    distributions: Dict
    harmonization: List[Dict]
    data_quality: Dict
    disclaimer: str

export interface ClusterProfile {
  cluster_id: number;
  cluster_size: number;
  ANC_First_Trimester_Pct: number;
  TT2_Booster_Pct: number;
  Severe_Anemia_Pct: number;
  Institutional_Delivery_Pct: number;
  PNC_48h_Pct: number;
  Obstetric_Complications_Pct: number;
}

export interface ClusteringMetrics {
  silhouette_score: number;
  davies_bouldin_index: number;
  calinski_harabasz_index: number;
}

export interface ModelMetrics {
  model: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  roc_auc: number;
}

export interface ConfusionMatrixRow {
  actual: string;
  predicted_High_Risk: number;
  predicted_Low_Risk: number;
  predicted_Medium_Risk: number;
}

export interface SensitivityAnalysis {
  primary_features: number;
  sensitivity_features: number;
  primary_silhouette: number;
  sensitivity_silhouette: number;
  primary_high_risk_size: number;
  sensitivity_high_risk_size: number;
  risk_class_changed: number;
  risk_class_change_proportion: number;
  risk_class_agreement: number;
}

export interface ShapFeatureSummary {
  feature: string;
  positive_mean: number;
  negative_mean: number;
  mean_abs_shap: number;
  positive_count: number;
  negative_count: number;
}

export interface RiskAnalysisData {
  risk_counts: Record<string, number>;
  cluster_profiles: ClusterProfile[];
  clustering_metrics: ClusteringMetrics;
  clustering_notes: {
    k_selection: string;
    silhouette_interpretation: string;
    label_sensitivity: string;
  };
  model_comparison: ModelMetrics[];
  confusion_matrix: ConfusionMatrixRow[];
  evaluation_design: {
    label_source: string;
    selection_metric: string;
    test_records: number;
    test_units: number;
    test_units_also_in_training: number;
    test_records_sharing_units_with_training: number;
    test_records_sharing_units_with_training_proportion: number;
    grouped_or_temporal_validation_completed: boolean;
    note: string;
  };
  shap_summary: {
    class_label: string;
    records: number;
    features: ShapFeatureSummary[];
    note: string;
  };
  sensitivity_analysis: SensitivityAnalysis;
}

export async function getRiskAnalysis(): Promise<RiskAnalysisData> {
  const { apiGet } = await import('./client');
  return apiGet<RiskAnalysisData>('/api/risk-analysis');
}

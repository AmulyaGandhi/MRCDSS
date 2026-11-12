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
  sensitivity_high_risk_size: number;
}

export interface RiskAnalysisData {
  risk_counts: Record<string, number>;
  cluster_profiles: ClusterProfile[];
  clustering_metrics: ClusteringMetrics;
  model_comparison: ModelMetrics[];
  confusion_matrix: ConfusionMatrixRow[];
  sensitivity_analysis: SensitivityAnalysis;
}

export async function getRiskAnalysis(): Promise<RiskAnalysisData> {
  const { apiGet } = await import('./client');
  return apiGet<RiskAnalysisData>('/api/risk-analysis');
}

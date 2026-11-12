export interface RiskProfile {
  total: number;
  low: number;
  medium: number;
  high: number;
}

export interface ClusterProfile {
  name: string;
  interpretation: string;
  indicators: {
    ancFirstTrimester: number;
    tt2Booster: number;
    severeAnemia: number;
    institutionalDelivery: number;
    pnc48h: number;
    obstetricComplications: number;
  };
}

export interface ClusteringQuality {
  silhouette: number;
  daviesBouldin: number;
  calinskiHarabasz: number;
}

export interface ModelMetrics {
  model: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  rocAuc: number;
  selected?: boolean;
}

export interface ConfusionMatrixRow {
  actual: string;
  predictedHigh: number;
  predictedLow: number;
  predictedMedium: number;
}

export interface SensitivityAnalysis {
  primaryFeatures: number;
  sensitivityFeatures: number;
  primarySilhouette: number;
  sensitivitySilhouette: number;
  sensitivityHighRiskSize: number;
}

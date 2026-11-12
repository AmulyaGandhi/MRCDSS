import type {
  RiskProfile,
  ClusterProfile,
  ClusteringQuality,
  ModelMetrics,
  ConfusionMatrixRow,
  SensitivityAnalysis,
} from '../types/riskAnalysis';

export const riskProfile: RiskProfile = {
  total: 8405,
  low: 4446,
  medium: 1345,
  high: 2614,
};

export const clusterProfiles: ClusterProfile[] = [
  {
    name: 'Low Risk',
    interpretation:
      'Low Risk has the strongest overall balance across protective maternal-health indicators. This profile does not imply a causal relationship.',
    indicators: {
      ancFirstTrimester: 67.7,
      tt2Booster: 89.2,
      severeAnemia: 3.6,
      institutionalDelivery: 69.8,
      pnc48h: 69.7,
      obstetricComplications: 5.8,
    },
  },
  {
    name: 'Medium Risk',
    interpretation:
      'Medium Risk is strongly characterized by severe anemia prevalence. This profile does not imply a causal relationship.',
    indicators: {
      ancFirstTrimester: 81.7,
      tt2Booster: 90.3,
      severeAnemia: 67.6,
      institutionalDelivery: 74.6,
      pnc48h: 68.8,
      obstetricComplications: 5.7,
    },
  },
  {
    name: 'High Risk',
    interpretation:
      'High Risk has the weakest protective maternal-health indicator profile across most measures. This profile does not imply a causal relationship.',
    indicators: {
      ancFirstTrimester: 39.7,
      tt2Booster: 75.5,
      severeAnemia: 4.9,
      institutionalDelivery: 42.3,
      pnc48h: 57.1,
      obstetricComplications: 3.2,
    },
  },
];

export const clusteringQuality: ClusteringQuality = {
  silhouette: 0.238,
  daviesBouldin: 1.474,
  calinskiHarabasz: 2276.145,
};

export const modelMetrics: ModelMetrics[] = [
  { model: 'Logistic Regression', accuracy: 0.9958, precision: 0.9957, recall: 0.9943, f1: 0.9950, rocAuc: 1.0, selected: true },
  { model: 'Decision Tree', accuracy: 0.9417, precision: 0.9430, recall: 0.9473, f1: 0.9451, rocAuc: 0.9569 },
  { model: 'Random Forest', accuracy: 0.9649, precision: 0.9650, recall: 0.9695, f1: 0.9672, rocAuc: 0.9979 },
  { model: 'XGBoost', accuracy: 0.9697, precision: 0.9680, recall: 0.9705, f1: 0.9693, rocAuc: 0.9987 },
];

export const confusionMatrix: ConfusionMatrixRow[] = [
  { actual: 'High', predictedHigh: 521, predictedLow: 2, predictedMedium: 0 },
  { actual: 'Low', predictedHigh: 1, predictedLow: 887, predictedMedium: 1 },
  { actual: 'Medium', predictedHigh: 2, predictedLow: 1, predictedMedium: 266 },
];

export const sensitivityAnalysis: SensitivityAnalysis = {
  primaryFeatures: 6,
  sensitivityFeatures: 5,
  primarySilhouette: 0.238,
  sensitivitySilhouette: 0.231,
  sensitivityHighRiskSize: 961,
};

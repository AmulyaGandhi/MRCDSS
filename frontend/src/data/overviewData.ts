import type { DatasetSummary, PriorityInfo, FeatureRank, WorkflowStep, QuickAction } from '../types';

export const datasetSummary: DatasetSummary = {
  districtYearRecords: 8405,
  districtStateUnits: 707,
  states: 36,
  coverageStart: 2008,
  coverageEnd: 2019,
};

export const priorityData: PriorityInfo[] = [
  { riskClass: 'Low Risk', priorityLevel: 'Low Priority', count: 4446 },
  { riskClass: 'Medium Risk', priorityLevel: 'Medium Priority', count: 1345 },
  { riskClass: 'High Risk', priorityLevel: 'High Priority', count: 2614 },
];

export const featureRanking: FeatureRank[] = [
  { rank: 1, variableName: 'ANC_First_Trimester_Pct', displayName: 'Antenatal Care — First Trimester' },
  { rank: 2, variableName: 'Institutional_Delivery_Pct', displayName: 'Institutional Delivery' },
  { rank: 3, variableName: 'TT2_Booster_Pct', displayName: 'Tetanus Toxoid Booster (TT2)' },
  { rank: 4, variableName: 'PNC_48h_Pct', displayName: 'Postnatal Care within 48 Hours' },
  { rank: 5, variableName: 'Severe_Anemia_Pct', displayName: 'Severe Anemia' },
  { rank: 6, variableName: 'Obstetric_Complications_Pct', displayName: 'Obstetric Complications' },
];

export const workflowSteps: WorkflowStep[] = [
  { step: 1, label: 'HMIS Data' },
  { step: 2, label: 'Preprocessing' },
  { step: 3, label: 'Feature Selection' },
  { step: 4, label: 'Risk Profile Derivation' },
  { step: 5, label: 'ML Classification' },
  { step: 6, label: 'SHAP Explainability' },
  { step: 7, label: 'Decision Support' },
  { step: 8, label: 'District Prioritization' },
];

export const quickActions: QuickAction[] = [
  { label: 'Explore Districts', description: 'Browse district-level health data and indicators.', route: '/districts' },
  { label: 'View Risk Analysis', description: 'Analyze risk factor distributions and trends.', route: '/risk-analysis' },
  { label: 'View Planning Priorities', description: 'Review planning priorities by district.', route: '/planning' },
  { label: 'Read Methodology', description: 'Understand the methods and algorithms used.', route: '/methodology' },
];

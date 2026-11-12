export interface DatasetSummary {
  districtYearRecords: number;
  districtStateUnits: number;
  states: number;
  coverageStart: number;
  coverageEnd: number;
}

export interface PriorityInfo {
  riskClass: string;
  priorityLevel: string;
  count: number;
}

export interface FeatureRank {
  rank: number;
  variableName: string;
  displayName: string;
}

export interface WorkflowStep {
  step: number;
  label: string;
}

export interface QuickAction {
  label: string;
  description: string;
  route: string;
}

export interface DistrictRecord {
  state: string;
  district: string;
  year: number;
  riskClass: 'Low' | 'Medium' | 'High';
  priority: 'Low' | 'Medium' | 'High';
  topPlanningFocus: string;
}

export interface HealthIndicator {
  name: string;
  value: number;
  unit: string;
  interpretation: string;
}

export interface ContributingFactor {
  feature: string;
  value?: number;
  direction?: 'positive' | 'negative';
  explanation?: string;
}

export interface PlanningPriority {
  text: string;
}

export interface DistrictDetail {
  state: string;
  district: string;
  year: number;
  riskClass: 'Low' | 'Medium' | 'High';
  priority: 'Low' | 'Medium' | 'High';
  indicators: HealthIndicator[];
  contributingFactors: ContributingFactor[];
  planningPriorities: string[];
}

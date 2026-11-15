export interface PlanningPriority {
  feature: string;
  planning_focus: string;
  feature_direction: string;
}

export interface FeaturePlanningFocusCount {
  feature: string;
  record_top3_appearances: number;
  record_top1_appearances: number;
  latest_units_top3: number;
  latest_units_top1: number;
}

export interface RepeatedPriorityInfo {
  total_units: number;
  total_district_year_records: number;
  repeated_high: number;
  repeated_medium: number;
  repeated_low: number;
  insufficient_history: number;
  repeated_high_proportion: number;
  repeated_medium_proportion: number;
  repeated_low_proportion: number;
  latest_observation_year: number | null;
  rule: string;
  label: string;
}

export interface PlanningPrioritiesData {
  priority_distribution: Record<string, number>;
  latest_priority_distribution: Record<string, number>;
  repeated_priority_info: RepeatedPriorityInfo;
  priority_semantics: {
    priority_distribution: string;
    latest_priority_distribution: string;
    repeated_priority_info: string;
  };
  planning_focus_label: string;
  planning_focus_note: string;
  planning_rules: PlanningPriority[];
  feature_planning_focus_counts: FeaturePlanningFocusCount[];
  feature_planning_focus_note: string;
}

export async function getPlanningPriorities(): Promise<PlanningPrioritiesData> {
  const { apiGet } = await import('./client');
  return apiGet<PlanningPrioritiesData>('/api/planning-priorities');
}

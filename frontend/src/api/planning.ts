export interface PlanningPriority {
  feature: string;
  planning_focus: string;
  feature_direction: string;
}

export interface FeaturePlanningFocusCount {
  feature: string;
  count: number;
}

export interface PlanningPrioritiesData {
  priority_distribution: Record<string, number>;
  persistent_priority_info: {
    total_districts: number;
    persistent_high: number;
    persistent_medium: number;
    persistent_low: number;
  };
  planning_rules: PlanningPriority[];
  feature_planning_focus_counts: FeaturePlanningFocusCount[];
}

export async function getPlanningPriorities(): Promise<PlanningPrioritiesData> {
  const { apiGet } = await import('./client');
  return apiGet<PlanningPrioritiesData>('/api/planning-priorities');
}

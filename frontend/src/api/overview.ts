export interface OverviewData {
  total_records: number;
  state_district_units: number;
  state_count: number;
  year_coverage: {
    start: number;
    end: number;
  };
  risk_distribution: Record<string, number>;
  priority_distribution: Record<string, number>;
  feature_ranking: Array<{
    feature: string;
    mean_abs_shap: number;
  }>;
}

export async function getOverview(): Promise<OverviewData> {
  const { apiGet } = await import('./client');
  return apiGet<OverviewData>('/api/overview');
}

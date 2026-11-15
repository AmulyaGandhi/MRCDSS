export interface RecentHmisOverviewData {
  dataset: string;
  total_observations: number;
  observations_by_year: Record<string, number>;
  n_state_district_units: number;
  n_states: number;
  years: string[];
  notes: {
    partial_2024_2025: string;
    not_included_2025_2026: string;
  };
  year_availability: Array<{
    fiscal_year: string;
    availability: string;
  }>;
}

export interface RecentHmisCoverageData {
  years_coverage: Array<{
    fiscal_year: string;
    observations: number;
    states: number;
    partial: boolean;
  }>;
  district_coverage: {
    reference_707_units: number;
    dataset_3_distinct_identifiers: number;
    difference: number;
    by_candidate_type: Array<{ type: string; count: number }>;
    reference_note: string;
    native_representation_note: string;
  };
}

export interface RecentHmisIndicatorsData {
  indicators: Array<{
    key: string;
    name: string;
    valid: number;
    missing: number;
    status: string;
    note: string;
  }>;
  distributions: Record<
    string,
    {
      bins: Array<{ label: string; count: number }>;
      total_values: number;
    }
  >;
  harmonization: Array<{
    indicator: string;
    status: string;
    reason: string;
  }>;
  data_quality: {
    total_flags: number;
    missing_flags: number;
    range_flags: number;
    structural_flags: number;
    zero_denominator_flags: number;
    by_feature: Record<
      string,
      {
        flags: number;
        missing_flags: number;
        range_flags: number;
        structural_flags: number;
        zero_denominator_flags: number;
        max_out_of_range_value: number | null;
      }
    >;
    note: string;
  };
  disclaimer: string;
}

export interface RecentHmisLatestRecord {
  state: string;
  district: string;
  year: string;
  ANC_First_Trimester_Pct: number | null;
  TT2_Booster_Pct: number | null;
  Severe_Anemia_Pct: number | null;
  Obstetric_Complications_Pct: number | null;
}

export interface RecentHmisDistrictsLatestResponse {
  count: number;
  records: RecentHmisLatestRecord[];
  note: string;
}

export async function getRecentHmisDistrictsLatest(): Promise<RecentHmisDistrictsLatestResponse> {
  const { apiGet } = await import('./client');
  return apiGet<RecentHmisDistrictsLatestResponse>('/api/recent-hmis/districts/latest');
}

export async function getRecentHmisOverview(): Promise<RecentHmisOverviewData> {
  const { apiGet } = await import('./client');
  return apiGet<RecentHmisOverviewData>('/api/recent-hmis/overview');
}

export async function getRecentHmisCoverage(): Promise<RecentHmisCoverageData> {
  const { apiGet } = await import('./client');
  return apiGet<RecentHmisCoverageData>('/api/recent-hmis/coverage');
}

export async function getRecentHmisIndicators(): Promise<RecentHmisIndicatorsData> {
  const { apiGet } = await import('./client');
  return apiGet<RecentHmisIndicatorsData>('/api/recent-hmis/indicators');
}
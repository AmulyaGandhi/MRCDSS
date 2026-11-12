export interface UnifiedOverviewData {
  dataset: string;
  total_observations: number;
  counts_by_source: {
    dataset1: number;
    dataset2: number;
    recent_hmis: number;
  };
  counts_by_era: {
    HISTORICAL_MRCDSS: number;
    RECENT_HMIS: number;
  };
  n_state_district_units: number;
  n_states: number;
  historical_years: string[];
  recent_years: string[];
  period_texts: {
    data_coverage: string;
    risk_model_period: string;
    recent_hmis_extension: string;
    partial_2024_2025: string;
  };
  feature_availability: Array<{
    key: string;
    name: string;
    historical_valid: number;
    historical_total: number;
    recent_valid: number;
    recent_total: number;
  }>;
  risk_classification: {
    historical_with_risk: number;
    recent_with_risk: number;
    note: string;
  };
}

export interface UnifiedDistrictSummary {
  state: string;
  district: string;
  historical_records: number;
  recent_records: number;
  historical_years: string[];
  recent_years: string[];
  latest_historical_year: string | null;
  latest_historical_risk_class: string | null;
  latest_recent_year: string | null;
}

export interface UnifiedDistrictsData {
  count: number;
  districts: UnifiedDistrictSummary[];
}

export interface UnifiedHistoricalRecord {
  Year: string;
  risk_class: string;
  priority_level: string;
  top_contributing_feature_1: string | null;
  top_contributing_feature_2: string | null;
  top_contributing_feature_3: string | null;
  planning_focus_1: string | null;
  planning_focus_2: string | null;
  planning_focus_3: string | null;
  ANC_First_Trimester_Pct: number | null;
  TT2_Booster_Pct: number | null;
  Severe_Anemia_Pct: number | null;
  Institutional_Delivery_Pct: number | null;
  SBA_Home_Delivery_Pct: number | null;
  PNC_48h_Pct: number | null;
  Obstetric_Complications_Pct: number | null;
}

export interface UnifiedRecentRecord {
  Year: string;
  ANC_First_Trimester_Pct: number | null;
  TT2_Booster_Pct: number | null;
  Severe_Anemia_Pct: number | null;
  Institutional_Delivery_Pct: number | null;
  SBA_Home_Delivery_Pct: number | null;
  PNC_48h_Pct: number | null;
  Obstetric_Complications_Pct: number | null;
  source_dataset: string;
  hmis_source_file: string | null;
  indicator_definition_status: string;
}

export interface UnifiedDistrictDetail {
  state: string;
  district: string;
  matched: boolean;
  historical: UnifiedHistoricalRecord[];
  recent: UnifiedRecentRecord[];
  period_texts: UnifiedOverviewData['period_texts'];
}

export interface UnifiedYearsData {
  historical: string[];
  recent: string[];
  period_texts: UnifiedOverviewData['period_texts'];
}

export async function getUnifiedOverview(): Promise<UnifiedOverviewData> {
  const { apiGet } = await import('./client');
  return apiGet<UnifiedOverviewData>('/api/unified/overview');
}

export async function getUnifiedDistricts(): Promise<UnifiedDistrictsData> {
  const { apiGet } = await import('./client');
  return apiGet<UnifiedDistrictsData>('/api/unified/districts');
}

export async function getUnifiedDistrict(state: string, district: string): Promise<UnifiedDistrictDetail> {
  const { apiGet } = await import('./client');
  return apiGet<UnifiedDistrictDetail>(`/api/unified/districts/${encodeURIComponent(state)}/${encodeURIComponent(district)}`);
}

export async function getUnifiedYears(): Promise<UnifiedYearsData> {
  const { apiGet } = await import('./client');
  return apiGet<UnifiedYearsData>('/api/unified/years');
}
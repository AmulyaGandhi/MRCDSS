export interface DistrictRecordDetail {
  state: string;
  district: string;
  year: number;
  risk_class: string;
  priority: string;
  top_contributing_feature_1: string;
  top_contributing_feature_2: string;
  top_contributing_feature_3: string;
  planning_focus_1: string;
  planning_focus_2: string;
  planning_focus_3: string;
  ANC_First_Trimester_Pct: number;
  TT2_Booster_Pct: number;
  Severe_Anemia_Pct: number;
  Institutional_Delivery_Pct: number;
  PNC_48h_Pct: number;
  Obstetric_Complications_Pct: number;
}

export interface PriorityHistory {
  repeated_priority: string;
  years_observed: number;
  high_risk_years: number;
  medium_risk_years: number;
  low_risk_years: number;
  high_risk_proportion: number;
  medium_risk_proportion: number;
  low_risk_proportion: number;
  latest_year: number;
  latest_risk_class: string;
  latest_priority: string;
  rule: string;
}

export interface DistrictDetailResponse {
  state: string;
  district: string;
  record_count: number;
  years: number[];
  latest_year: number | null;
  assessment_scope: string;
  priority_history: PriorityHistory | null;
  records: DistrictRecordDetail[];
}

export async function getDistrictDetail(state: string, district: string): Promise<DistrictDetailResponse> {
  const { apiGet } = await import('./client');
  const stateParam = encodeURIComponent(state);
  const districtParam = encodeURIComponent(district);
  return apiGet<DistrictDetailResponse>(`/api/districts/${stateParam}/${districtParam}`);
}

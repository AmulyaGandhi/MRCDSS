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

export interface DistrictDetailResponse {
  state: string;
  district: string;
  record_count: number;
  years: number[];
  records: DistrictRecordDetail[];
}

export async function getDistrictDetail(state: string, district: string): Promise<DistrictDetailResponse> {
  const { apiGet } = await import('./client');
  const stateParam = encodeURIComponent(state);
  const districtParam = encodeURIComponent(district);
  return apiGet<DistrictDetailResponse>(`/api/districts/${stateParam}/${districtParam}`);
}

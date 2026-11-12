export interface DistrictRecord {
  state: string;
  district: string;
  year: number;
  risk_class: string;
  priority: string;
  top_planning_focus: string;
}

export interface LatestDistrictRecord {
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
}

export interface LatestDistrictsResponse {
  count: number;
  records: LatestDistrictRecord[];
  total: number;
}

export interface DistrictListResponse {
  count: number;
  records: DistrictRecord[];
  page: number;
  per_page: number;
  total: number;
}

export interface StateListResponse {
  states: string[];
}

export interface YearListResponse {
  years: number[];
}

export async function getLatestDistrictObservations(): Promise<LatestDistrictsResponse> {
  const { apiGet } = await import('./client');
  return apiGet<LatestDistrictsResponse>('/api/districts/latest');
}

export async function getDistricts(params: {
  state?: string;
  district?: string;
  risk_class?: string;
  priority?: string;
  year?: number;
  page?: number;
  per_page?: number;
}): Promise<DistrictListResponse> {
  const { apiGet } = await import('./client');
  const searchParams = new URLSearchParams();
  if (params.state) searchParams.set('state', params.state);
  if (params.district) searchParams.set('district', params.district);
  if (params.risk_class) searchParams.set('risk_class', params.risk_class);
  if (params.priority) searchParams.set('priority', params.priority);
  if (params.year !== undefined) searchParams.set('year', String(params.year));
  if (params.page !== undefined) searchParams.set('page', String(params.page));
  if (params.per_page !== undefined) searchParams.set('per_page', String(params.per_page));

  const query = searchParams.toString();
  return apiGet<DistrictListResponse>(`/api/districts${query ? `?${query}` : ''}`);
}

export async function getStates(): Promise<StateListResponse> {
  const { apiGet } = await import('./client');
  return apiGet<StateListResponse>('/api/districts/states');
}

export async function getYears(): Promise<YearListResponse> {
  const { apiGet } = await import('./client');
  return apiGet<YearListResponse>('/api/districts/years');
}

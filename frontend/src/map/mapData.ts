import type { Feature, FeatureCollection, Geometry, GeoJsonProperties } from 'geojson';

export type DistrictMapFeature = Feature<Geometry, GeoJsonProperties & { state: string; district: string }>;
export type DistrictMapFeatureCollection = FeatureCollection<Geometry, GeoJsonProperties & { state: string; district: string }>;

export interface StateMapEntry {
  file: string;
  count: number;
  bytes: number;
}

export interface IndiaDistrictsIndex {
  [state: string]: StateMapEntry;
}

export async function loadIndiaDistrictsIndex(): Promise<IndiaDistrictsIndex> {
  const res = await fetch('/data/india_districts_index.json');
  if (!res.ok) throw new Error('Failed to load district index');
  return res.json();
}

export async function loadStateDistricts(state: string): Promise<DistrictMapFeatureCollection> {
  const entry = (await loadIndiaDistrictsIndex())[state];
  if (!entry) throw new Error(`No boundary data for state: ${state}`);
  const res = await fetch(`/data/states/${encodeURIComponent(state)}.geojson`);
  if (!res.ok) throw new Error(`Failed to load boundaries for state: ${state}`);
  return res.json() as Promise<DistrictMapFeatureCollection>;
}
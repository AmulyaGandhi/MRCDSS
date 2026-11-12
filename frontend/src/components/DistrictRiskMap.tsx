import { useEffect, useMemo, useState } from 'react';
import { MapContainer, TileLayer, GeoJSON, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { Feature, FeatureCollection, Geometry, GeoJsonProperties } from 'geojson';
import type { LatestDistrictRecord } from '../api/districts';
import { loadIndiaDistrictsIndex, type IndiaDistrictsIndex } from '../map/mapData';

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const RISK_COLORS: Record<string, string> = {
  'Low Risk': '#2e7d32',
  'Medium Risk': '#f9a825',
  'High Risk': '#c62828',
};

export const NO_DATA_FILL = '#8d99a6';

const INDIA_BOUNDS: [[number, number], [number, number]] = [
  [5.0, 67.5],
  [37.5, 98.0],
];

const NEUTRAL_FILL = { fillColor: NO_DATA_FILL, color: '#7d8696', weight: 0.6, fillOpacity: 1 };

function riskColor(value: string): string {
  return RISK_COLORS[value] || NO_DATA_FILL;
}

export type DistrictMapRecord = LatestDistrictRecord;

interface DistrictMapProps {
  records: DistrictMapRecord[];
  selectedKey: string | null;
  onDistrictSelect: (record: DistrictMapRecord) => void;
  onNoDataSelect?: () => void;
}

function DistrictLayer({ records, selectedKey, onDistrictSelect, onNoDataSelect }: DistrictMapProps) {
  const [geoByState, setGeoByState] = useState<Record<string, FeatureCollection | null>>({});
  const [loadedStates, setLoadedStates] = useState<Set<string>>(new Set());

  const recordByKey = useMemo(
    () => new Map(records.map((r) => [`${r.state}||${r.district}`, r] as [string, DistrictMapRecord])),
    [records],
  );

  useEffect(() => {
    let active = true;
    (async () => {
      let index: IndiaDistrictsIndex;
      try {
        index = await loadIndiaDistrictsIndex();
      } catch (err) {
        console.warn('Failed to load district index', err);
        return;
      }
      if (!active) return;
      const allStates = Object.keys(index);
      for (const state of allStates) {
        if (loadedStates.has(state)) continue;
        try {
          const res = await fetch(`/data/states/${encodeURIComponent(state)}.geojson`);
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          const fc = (await res.json()) as FeatureCollection;
          if (!active) return;
          setGeoByState((prev) => ({ ...prev, [state]: fc }));
          setLoadedStates((prev) => new Set(prev).add(state));
        } catch (err) {
          console.warn('Failed to load boundaries for', state, err);
        }
      }
    })();
    return () => { active = false; };
  }, [loadedStates]);

  const styleFeature = (feature: Feature<Geometry, GeoJsonProperties> | undefined, state: string) => {
    if (!feature || !feature.properties) return NEUTRAL_FILL;
    const district = feature.properties.district as string;
    const key = `${state}||${district}`;
    const rec = recordByKey.get(key);
    if (!rec) return NEUTRAL_FILL;
    const selected = selectedKey === key;
    return {
      fillColor: riskColor(rec.risk_class),
      color: selected ? '#1a237e' : '#424242',
      weight: selected ? 2.5 : 0.5,
      fillOpacity: selected ? 0.85 : 0.65,
    };
  };

  const onEachFeature = (feature: Feature<Geometry, GeoJsonProperties> | undefined, layer: L.Layer) => {
    if (!feature || !feature.properties) return;
    const state = feature.properties.state as string;
    const district = feature.properties.district as string;
    const key = `${state}||${district}`;
    const rec = recordByKey.get(key);
    layer.on({
      click: () => {
        if (rec) onDistrictSelect(rec);
        else if (onNoDataSelect) onNoDataSelect();
      },
      mouseover: (e) => {
        const target = e.target as L.Path;
        target.setStyle({ weight: 1.5, color: '#1a237e' });
        target.bringToFront();
      },
      mouseout: (e) => {
        const target = e.target as L.Path;
        target.setStyle(styleFeature(feature, state));
      },
    });
    (layer as any).bindTooltip(
      rec ? `${district}, ${state}: ${rec.risk_class}` : `${district}, ${state}: No data available`,
      { direction: 'top', offset: [0, -4] },
    );
  };

  return (
    <>
      {Object.entries(geoByState).map(([state, fc]) =>
        fc ? (
          <GeoJSON
            key={state}
            data={fc}
            style={(feature) => styleFeature(feature, state)}
            onEachFeature={onEachFeature}
          />
        ) : null
      )}
    </>
  );
}

function MapController({ onBounds }: { onBounds: (b: L.LatLngBounds) => void }) {
  const map = useMapEvents({
    moveend: () => onBounds(map.getBounds()),
  });
  return null;
}

export interface DistrictRiskMapProps {
  records: DistrictMapRecord[];
  selectedKey: string | null;
  onDistrictSelect: (record: DistrictMapRecord) => void;
  onBoundsChange?: (bounds: L.LatLngBounds) => void;
  onNoDataSelect?: () => void;
}

export default function DistrictRiskMap({
  records,
  selectedKey,
  onDistrictSelect,
  onBoundsChange,
  onNoDataSelect,
}: DistrictRiskMapProps) {
  const handleBounds = (b: L.LatLngBounds) => {
    if (onBoundsChange) onBoundsChange(b);
  };

  return (
    <div className="district-risk-map">
      <MapContainer
        center={[22.0, 82.0]}
        zoom={5}
        bounds={INDIA_BOUNDS}
        boundsOptions={{ padding: [16, 16] }}
        minZoom={4}
        maxZoom={12}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom
        doubleClickZoom
        zoomControl
        attributionControl
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
          subdomains="abcd"
        />
        <DistrictLayer
          records={records}
          selectedKey={selectedKey}
          onDistrictSelect={onDistrictSelect}
          onNoDataSelect={onNoDataSelect}
        />
        <MapController onBounds={handleBounds} />
      </MapContainer>
    </div>
  );
}
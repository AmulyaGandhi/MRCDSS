import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import AppLayout from '../components/AppLayout';
import DistrictRiskMap, { type DistrictMapRecord } from '../components/DistrictRiskMap';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import { getOverview } from '../api/overview';
import { getPlanningPriorities } from '../api/planning';
import { getLatestDistrictObservations, type LatestDistrictRecord } from '../api/districts';
import {
  getRecentHmisOverview,
  getRecentHmisIndicators,
  type RecentHmisOverviewData,
  type RecentHmisIndicatorsData,
} from '../api/recentHmis';
import KpiCard from '../components/KpiCard';
import { BarChart3, MapPin, AlertTriangle, TrendingUp, Shield } from 'lucide-react';
import { ASSISTANT_DISTRICT_EVENT } from '../components/Assistant';

const RISK_COLORS: Record<string, string> = {
  Low: '#3a8248',
  Medium: '#c27d2f',
  High: '#b94538',
};

function riskColor(riskClass: string) {
  const key = riskClass.replace(' Risk', '');
  return RISK_COLORS[key] ?? '#7a8797';
}

export default function Overview() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [overviewData, setOverviewData] = useState<{
    total_records: number;
    state_district_units: number;
    state_count: number;
    year_coverage: { start: number; end: number };
    risk_distribution: Record<string, number>;
    priority_distribution: Record<string, number>;
    feature_ranking: Array<{ feature: string; mean_abs_shap: number }>;
  } | null>(null);
  const [planningData, setPlanningData] = useState<{
    latest_priority_distribution: Record<string, number>;
    planning_rules: Array<{ feature: string; planning_focus: string; feature_direction: string }>;
  } | null>(null);
  const [mapRecords, setMapRecords] = useState<LatestDistrictRecord[]>([]);
  const [mapError, setMapError] = useState<string | null>(null);
  const [selectedDistrict, setSelectedDistrict] = useState<DistrictMapRecord | null>(null);
  const [recentOverview, setRecentOverview] = useState<RecentHmisOverviewData | null>(null);
  const [recentIndicators, setRecentIndicators] = useState<RecentHmisIndicatorsData | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    setMapError(null);
    try {
      const [overview, planning, latest, recentOverviewData, recentIndicatorsData] =
        await Promise.all([
          getOverview(),
          getPlanningPriorities(),
          getLatestDistrictObservations().catch((err) => {
            setMapError(err instanceof Error ? err.message : 'District boundaries unavailable.');
            return { count: 0, records: [], total: 0 };
          }),
          getRecentHmisOverview().catch(() => null),
          getRecentHmisIndicators().catch(() => null),
        ]);
      setOverviewData(overview);
      setPlanningData(planning);
      setMapRecords(latest.records);
      setRecentOverview(recentOverviewData);
      setRecentIndicators(recentIndicatorsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    window.dispatchEvent(
      new CustomEvent(ASSISTANT_DISTRICT_EVENT, {
        detail: selectedDistrict
          ? { state: selectedDistrict.state, district: selectedDistrict.district }
          : null,
      }),
    );
  }, [selectedDistrict]);

  const selectedKey = selectedDistrict
    ? `${selectedDistrict.state}||${selectedDistrict.district}`
    : null;

  if (loading) {
    return (
      <AppLayout>
        <div className="content condensed">
          <LoadingState />
        </div>
      </AppLayout>
    );
  }

  if (error || !overviewData || !planningData) {
    return (
      <AppLayout>
        <div className="content condensed">
          <ErrorState message={error ?? 'No data available.'} onRetry={fetchData} />
        </div>
      </AppLayout>
    );
  }

  const riskDist = overviewData.risk_distribution;
  const priorityDist = overviewData.priority_distribution;
  const totalRecords = Object.values(riskDist).reduce((s, v) => s + v, 0);
  const totalUnits = Object.values(priorityDist).reduce((s, v) => s + v, 0);
  const highRiskCount = riskDist['High Risk'] ?? 0;

  const recentValid = recentIndicators?.indicators.find(
    (i) => i.key === 'ANC_First_Trimester_Pct',
  )?.valid ?? 0;
  const recentMissing = recentIndicators?.indicators.find(
    (i) => i.key === 'ANC_First_Trimester_Pct',
  )?.missing ?? 0;

  return (
    <AppLayout>
      <div className="content">
        <div className="page-header">
          <div className="page-header-main">
            <span className="page-kicker">Executive Dashboard</span>
            <h1 className="page-title">District Health Intelligence</h1>
            <p className="page-subtitle">
              MRCDSS combines historical district-level risk classification (2008–2019) with Recent HMIS
              evidence (2020–2025) to support district health planning. The map shows the latest historical
              MRCDSS risk classification per district; recent HMIS evidence is contextual only and carries no
              risk classification.
            </p>
          </div>
          <div className="page-actions">
            <Link to="/districts" className="btn btn-outline btn-sm">
              <MapPin size={16} strokeWidth={2} /> Browse Districts
            </Link>
          </div>
        </div>

        {/* KPI Row */}
        <div className="kpi-grid">
          <KpiCard
            label="Historical District-Year Records"
            value={totalRecords.toLocaleString('en-US')}
            icon={<BarChart3 size={16} strokeWidth={2} />}
          />
          <KpiCard
            label="State–District Units"
            value={overviewData.state_district_units.toLocaleString('en-US')}
            icon={<MapPin size={16} strokeWidth={2} />}
          />
          <KpiCard
            label="High Risk Units (Latest)"
            value={(planningData?.latest_priority_distribution?.['High Priority'] ?? 0).toLocaleString('en-US')}
            change={((planningData?.latest_priority_distribution?.['High Priority'] ?? 0) / overviewData.state_district_units * 100).toFixed(1) + '% of units'}
            changeType="neutral"
            icon={<AlertTriangle size={16} strokeWidth={2} />}
          />
          <KpiCard
            label="States Covered"
            value={overviewData.state_count.toLocaleString('en-US')}
            icon={<TrendingUp size={16} strokeWidth={2} />}
          />
        </div>

        {/* Map + Attention Table row */}
        <div className="grid-2">
          <div className="card elevated">
            <div className="card-header">
              <div>
                <h2 className="card-title">District Risk Map</h2>
                <p className="note text-small mb-0">
                  Latest historical MRCDSS risk classification per State–District unit.
                </p>
              </div>
              <span className="badge badge-outline">
                {mapRecords.length.toLocaleString()} units
              </span>
            </div>
            <div className="card-body" style={{ paddingTop: 0, minHeight: 520 }}>
              {mapError && (
                <div className="callout warn" style={{ marginBottom: 0 }}>
                  <span className="callout-icon">
                    <AlertTriangle size={16} strokeWidth={2} />
                  </span>
                  <div className="callout-body">
                    <p className="callout-text" style={{ margin: 0 }}>
                      District boundaries temporarily unavailable: {mapError}
                    </p>
                  </div>
                </div>
              )}
              {mapRecords.length === 0 && !mapError ? (
                <div className="empty-state" style={{ padding: 'var(--space-6) var(--space-4)' }}>
                  <span className="icon" aria-hidden="true">
                    <MapPin size={32} strokeWidth={2} />
                  </span>
                  <h2>Loading district boundaries…</h2>
                </div>
              ) : (
                <DistrictRiskMap
                  records={mapRecords}
                  selectedKey={selectedKey}
                  onDistrictSelect={setSelectedDistrict}
                  onNoDataSelect={() => setSelectedDistrict(null)}
                />
              )}
            </div>
          </div>

          <div className="card elevated">
            <div className="card-header">
              <div>
                <h2 className="card-title">Districts Requiring Attention</h2>
                <p className="note text-small mb-0">
                  Latest historical High Priority units. Assessment year shown — not current or live status.
                </p>
              </div>
            </div>
            <div className="card-body" style={{ paddingTop: 0, minHeight: 520 }}>
              <div className="table-wrap" style={{ maxHeight: 440, overflow: 'auto' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th scope="col">District</th>
                      <th scope="col">State</th>
                      <th scope="col">Year</th>
                      <th scope="col">Risk</th>
                      <th scope="col">Priority</th>
                      <th scope="col">Planning Focus</th>
                    </tr>
                  </thead>
                  <tbody>
                    {mapRecords
                      .filter((r) => r.priority === 'High Priority')
                      .slice(0, 8)
                      .map((record, index) => (
                        <tr
                          key={`${record.state}-${record.district}-${record.year}-${index}`}
                          className="row-link"
                          onClick={() => {
                            const stateParam = encodeURIComponent(record.state);
                            const districtParam = encodeURIComponent(record.district);
                            window.location.href = `/districts/${stateParam}/${districtParam}`;
                          }}
                          tabIndex={0}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault();
                              const stateParam = encodeURIComponent(record.state);
                              const districtParam = encodeURIComponent(record.district);
                              window.location.href = `/districts/${stateParam}/${districtParam}`;
                            }
                          }}
                        >
                          <td><strong>{record.district}</strong></td>
                          <td>{record.state}</td>
                          <td>{record.year}</td>
                          <td>
                            <span
                              className={`badge ${riskColor(record.risk_class).includes('green') ? 'badge-low' : riskColor(record.risk_class).includes('#c2') ? 'badge-medium' : 'badge-high'}`}
                              style={{
                                borderColor:
                                  record.risk_class === 'High Risk'
                                    ? 'rgba(185, 69, 56, 0.18)'
                                    : record.risk_class === 'Medium Risk'
                                    ? 'rgba(194, 125, 47, 0.18)'
                                    : 'rgba(58, 130, 72, 0.18)',
                              }}
                            >
                              {record.risk_class.replace(' Risk', '')}
                            </span>
                          </td>
                          <td>
                            <span className="badge badge-high">{record.priority.replace(' Priority', '')}</span>
                          </td>
                          <td style={{ maxWidth: 200 }}>{record.planning_focus_1}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
                {highRiskCount === 0 && (
                  <div className="empty-state" style={{ padding: 'var(--space-4)' }}>
                    <p className="text-small">No High Priority units in the latest historical assessment.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Distributions */}
        <div className="grid-2">
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Risk Classification Distribution</h2>
            </div>
            <div className="card-body" style={{ paddingTop: 0 }}>
              <div className="distribution">
                <div className="distribution-title">Historical district-year records by risk class</div>
                {Object.entries(riskDist).map(([name, value]) => {
                  const share = totalRecords ? value / totalRecords : 0;
                  const key = name.replace(' Risk', '');
                  return (
                    <>
                      <div className="dist-bar">
                        <div
                          className="dist-seg"
                          style={{
                            width: `${share * 100}%`,
                            backgroundColor: riskColor(name),
                          }}
                        />
                      </div>
                      <div className="dist-legend">
                        <span className="dist-swatch" style={{ backgroundColor: riskColor(name) }} />
                        <span>{key}</span>
                        <span style={{ marginLeft: 'auto' }}>{value.toLocaleString()}</span>
                        <span className="dist-legend-share" style={{ color: 'var(--ink-3)' }}>
                          {(share * 100).toFixed(1)}%
                        </span>
                      </div>
                    </>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Planning Priority Distribution</h2>
            </div>
            <div className="card-body" style={{ paddingTop: 0 }}>
              <div className="distribution">
                <div className="distribution-title">Historical district-year records by DSS priority</div>
                {Object.entries(priorityDist).map(([name, value]) => {
                  const share = totalUnits ? value / totalUnits : 0;
                  const key = name.replace(' Priority', '');
                  const color =
                    key === 'High' ? '#b94538' : key === 'Medium' ? '#c27d2f' : '#3a8248';
                  return (
                    <>
                      <div className="dist-bar">
                        <div
                          className="dist-seg"
                          style={{ width: `${share * 100}%`, backgroundColor: color }}
                        />
                      </div>
                      <div className="dist-legend">
                        <span className="dist-swatch" style={{ backgroundColor: color }} />
                        <span>{key}</span>
                        <span style={{ marginLeft: 'auto' }}>{value.toLocaleString()}</span>
                        <span className="dist-legend-share" style={{ color: 'var(--ink-3)' }}>
                          {(share * 100).toFixed(1)}%
                        </span>
                      </div>
                    </>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        {/* Recent HMIS evidence strip */}
        {recentOverview && recentIndicators && (
          <section className="section">
            <div className="card elevated">
              <div className="card-header">
                <div>
                  <h2 className="card-title">Recent HMIS Evidence</h2>
                  <p className="note text-small mb-0">
                    Dataset 3 (2020–2025) — contextual indicator evidence only; not used to retrain the
                    historical model and no risk class assigned.
                  </p>
                </div>
                <Link to="/recent-hmis" className="btn btn-outline btn-sm">
                  View Full Report
                </Link>
              </div>
              <div className="card-body" style={{ paddingTop: 0 }}>
                <div className="grid-4" style={{ gap: 'var(--space-3)' }}>
                  <div className="kpi-card" style={{ padding: 'var(--space-3)' }}>
                    <span className="kpi-label">Observations</span>
                    <span className="kpi-value" style={{ fontSize: '1.5rem' }}>
                      {recentOverview.total_observations.toLocaleString('en-US')}
                    </span>
                  </div>
                  <div className="kpi-card" style={{ padding: 'var(--space-3)' }}>
                    <span className="kpi-label">Units</span>
                    <span className="kpi-value" style={{ fontSize: '1.5rem' }}>
                      {recentOverview.n_state_district_units.toLocaleString('en-US')}
                    </span>
                  </div>
                  <div className="kpi-card" style={{ padding: 'var(--space-3)' }}>
                    <span className="kpi-label">States</span>
                    <span className="kpi-value" style={{ fontSize: '1.5rem' }}>
                      {recentOverview.n_states.toLocaleString('en-US')}
                    </span>
                  </div>
                  <div className="kpi-card" style={{ padding: 'var(--space-3)' }}>
                    <span className="kpi-label">ANC Available / Missing</span>
                    <span className="kpi-value" style={{ fontSize: '1.3rem' }}>
                      {recentValid.toLocaleString('en-US')} / {recentMissing.toLocaleString('en-US')}
                    </span>
                  </div>
                </div>
                <div className="callout info" style={{ marginTop: 'var(--space-4)' }}>
                  <span className="callout-icon">
                    <Shield size={16} strokeWidth={2} />
                  </span>
                  <div className="callout-body">
                    <p className="callout-title" style={{ margin: 0 }}>
                      Recent HMIS is evidence, not a risk re-assessment
                    </p>
                    <p className="callout-text" style={{ margin: 0 }}>
                      Recent records were not used to retrain or externally validate the historical MRCDSS
                      model, and no High / Medium / Low risk class is assigned to them.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        <footer className="page-footer" style={{ marginTop: 'var(--space-8)' }}>
          <p className="page-footer-text">
            For data sources, preprocessing, and the analytical pipeline, see{' '}
            <Link to="/methodology">Methodology</Link>. For system purpose, intended users, and limitations,
            see <Link to="/about">About</Link>. Browse every district in the{' '}
            <Link to="/districts">District Explorer</Link>.
          </p>
        </footer>
      </div>
    </AppLayout>
  );
}

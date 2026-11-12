import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import AppLayout from '../components/AppLayout';
import TopBar from '../components/TopBar';
import SectionBlock from '../components/SectionBlock';
import FeatureBarChart from '../components/charts/FeatureBarChart';
import DistrictRiskMap, { NO_DATA_FILL, type DistrictMapRecord } from '../components/DistrictRiskMap';
import DistrictInfoPanel from '../components/DistrictInfoPanel';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import { getOverview } from '../api/overview';
import { getPlanningPriorities } from '../api/planning';
import { getDistricts, getLatestDistrictObservations, type LatestDistrictRecord } from '../api/districts';
import {
  getRecentHmisOverview,
  getRecentHmisIndicators,
  getRecentHmisDistrictsLatest,
  type RecentHmisOverviewData,
  type RecentHmisIndicatorsData,
  type RecentHmisLatestRecord,
} from '../api/recentHmis';
import KpiCard from '../components/KpiCard';
import MetricTable from '../components/MetricTable';
import { ASSISTANT_DISTRICT_EVENT } from '../components/Assistant';
import type { DistrictRecord } from '../types';

function formatFeatureName(feature: string): string {
  return feature.replace(/_Pct/g, '%').replace(/_/g, ' ');
}

const RISK_COLORS: Record<string, string> = {
  Low: '#2e7d32',
  Medium: '#f9a825',
  High: '#c62828',
};

interface DistributionSegment {
  label: string;
  value: number;
  share: number;
  color: string;
}

function toDistributionSegments(
  data: Record<string, number>,
  colors: Record<string, string> = RISK_COLORS,
): DistributionSegment[] {
  const entries = Object.entries(data);
  const total = entries.reduce((sum, [, value]) => sum + value, 0) || 1;
  return entries.map(([key, value]) => {
    const label = key.replace(' Risk', '').replace(' Priority', '');
    return { label, value, share: value / total, color: colors[label] ?? '#8d99a6' };
  });
}

function DistributionBar({ title, data }: { title: string; data: DistributionSegment[] }) {
  return (
    <section className="distribution-block">
      <h3 className="distribution-title">{title}</h3>
      <div
        className="dist-bar"
        role="img"
        aria-label={`${title}: ${data.map((d) => `${d.label} ${(d.share * 100).toFixed(1)}%`).join(', ')}`}
      >
        {data.map((d) => (
          <div
            key={d.label}
            className="dist-seg"
            style={{ width: `${d.share * 100}%`, backgroundColor: d.color }}
            title={`${d.label}: ${d.value.toLocaleString()} (${(d.share * 100).toFixed(1)}%)`}
          />
        ))}
      </div>
      <div className="dist-legend">
        {data.map((d) => (
          <div key={d.label} className="dist-legend-item">
            <span className="dist-swatch" style={{ backgroundColor: d.color }} aria-hidden="true" />
            <span className="dist-legend-label">{d.label}</span>
            <span className="dist-legend-value">{d.value.toLocaleString()}</span>
            <span className="dist-legend-share">{(d.share * 100).toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </section>
  );
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
    priority_distribution: Record<string, number>;
    persistent_priority_info: { total_districts: number; persistent_high: number; persistent_medium: number; persistent_low: number };
    planning_rules: Array<{ feature: string; planning_focus: string; feature_direction: string }>;
    feature_planning_focus_counts: Array<{ feature: string; count: number }>;
  } | null>(null);
  const [attentionDistricts, setAttentionDistricts] = useState<DistrictRecord[]>([]);
  const [mapRecords, setMapRecords] = useState<LatestDistrictRecord[]>([]);
  const [recentMapRecords, setRecentMapRecords] = useState<RecentHmisLatestRecord[]>([]);
  const [mapError, setMapError] = useState<string | null>(null);
  const [selectedDistrict, setSelectedDistrict] = useState<DistrictMapRecord | null>(null);
  const [recentOverview, setRecentOverview] = useState<RecentHmisOverviewData | null>(null);
  const [recentIndicators, setRecentIndicators] = useState<RecentHmisIndicatorsData | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    setMapError(null);
    try {
      const [overview, planning, districts, latest, recentOverviewData, recentIndicatorsData, recentLatest] = await Promise.all([
        getOverview(),
        getPlanningPriorities(),
        getDistricts({ priority: 'High', page: 1, per_page: 8 }),
        getLatestDistrictObservations().catch((err) => {
          setMapError(err instanceof Error ? err.message : 'Unable to load district boundaries.');
          return { count: 0, records: [], total: 0 };
        }),
        getRecentHmisOverview().catch(() => null),
        getRecentHmisIndicators().catch(() => null),
        getRecentHmisDistrictsLatest().catch(() => ({ count: 0, records: [] })),
      ]);
      setOverviewData(overview);
      setPlanningData(planning);
      setAttentionDistricts(districts.records.map((r) => ({
        state: r.state,
        district: r.district,
        year: r.year,
        riskClass: r.risk_class.replace(' Risk', '') as DistrictRecord['riskClass'],
        priority: r.priority.replace(' Priority', '') as DistrictRecord['priority'],
        topPlanningFocus: r.top_planning_focus,
      })));
      setMapRecords(latest.records);
      setRecentMapRecords(recentLatest.records);
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
        detail: selectedDistrict ? { state: selectedDistrict.state, district: selectedDistrict.district } : null,
      }),
    );
  }, [selectedDistrict]);

  const selectedKey = selectedDistrict ? `${selectedDistrict.state}||${selectedDistrict.district}` : null;
  const selectedRecent =
    selectedDistrict && recentMapRecords.length > 0
      ? (recentMapRecords.find((r) => r.state === selectedDistrict.state && r.district === selectedDistrict.district) ?? null)
      : null;

  if (loading) {
    return (
      <AppLayout>
        <main className="content"><LoadingState /></main>
      </AppLayout>
    );
  }

  if (error || !overviewData || !planningData) {
    return (
      <AppLayout>
        <main className="content"><ErrorState message={error ?? 'No data available.'} onRetry={fetchData} /></main>
      </AppLayout>
    );
  }

  const featureChartData = overviewData.feature_ranking.map((f) => ({
    name: formatFeatureName(f.feature),
    value: f.mean_abs_shap,
  }));

  const focusToFeature: Record<string, string> = {};
  planningData.planning_rules.forEach((rule) => {
    focusToFeature[rule.planning_focus] = rule.feature;
  });

  const RECENT_STATUS: Record<string, string> = {
    ANC_First_Trimester_Pct: 'Comparable',
    TT2_Booster_Pct: 'Comparable with caveat',
    Severe_Anemia_Pct: 'Definition changed',
    Obstetric_Complications_Pct: 'Schema changes after 2022-23',
  };

  const shortYears = recentOverview
    ? recentOverview.years.map((y) => `${y.slice(0, 4)}-${y.slice(-2)}`)
    : [];
  const recentPeriod =
    shortYears.length >= 2
      ? `${shortYears[0]} → ${shortYears[shortYears.length - 1]}`
      : '';
  const recentPartialMatch =
    recentOverview?.notes?.partial_2024_2025?.match(/(\d+)\s+states with complete UpTo_Mar/i);
  const recentPartialStates = recentPartialMatch ? recentPartialMatch[1] : null;

  const recentMetricRows = recentIndicators
    ? recentIndicators.indicators.map((ind) => [
        ind.name,
        ind.valid.toLocaleString('en-US'),
        ind.missing.toLocaleString('en-US'),
        RECENT_STATUS[ind.key] ?? ind.status,
      ] as (string | number)[])
    : [];

  return (
    <AppLayout>
      <main className="content">
        <TopBar
          title="District-Level Maternal Health Risk Decision Support System"
          subtitle="Analyze district-level maternal-health patterns to identify planning priorities and support public-health resource planning."
        />

        <section className="map-block">
          <div className="map-block-header">
            <div className="map-block-heading">
              <h2 className="map-block-title">District Health Intelligence</h2>
              <p className="map-block-subtitle">
                MRCDSS combines historical district-level risk classification with newer HMIS evidence to support
                district health planning. The map shows the validated MRCDSS district risk classification; selecting
                a district adds recent HMIS evidence as current context alongside its historical assessment.
              </p>
            </div>
          </div>
          <div className="map-key" aria-label="Map legend">
            <span className="map-key-item"><span className="map-key-swatch" style={{ backgroundColor: '#c62828' }} />High</span>
            <span className="map-key-item"><span className="map-key-swatch" style={{ backgroundColor: '#f9a825' }} />Medium</span>
            <span className="map-key-item"><span className="map-key-swatch" style={{ backgroundColor: '#2e7d32' }} />Low</span>
            <span className="map-key-item"><span className="map-key-swatch" style={{ backgroundColor: NO_DATA_FILL }} />No Data</span>
          </div>
          {mapError && <p className="map-coverage-note">District boundaries are temporarily unavailable: {mapError}</p>}
          <div className="map-layout">
            {mapRecords.length === 0 && !mapError ? (
              <div className="map-empty">Loading district boundaries…</div>
            ) : (
              <DistrictRiskMap
                records={mapRecords}
                selectedKey={selectedKey}
                onDistrictSelect={setSelectedDistrict}
                onNoDataSelect={() => setSelectedDistrict(null)}
              />
            )}
            <DistrictInfoPanel
              record={selectedDistrict}
              recent={selectedRecent}
              loading={false}
              onClear={() => setSelectedDistrict(null)}
            />
          </div>
        </section>

        <SectionBlock title="What Is the Priority?">
          <div className="distribution-grid">
            <DistributionBar
              title="Risk Classification"
              data={toDistributionSegments(overviewData.risk_distribution)}
            />
            <DistributionBar
              title="Planning Priority"
              data={toDistributionSegments(overviewData.priority_distribution)}
            />
          </div>
        </SectionBlock>

        <SectionBlock title="Where Is Attention Needed?">
          <p className="section-note">Districts currently flagged at the highest planning priority.</p>
          <div className="table-container">
            <table className="district-table">
              <thead>
                <tr>
                  <th scope="col">District</th>
                  <th scope="col">State</th>
                  <th scope="col">Latest Year</th>
                  <th scope="col">Risk</th>
                  <th scope="col">Priority</th>
                  <th scope="col">Key Contributing Indicator</th>
                  <th scope="col">Planning Focus</th>
                </tr>
              </thead>
              <tbody>
                {attentionDistricts.map((record, index) => {
                  const contributingIndicator = focusToFeature[record.topPlanningFocus]
                    ? formatFeatureName(focusToFeature[record.topPlanningFocus])
                    : '—';
                  return (
                    <tr key={`${record.state}-${record.district}-${record.year}-${index}`} className="district-row" onClick={() => {
                      const stateParam = encodeURIComponent(record.state);
                      const districtParam = encodeURIComponent(record.district);
                      window.location.href = `/districts/${stateParam}/${districtParam}`;
                    }} tabIndex={0} onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        const stateParam = encodeURIComponent(record.state);
                        const districtParam = encodeURIComponent(record.district);
                        window.location.href = `/districts/${stateParam}/${districtParam}`;
                      }
                    }}>
                      <td><strong>{record.district}</strong></td>
                      <td>{record.state}</td>
                      <td>{record.year}</td>
                      <td><span className={`priority-badge badge-${record.riskClass.toLowerCase()}`}>{record.riskClass}</span></td>
                      <td><span className={`priority-badge badge-${record.priority.toLowerCase()}`}>{record.priority}</span></td>
                      <td>{contributingIndicator}</td>
                      <td>{record.topPlanningFocus}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </SectionBlock>

        <SectionBlock title="What Is Driving the Assessment?">
          <p className="section-note">
            Mean absolute SHAP values from the Logistic Regression model, indicating each indicator's relative
            contribution to risk classification (contribution, not causation).
          </p>
          <FeatureBarChart data={featureChartData} />
        </SectionBlock>

        <SectionBlock title="What Should Planners Focus On?">
          <p className="section-note">
            Indicators mapped to planning focus areas based on whether higher values are protective or risk-increasing.
          </p>
          <div className="focus-list">
            {planningData.planning_rules.map((rule) => (
              <div key={rule.feature} className="focus-item">
                <span className="focus-feature">{formatFeatureName(rule.feature)}</span>
                <span className={`direction-badge ${rule.feature_direction.includes('risk') ? 'direction-risk' : 'direction-protective'}`}>
                  {rule.feature_direction}
                </span>
                <span className="focus-text">{rule.planning_focus}</span>
              </div>
            ))}
          </div>
        </SectionBlock>

        {recentOverview && recentIndicators && (
          <SectionBlock title="Recent HMIS Evidence">
            <p className="section-note">
              These indicators are part of the same MRCDSS system and appear as additional current evidence for
              districts selected on the map above. They are reported as indicators only — never assigned a risk
              classification — and describe indicator availability and reporting changes across the recent
              acquisition period.
            </p>
            <div className="kpi-grid">
              <KpiCard
                label="District-Year Observations"
                value={recentOverview.total_observations.toLocaleString('en-US')}
              />
              <KpiCard
                label="States Represented"
                value={recentOverview.n_states.toLocaleString('en-US')}
              />
              <KpiCard
                label="Acquired HMIS Period"
                value={recentPeriod}
              />
              <KpiCard
                label="States with Complete UpTo_Mar Data in 2024-25"
                value={recentPartialStates ?? '—'}
              />
            </div>
            <MetricTable
              headers={['Indicator', 'Available', 'Missing', 'Status']}
              rows={recentMetricRows}
              caption="Recent HMIS indicator availability across the acquired fiscal years."
            />
            <div className="callout-box">
              <p className="body-text">
                Recent HMIS evidence extends the same MRCDSS system with current district-level indicators. It was
                not used to retrain or externally validate the existing historical MRCDSS risk model, and no risk
                class is assigned to recent records.
              </p>
              <p className="body-text">
                Changes in HMIS reporting definitions prevent direct harmonization of several historical
                indicators across the full period. Indicators were retained only where their definitions
                could be reconstructed with sufficient evidence.
              </p>
            </div>
          </SectionBlock>
        )}

        <footer className="page-footer">
          <p className="page-footer-text">
            For data sources, preprocessing, and the analytical pipeline, see <Link to="/methodology">Methodology</Link>.
            For system purpose, intended users, and limitations, see <Link to="/about">About</Link>.
            Browse every district in the <Link to="/districts">District Explorer</Link>.
          </p>
        </footer>
      </main>
    </AppLayout>
  );
}
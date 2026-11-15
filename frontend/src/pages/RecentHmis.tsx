import { useState, useEffect } from 'react';
import AppLayout from '../components/AppLayout';
import KpiCard from '../components/KpiCard';
import MetricTable from '../components/MetricTable';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import RecentHmisCoverageChart from '../components/charts/RecentHmisCoverageChart';
import IndicatorDistributionChart from '../components/charts/IndicatorDistributionChart';
import {
  getRecentHmisOverview,
  getRecentHmisCoverage,
  getRecentHmisIndicators,
  RecentHmisOverviewData,
  RecentHmisCoverageData,
  RecentHmisIndicatorsData,
} from '../api/recentHmis';
import { Shield, Info } from 'lucide-react';

export default function RecentHmis() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [overview, setOverview] = useState<RecentHmisOverviewData | null>(null);
  const [coverage, setCoverage] = useState<RecentHmisCoverageData | null>(null);
  const [indicators, setIndicators] = useState<RecentHmisIndicatorsData | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function fetchData() {
      setLoading(true);
      setError(null);
      try {
        const [overviewData, coverageData, indicatorsData] = await Promise.all([
          getRecentHmisOverview(),
          getRecentHmisCoverage(),
          getRecentHmisIndicators(),
        ]);
        if (cancelled) return;
        setOverview(overviewData);
        setCoverage(coverageData);
        setIndicators(indicatorsData);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load Recent HMIS analysis.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    fetchData();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <AppLayout>
        <div className="content condensed"><LoadingState /></div>
      </AppLayout>
    );
  }

  if (error || !overview || !coverage || !indicators) {
    return (
      <AppLayout>
        <div className="content condensed">
          <ErrorState message={error ?? 'No data available.'} onRetry={() => window.location.reload()} />
        </div>
      </AppLayout>
    );
  }

  const yearsSpan = `${overview.years[0].slice(0, 4)}–${overview.years[overview.years.length - 1].slice(0, 4)}`;

  const indicatorHeaders = ['Indicator', 'Available (District-Year)', 'Missing', 'Status', 'Methodological Note'];
  const indicatorRows = indicators.indicators.map((ind) => [
    ind.name,
    ind.valid.toLocaleString('en-US'),
    ind.missing.toLocaleString('en-US'),
    ind.status,
    ind.note,
  ]);

  const qualityHeaders = ['Indicator', 'Flags', 'Missing', 'Out of Range', 'Structural / Unavailable', 'Zero Denominator', 'Max Out-of-Range'];
  const qualityRows = Object.entries(indicators.data_quality.by_feature).map(([feature, q]) => [
    feature.replace(/_Pct$/, '').replace(/_/g, ' '),
    q.flags.toLocaleString('en-US'),
    q.missing_flags.toLocaleString('en-US'),
    q.range_flags.toLocaleString('en-US'),
    q.structural_flags.toLocaleString('en-US'),
    q.zero_denominator_flags.toLocaleString('en-US'),
    q.max_out_of_range_value === null ? '—' : q.max_out_of_range_value.toFixed(4),
  ]);

  return (
    <AppLayout>
      <div className="content">
        <div className="page-header">
          <div className="page-header-main">
            <span className="page-kicker">Recent HMIS Extension</span>
            <h1 className="page-title">Recent HMIS Analysis</h1>
            <p className="page-subtitle">
              Dataset 3 (2020–2025) provides district-level indicator evidence. It was not used to retrain or
              externally validate the historical MRCDSS classifier, and no risk class is assigned to recent
              records. Values are reported as acquired — missingness and out-of-range values are disclosed,
              never clipped.
            </p>
          </div>
        </div>

        <section className="section">
          <div className="card elevated">
            <div className="card-header">
              <h2 className="card-title">Recent HMIS Data Overview</h2>
            </div>
            <div className="card-body" style={{ paddingTop: 0 }}>
              <div className="kpi-grid">
                <KpiCard
                  label="District-Year Observations"
                  value={overview.total_observations.toLocaleString('en-US')}
                  icon={<Shield size={16} strokeWidth={2} />}
                />
                <KpiCard
                  label="Distinct State–District Identifiers"
                  value={overview.n_state_district_units.toLocaleString('en-US')}
                />
                <KpiCard
                  label="States"
                  value={overview.n_states.toLocaleString('en-US')}
                />
                <KpiCard
                  label="Acquired Annual Data"
                  value={yearsSpan}
                />
              </div>
              <ul className="caveat-list" style={{ marginTop: 'var(--space-4)', listStyle: 'none', padding: 0 }}>
                <li style={{ padding: 'var(--space-1) 0', color: 'var(--ink-2)', fontSize: 'var(--fs-sm)', lineHeight: 1.6 }}>
                  <span style={{ color: 'var(--teal-deep)', fontWeight: '600', marginRight: 'var(--space-2)' }}>●</span>
                  {overview.notes.partial_2024_2025} — other states only had partial cumulative files, excluded from the annual dataset.
                </li>
                <li style={{ padding: 'var(--space-1) 0', color: 'var(--ink-2)', fontSize: 'var(--fs-sm)', lineHeight: 1.6 }}>
                  <span style={{ color: 'var(--teal-deep)', fontWeight: '600', marginRight: 'var(--space-2)' }}>●</span>
                  {overview.notes.not_included_2025_2026}.
                </li>
              </ul>
            </div>
          </div>
        </section>

        <section className="section">
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Yearly Coverage</h2>
            </div>
            <div className="card-body" style={{ paddingTop: 0 }}>
              <div style={{ minHeight: 260 }}>
                <RecentHmisCoverageChart data={coverage.years_coverage} />
              </div>
              <p className="note mt-4">
                District-year observations retained per fiscal year (3,306 total). 2024-25 is a partial year:
                complete UpTo_Mar files were available for 17 states and 168 district-year records. Values are
                shown for the year they are measured; they are not a forward-looking projection.
              </p>
            </div>
          </div>
        </section>

        <section className="section">
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Available Indicators</h2>
              <p className="note text-small mb-0">
                Non-missing indicator values within Dataset 3 (3,306 records).
              </p>
            </div>
            <div className="card-body" style={{ paddingTop: 0 }}>
              <MetricTable headers={indicatorHeaders} rows={indicatorRows} caption="Indicator availability and missingness." />
              <p className="note mt-4">
                Obstetric Complications is reported as an aggregate only through 2022-23; the newer HMIS schema
                does not provide the same aggregate, so its values are missing from 2023-24 onward.
              </p>
            </div>
          </div>
        </section>

        <section className="section">
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Recent HMIS Indicator Distributions</h2>
              <p className="note text-small mb-0">
                Value distributions pool all fiscal years in Dataset 3 and are shown per fiscal-year measurement
                only; they are not a longitudinal trend across years. Recorded values above 100% are retained as
                acquired, not clipped or silently corrected.
              </p>
            </div>
            <div className="card-body" style={{ paddingTop: 0, display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--space-4)' }}>
              <div>
                <IndicatorDistributionChart
                  title="ANC First Trimester (%)"
                  bins={indicators.distributions.ANC_First_Trimester_Pct.bins}
                  totalValues={indicators.distributions.ANC_First_Trimester_Pct.total_values}
                />
              </div>
              <div>
                <IndicatorDistributionChart
                  title="TT2 / Booster (%)"
                  bins={indicators.distributions.TT2_Booster_Pct.bins}
                  totalValues={indicators.distributions.TT2_Booster_Pct.total_values}
                />
              </div>
              <div>
                <IndicatorDistributionChart
                  title="Severe Anemia (%)"
                  bins={indicators.distributions.Severe_Anemia_Pct.bins}
                  totalValues={indicators.distributions.Severe_Anemia_Pct.total_values}
                />
              </div>
            </div>
          </div>
        </section>

        <section className="section">
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Data Quality Flags</h2>
              <p className="note text-small mb-0">
                {indicators.data_quality.total_flags.toLocaleString('en-US')} flagged cells in Dataset 3.
                Out-of-range percentages are a data-quality issue, not evidence that the values are valid.
              </p>
            </div>
            <div className="card-body" style={{ paddingTop: 0 }}>
              <MetricTable headers={qualityHeaders} rows={qualityRows} caption="Flagged cells by indicator." />
              <p className="note mt-4">
                {indicators.data_quality.note} Missing flags can reflect unavailable numerators or denominators;
                structural flags are concentrated in Obstetric Complications after the 2023-24 schema change.
              </p>
            </div>
          </div>
        </section>

        <section className="section">
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">District Coverage</h2>
            </div>
            <div className="card-body" style={{ paddingTop: 0 }}>
              <div className="callout info" style={{ marginBottom: 'var(--space-4)' }}>
                <span className="callout-icon">
                  <Info size={16} strokeWidth={2} />
                </span>
                <div className="callout-body">
                  <p className="callout-title" style={{ margin: 0 }}>
                    The original MRCDSS reference contains {coverage.district_coverage.reference_707_units} State–District units.
                  </p>
                  <p className="callout-text" style={{ margin: 'var(--space-1) 0 0' }}>
                    Dataset 3 contains {coverage.district_coverage.dataset_3_distinct_identifiers} distinct State–District
                    identifiers across the acquired years. The difference of{' '}
                    {coverage.district_coverage.difference.toLocaleString('en-US')} is primarily associated with
                    district reorganization, aliases, formatting variants, and HMIS's retrospective listing of
                    newly created districts.
                  </p>
                </div>
              </div>
              <div className="candidate-type-grid">
                {coverage.district_coverage.by_candidate_type.map((entry) => (
                  <div key={entry.type} className="candidate-type-card">
                    <span className="candidate-type-label">{entry.type}</span>
                    <span className="candidate-type-value">{entry.count.toLocaleString('en-US')}</span>
                  </div>
                ))}
              </div>
              <p className="note mt-4">
                District identifiers were retained at their native HMIS representation; no automatic district
                merging was performed.
              </p>
            </div>
          </div>
        </section>

        <section className="section">
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Data Availability</h2>
            </div>
            <div className="card-body" style={{ paddingTop: 0 }}>
              <table className="data-table" style={{ width: '100%' }}>
                <thead>
                  <tr>
                    <th scope="col">Fiscal Year</th>
                    <th scope="col">Availability</th>
                  </tr>
                </thead>
                <tbody>
                  {overview.year_availability.map((row) => (
                    <tr key={row.fiscal_year}>
                      <td>{row.fiscal_year}</td>
                      <td>{row.availability}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <section className="section">
          <div className="card callout info" style={{ padding: 'var(--space-5)' }}>
            <div className="flex-between" style={{ alignItems: 'flex-start' }}>
              <div>
                <h2 className="card-title" style={{ fontSize: 'var(--fs-lg)', marginBottom: 'var(--space-1)' }}>Methodological Note</h2>
                <p className="note text-small" style={{ margin: 0 }}>
                  Dataset 3 is a recent-HMIS analytical extension and was not used to retrain or externally
                  validate the existing MRCDSS classifier. Where the HMIS item structure changed across the
                  acquired years, the extension states which indicators are comparable and which are excluded
                  rather than artificially harmonizing them.
                </p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AppLayout>
  );
}

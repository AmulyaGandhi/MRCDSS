import { useState, useEffect } from 'react';
import AppLayout from '../components/AppLayout';
import TopBar from '../components/TopBar';
import SectionBlock from '../components/SectionBlock';
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
        <main className="content"><LoadingState /></main>
      </AppLayout>
    );
  }

  if (error || !overview || !coverage || !indicators) {
    return (
      <AppLayout>
        <main className="content"><ErrorState message={error ?? 'No data available.'} onRetry={() => window.location.reload()} /></main>
      </AppLayout>
    );
  }

  const yearsSpan = overview.years.length > 1
    ? `${overview.years[0].replace(/-/, '-').slice(0, 4)}-${overview.years[overview.years.length - 1].replace(/-/, '-').slice(0, 4)}`
    : overview.years[0];

  const availabilityHeaders = ['Fiscal Year', 'Availability'];
  const availabilityRows = overview.year_availability.map((row) => [row.fiscal_year, row.availability]);

  const indicatorHeaders = ['Indicator', 'Available (District-Year)', 'Missing', 'Status', 'Methodological Note'];
  const indicatorRows = indicators.indicators.map((ind) => [
    ind.name,
    ind.valid.toLocaleString('en-US'),
    ind.missing.toLocaleString('en-US'),
    ind.status,
    ind.note,
  ]);

  const harmonizationHeaders = ['Indicator', 'Harmonization Status', 'Reason'];
  const harmonizationRows = indicators.harmonization.map((row) => [row.indicator, row.status, row.reason]);

  return (
    <AppLayout>
      <main className="content">
        <TopBar
          title="Recent HMIS Analysis"
          subtitle="Recent district-level HMIS data and indicator availability"
        />

        <SectionBlock title="Recent HMIS Data Overview">
          <div className="kpi-grid">
            <KpiCard
              label="District-Year Observations"
              value={overview.total_observations.toLocaleString('en-US')}
            />
            <KpiCard
              label="Distinct State-District Identifiers"
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
          <ul className="caveat-list">
            <li>{overview.notes.partial_2024_2025} — other states only had partial cumulative files, excluded from the annual dataset.</li>
            <li>{overview.notes.not_included_2025_2026}.</li>
          </ul>
        </SectionBlock>

        <SectionBlock title="Yearly Coverage">
          <RecentHmisCoverageChart data={coverage.years_coverage} />
          <p className="section-note">
            District-year observations retained per fiscal year (3,306 total). 2024-25 is a partial
            year: complete UpTo_Mar files were available for 17 states and 168 district-year records.
            Values are shown for the year they are measured; they are not a forward-looking projection.
          </p>
        </SectionBlock>

        <SectionBlock title="Available Indicators">
          <MetricTable headers={indicatorHeaders} rows={indicatorRows} caption="Non-missing indicator values within Dataset 3 (3,306 records)." />
          <p className="section-note">
            Obstetric Complications is reported as an aggregate only through 2022-23; the newer HMIS
            schema does not provide the same aggregate, so its values are missing from 2023-24 onward.
          </p>
        </SectionBlock>

        <SectionBlock title="Recent HMIS Indicator Distributions">
          <div className="distribution-grid">
            <IndicatorDistributionChart
              title="ANC First Trimester (%)"
              bins={indicators.distributions.ANC_First_Trimester_Pct.bins}
              totalValues={indicators.distributions.ANC_First_Trimester_Pct.total_values}
            />
            <IndicatorDistributionChart
              title="TT2 / Booster (%)"
              bins={indicators.distributions.TT2_Booster_Pct.bins}
              totalValues={indicators.distributions.TT2_Booster_Pct.total_values}
            />
            <IndicatorDistributionChart
              title="Severe Anemia (%)"
              bins={indicators.distributions.Severe_Anemia_Pct.bins}
              totalValues={indicators.distributions.Severe_Anemia_Pct.total_values}
            />
          </div>
          <p className="section-note">
            Value distributions pool all fiscal years in Dataset 3 and are shown per fiscal-year
            measurement only; they are not a longitudinal trend across years. TT2 / Booster values
            above 100 are legitimate reconstructed values (TT2 and booster can overlap) and are
            retained, not clipped.
          </p>
        </SectionBlock>

        <SectionBlock title="Data Harmonization Findings">
          <MetricTable headers={harmonizationHeaders} rows={harmonizationRows} caption="Cross-year comparability of indicators within the recent-HMIS extension." />
        </SectionBlock>

        <SectionBlock title="District Coverage">
          <p className="body-text">
            The original MRCDSS reference contains{' '}
            <strong>{coverage.district_coverage.reference_707_units} State-District units</strong>.
            Dataset 3 contains{' '}
            <strong>{coverage.district_coverage.dataset_3_distinct_identifiers} distinct
            State-District identifiers</strong> across the acquired years. The difference of{' '}
            {coverage.district_coverage.difference.toLocaleString('en-US')}{' '}
            is primarily associated with district reorganization, aliases, formatting variants, and
            HMIS's retrospective listing of newly created districts.
          </p>
          <div className="candidate-type-grid">
            {coverage.district_coverage.by_candidate_type.map((entry) => (
              <div key={entry.type} className="candidate-type-card">
                <span className="candidate-type-label">{entry.type}</span>
                <span className="candidate-type-value">{entry.count.toLocaleString('en-US')}</span>
              </div>
            ))}
          </div>
          <p className="section-note">
            District identifiers were retained at their native HMIS representation; no automatic
            district merging was performed.
          </p>
        </SectionBlock>

        <SectionBlock title="Data Availability">
          <MetricTable headers={availabilityHeaders} rows={availabilityRows} caption="Fiscal-year file availability underlying Dataset 3." />
        </SectionBlock>

        <SectionBlock title="Methodological Note">
          <div className="callout-box">
            <p className="body-text">
              Dataset 3 is a recent-HMIS analytical extension and was not used to retrain or
              externally validate the existing MRCDSS classifier. Where the HMIS item structure
              changed across the acquired years, the extension states which indicators are
              comparable and which are excluded rather than artificially harmonizing them.
            </p>
          </div>
        </SectionBlock>
      </main>
    </AppLayout>
  );
}
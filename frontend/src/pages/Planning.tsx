import { useState, useEffect, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import AppLayout from '../components/AppLayout';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import { getPlanningPriorities } from '../api/planning';
import { getDistricts } from '../api/districts';
import { Info } from 'lucide-react';

const PAGE_SIZE = 10;

function mapApiRecord(r: {
  state: string;
  district: string;
  year: number;
  risk_class: string;
  priority: string;
  top_planning_focus: string;
}) {
  return {
    state: r.state,
    district: r.district,
    year: r.year,
    riskClass: r.risk_class.replace(' Risk', ''),
    priority: r.priority.replace(' Priority', ''),
    topPlanningFocus: r.top_planning_focus,
  };
}

const RISK_COLOR: Record<string, string> = {
  Low: '#3a8248',
  Medium: '#c27d2f',
  High: '#b94538',
};

export default function PlanningPriorities() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<{
    priority_distribution: Record<string, number>;
    latest_priority_distribution: Record<string, number>;
    repeated_priority_info: {
      total_units: number;
      total_district_year_records: number;
      repeated_high: number;
      repeated_medium: number;
      repeated_low: number;
      insufficient_history: number;
      repeated_high_proportion: number;
      repeated_medium_proportion: number;
      repeated_low_proportion: number;
      latest_observation_year: number | null;
      rule: string;
    };
    planning_focus_label: string;
    planning_focus_note: string;
    planning_rules: Array<{ feature: string; planning_focus: string; feature_direction: string }>;
    feature_planning_focus_counts: Array<{
      feature: string;
      record_top3_appearances: number;
      record_top1_appearances: number;
      latest_units_top3: number;
      latest_units_top1: number;
    }>;
    feature_planning_focus_note: string;
  } | null>(null);
  const [districts, setDistricts] = useState<Array<{
    state: string;
    district: string;
    year: number;
    riskClass: string;
    priority: string;
    topPlanningFocus: string;
  }>>([]);
  const [priorityFilter, setPriorityFilter] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [filteredCount, setFilteredCount] = useState<number>(0);
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const planning = await getPlanningPriorities();
      setData(planning);
      await fetchDistricts({ priority: '', search: '', page: 1 });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load planning priorities.');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchDistricts = useCallback(async (params: { priority?: string; search?: string; page: number }) => {
    try {
      const queryParams: { priority?: string; district?: string; page?: number; per_page?: number } = {
        page: params.page,
        per_page: PAGE_SIZE,
      };
      if (params.priority) queryParams.priority = params.priority;
      if (params.search) queryParams.district = params.search;
      const response = await getDistricts(queryParams);
      setDistricts(response.records.map(mapApiRecord));
      setTotalPages(Math.max(Math.ceil(response.total / response.per_page), 1));
      setFilteredCount(response.total);
    } catch (err) {
      console.error('Failed to load districts:', err);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
    searchTimeoutRef.current = setTimeout(() => {
      setCurrentPage(1);
      fetchDistricts({ priority: priorityFilter, search: searchTerm, page: 1 });
    }, 300);
    return () => {
      if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
    };
  }, [searchTerm, priorityFilter, fetchDistricts]);

  const handlePageChange = useCallback((page: number) => setCurrentPage(page), []);

  const handlePriorityChange = (value: string) => {
    setPriorityFilter(value);
    setCurrentPage(1);
  };

  const handleSearchChange = (value: string) => {
    setSearchTerm(value);
  };

  if (loading) {
    return (
      <AppLayout>
        <div className="content condensed"><LoadingState /></div>
      </AppLayout>
    );
  }

  if (error || !data) {
    return (
      <AppLayout>
        <div className="content condensed">
          <ErrorState message={error ?? 'No data available.'} onRetry={fetchData} />
        </div>
      </AppLayout>
    );
  }

  const totalPriorityRecords = Object.values(data.priority_distribution).reduce((s, v) => s + v, 0);
  const latest = data.latest_priority_distribution;
  const repeated = data.repeated_priority_info;

  return (
    <AppLayout>
      <div className="content">
        <div className="page-header">
          <div className="page-header-main">
            <span className="page-kicker">Decision Support</span>
            <h1 className="page-title">Planning Priorities</h1>
            <p className="page-subtitle">
              Planning priorities come from the historical MRCDSS decision support system (2008–2019). The DSS
              maps district-year risk classifications and model-attributed contributing factors to priority
              levels using transparent rule-based logic. The figures below are historical district-year records,
              not unique districts and not the latest status of each unit. Recent HMIS evidence (2020–2025) is
              contextual only and does not generate new risk classifications or planning priorities.
            </p>
          </div>
        </div>

        <section className="section">
          <div className="card elevated">
            <div className="card-header">
              <h2 className="card-title">Priority Overview</h2>
            </div>
            <div className="card-body" style={{ paddingTop: 0 }}>
              <div className="kpi-grid">
                <div className="kpi-card" style={{ borderLeft: '4px solid var(--risk-high)' }}>
                  <span className="kpi-label">High Priority Records</span>
                  <span className="kpi-value">
                    {(data.priority_distribution['High Priority'] ?? 0).toLocaleString('en-US')}
                  </span>
                </div>
                <div className="kpi-card" style={{ borderLeft: '4px solid var(--risk-medium)' }}>
                  <span className="kpi-label">Medium Priority Records</span>
                  <span className="kpi-value">
                    {(data.priority_distribution['Medium Priority'] ?? 0).toLocaleString('en-US')}
                  </span>
                </div>
                <div className="kpi-card" style={{ borderLeft: '4px solid var(--risk-low)' }}>
                  <span className="kpi-label">Low Priority Records</span>
                  <span className="kpi-value">
                    {(data.priority_distribution['Low Priority'] ?? 0).toLocaleString('en-US')}
                  </span>
                </div>
                <div className="kpi-card">
                  <span className="kpi-label">State–District Units</span>
                  <span className="kpi-value">
                    {repeated.total_units.toLocaleString('en-US')}
                  </span>
                </div>
              </div>
              <p className="note mt-4">
                {totalPriorityRecords.toLocaleString()} historical district-year records across{' '}
                {repeated.total_units.toLocaleString()} units.{' '}
              </p>
            </div>
          </div>
        </section>

        <section className="section">
          <div className="card">
            <div className="card-header">
              <div className="flex-between">
                <div>
                  <h2 className="card-title">Latest Historical Priority ({data.repeated_priority_info.latest_observation_year ?? '—'})</h2>
                  <p className="note text-small mb-0 mt-2">
                    One latest historical record per State–District unit. This is not a current or live priority.
                  </p>
                </div>
              </div>
            </div>
            <div className="card-body" style={{ paddingTop: 0 }}>
              <div className="grid-3" style={{ gap: 'var(--space-3)' }}>
                <div className="kpi-card" style={{ padding: 'var(--space-3)', borderLeft: '4px solid var(--risk-high)' }}>
                  <span className="kpi-label">Latest High</span>
                  <span className="kpi-value" style={{ fontSize: '1.5rem' }}>
                    {(latest['High Priority'] ?? 0).toLocaleString('en-US')}
                  </span>
                </div>
                <div className="kpi-card" style={{ padding: 'var(--space-3)', borderLeft: '4px solid var(--risk-medium)' }}>
                  <span className="kpi-label">Latest Medium</span>
                  <span className="kpi-value" style={{ fontSize: '1.5rem' }}>
                    {(latest['Medium Priority'] ?? 0).toLocaleString('en-US')}
                  </span>
                </div>
                <div className="kpi-card" style={{ padding: 'var(--space-3)', borderLeft: '4px solid var(--risk-low)' }}>
                  <span className="kpi-label">Latest Low</span>
                  <span className="kpi-value" style={{ fontSize: '1.5rem' }}>
                    {(latest['Low Priority'] ?? 0).toLocaleString('en-US')}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <div className="grid-2">
          <section className="section">
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Repeated Priority Observations</h2>
                <p className="note text-small mb-0">
                  Units with at least two historical district-year records at the same priority level. This does
                  not mean consecutive years, and it is not the unit's latest priority.
                </p>
              </div>
              <div className="card-body" style={{ paddingTop: 0, display: 'flex', gap: 'var(--space-4)', flexWrap: 'wrap' }}>
                <div style={{ flex: 1, minWidth: 200 }}>
                  <div className="kpi-card" style={{ padding: 'var(--space-4)', borderLeft: '4px solid var(--risk-high)' }}>
                    <span className="kpi-label">Repeated High</span>
                    <span className="kpi-value" style={{ fontSize: '2rem' }}>
                      {repeated.repeated_high.toLocaleString('en-US')}
                    </span>
                    <span className="kpi-delta kpi-delta-neutral" style={{ fontSize: '0.8rem' }}>
                      {(repeated.repeated_high_proportion * 100).toFixed(1)}% of units
                    </span>
                  </div>
                </div>
                <div style={{ flex: 1, minWidth: 200 }}>
                  <div className="kpi-card" style={{ padding: 'var(--space-4)', borderLeft: '4px solid var(--risk-medium)' }}>
                    <span className="kpi-label">Repeated Medium</span>
                    <span className="kpi-value" style={{ fontSize: '2rem' }}>
                      {repeated.repeated_medium.toLocaleString('en-US')}
                    </span>
                    <span className="kpi-delta kpi-delta-neutral" style={{ fontSize: '0.8rem' }}>
                      {(repeated.repeated_medium_proportion * 100).toFixed(1)}% of units
                    </span>
                  </div>
                </div>
                <div style={{ flex: 1, minWidth: 200 }}>
                  <div className="kpi-card" style={{ padding: 'var(--space-4)', borderLeft: '4px solid var(--risk-low)' }}>
                    <span className="kpi-label">Repeated Low</span>
                    <span className="kpi-value" style={{ fontSize: '2rem' }}>
                      {repeated.repeated_low.toLocaleString('en-US')}
                    </span>
                    <span className="kpi-delta kpi-delta-neutral" style={{ fontSize: '0.8rem' }}>
                      {(repeated.repeated_low_proportion * 100).toFixed(1)}% of units
                    </span>
                  </div>
                </div>
              </div>
              <div className="callout info" style={{ marginTop: 'var(--space-4)' }}>
                <span className="callout-icon">
                  <Info size={16} strokeWidth={2} />
                </span>
                <div className="callout-body">
                  <p className="callout-text" style={{ margin: 0 }}>
                    Insufficient history: {repeated.insufficient_history.toLocaleString()} units.{' '}
                    {repeated.rule}
                  </p>
                </div>
              </div>
            </div>
          </section>

          <section className="section">
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Decision Rules</h2>
                <p className="note text-small mb-0">
                  Six indicators drive DSS planning priorities. Direction indicates whether higher values improve
                  or worsen the assessment.
                </p>
              </div>
              <div className="card-body" style={{ paddingTop: 0 }}>
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th scope="col">Feature</th>
                        <th scope="col">Model-Attributed Focus</th>
                        <th scope="col">Direction</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.planning_rules.map((rule) => (
                        <tr key={rule.feature}>
                          <td>
                            <span className="cell-monospace">
                              {rule.feature.replace(/_Pct/g, '%').replace(/_/g, ' ')}
                            </span>
                          </td>
                          <td>{rule.planning_focus}</td>
                          <td>
                            <span className={`badge ${rule.feature_direction.toLowerCase().includes('risk') ? 'badge-medium' : 'badge-low'}`}>
                              {rule.feature_direction}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </section>
        </div>

        <section className="section">
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Model-Attributed Contributing Indicators</h2>
              <p className="note text-small mb-0">
                {data.feature_planning_focus_note} A record can contain multiple top-three indicators; these
                counts are not unique districts. Planning focus areas are model-attributed planning priorities,
                not a verified needs assessment.
              </p>
            </div>
            <div className="card-body" style={{ paddingTop: 0 }}>
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th scope="col">Feature</th>
                      <th scope="col">Model-Attributed Focus</th>
                      <th scope="col">Record Top-3</th>
                      <th scope="col">Record Top-1</th>
                      <th scope="col">Latest Units Top-3</th>
                      <th scope="col">Latest Units Top-1</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.feature_planning_focus_counts.map((item) => {
                      const rule = data.planning_rules.find((r) => r.feature === item.feature);
                      return (
                        <tr key={item.feature}>
                          <td>
                            <span className="cell-monospace">
                              {item.feature.replace(/_Pct/g, '%').replace(/_/g, ' ')}
                            </span>
                          </td>
                          <td>{rule?.planning_focus ?? '—'}</td>
                          <td>{item.record_top3_appearances.toLocaleString()}</td>
                          <td>{item.record_top1_appearances.toLocaleString()}</td>
                          <td>{item.latest_units_top3.toLocaleString()}</td>
                          <td>{item.latest_units_top1.toLocaleString()}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <p className="note mt-4">{data.planning_focus_note}</p>
            </div>
          </div>
        </section>

        <section className="section">
          <div className="card">
            <div className="card-header">
              <div className="flex-between">
                <div>
                  <h2 className="card-title">Historical District-Year Priorities</h2>
                  <p className="note text-small mb-0 mt-2">
                    Each row is one historical district-year record, not one unique district or the unit's latest
                    status. Use the Year column to distinguish assessment periods.
                  </p>
                </div>
                <div className="filter-row" style={{ gap: 'var(--space-2)' }}>
                  <div className="filter-group" style={{ minWidth: 160 }}>
                    <label className="filter-label">Priority</label>
                    <select
                      className="filter-select"
                      value={priorityFilter}
                      onChange={(e) => handlePriorityChange(e.target.value)}
                    >
                      <option value="">All</option>
                      <option value="High">High</option>
                      <option value="Medium">Medium</option>
                      <option value="Low">Low</option>
                    </select>
                  </div>
                  <div className="filter-group" style={{ flex: 1, minWidth: 200 }}>
                    <label className="filter-label">Search Districts</label>
                    <input
                      className="filter-search"
                      type="text"
                      placeholder="Search by district name..."
                      value={searchTerm}
                      onChange={(e) => handleSearchChange(e.target.value)}
                    />
                  </div>
                  <span className="filter-result-count">
                    {filteredCount.toLocaleString()} historical records
                  </span>
                </div>
              </div>
            </div>
            <div className="card-body" style={{ paddingTop: 0 }}>
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th scope="col">District</th>
                      <th scope="col">State</th>
                      <th scope="col">Year</th>
                      <th scope="col">Risk</th>
                      <th scope="col">Priority</th>
                      <th scope="col">Contributing Indicator</th>
                      <th scope="col">Planning Focus</th>
                    </tr>
                  </thead>
                  <tbody>
                    {districts.map((record, index) => (
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
                            className={`badge ${RISK_COLOR[record.riskClass] ? 'badge-low' : 'badge-neutral'}`}
                            style={{
                              backgroundColor: `${RISK_COLOR[record.riskClass] ?? '#7a8797'}15`,
                              color: RISK_COLOR[record.riskClass] ?? '#7a8797',
                              borderColor: `${RISK_COLOR[record.riskClass] ?? '#7a8797'}30`,
                            }}
                          >
                            {record.riskClass}
                          </span>
                        </td>
                        <td>
                          <span
                            className={`badge ${record.priority === 'High' ? 'badge-high' : record.priority === 'Medium' ? 'badge-medium' : 'badge-low'}`}
                          >
                            {record.priority}
                          </span>
                        </td>
                        <td>{record.topPlanningFocus}</td>
                        <td>{record.topPlanningFocus}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {totalPages > 1 && (
                <div className="pagination-wrapper" style={{ marginTop: 'var(--space-4)' }}>
                  <button
                    type="button"
                    className="btn btn-outline btn-sm"
                    disabled={currentPage === 1}
                    onClick={() => handlePageChange(currentPage - 1)}
                    aria-label="Previous page"
                  >
                    Previous
                  </button>
                  <span className="filter-result-count" style={{ margin: '0 var(--space-2)' }}>
                    Page {currentPage} of {totalPages}
                  </span>
                  <button
                    type="button"
                    className="btn btn-outline btn-sm"
                    disabled={currentPage === totalPages}
                    onClick={() => handlePageChange(currentPage + 1)}
                    aria-label="Next page"
                  >
                    Next
                  </button>
                </div>
              )}
            </div>
          </div>
        </section>

        <div className="section-actions mt-6">
          <Link to="/" className="btn btn-outline">
            ← Back to Overview
          </Link>
          <Link to="/risk-analysis" className="btn btn-secondary">
            Review Risk Analysis
          </Link>
        </div>
      </div>
    </AppLayout>
  );
}

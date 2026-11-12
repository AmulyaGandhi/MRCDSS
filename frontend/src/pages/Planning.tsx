import { useState, useEffect, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import AppLayout from '../components/AppLayout';
import TopBar from '../components/TopBar';
import SectionBlock from '../components/SectionBlock';
import MetricTable from '../components/MetricTable';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import { getPlanningPriorities } from '../api/planning';
import { getDistricts } from '../api/districts';
import type { DistrictRecord } from '../types';

const PAGE_SIZE = 10;

function mapApiRecord(r: {
  state: string;
  district: string;
  year: number;
  risk_class: string;
  priority: string;
  top_planning_focus: string;
}): DistrictRecord {
  return {
    state: r.state,
    district: r.district,
    year: r.year,
    riskClass: r.risk_class.replace(' Risk', '') as DistrictRecord['riskClass'],
    priority: r.priority.replace(' Priority', '') as DistrictRecord['priority'],
    topPlanningFocus: r.top_planning_focus,
  };
}

export default function PlanningPriorities() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<{
    priority_distribution: Record<string, number>;
    persistent_priority_info: { total_districts: number; persistent_high: number; persistent_medium: number; persistent_low: number };
    planning_rules: Array<{ feature: string; planning_focus: string; feature_direction: string }>;
    feature_planning_focus_counts: Array<{ feature: string; count: number }>;
  } | null>(null);
  const [districts, setDistricts] = useState<DistrictRecord[]>([]);
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

  const priorityBadgeClass: Record<string, string> = {
    'High Priority': 'badge-high',
    'Medium Priority': 'badge-medium',
    'Low Priority': 'badge-low',
  };

  const focusToFeature: Record<string, string> = {};
  if (data) {
    data.planning_rules.forEach((rule) => {
      focusToFeature[rule.planning_focus] = rule.feature;
    });
  }

  if (loading) {
    return (
      <AppLayout>
        <main className="content"><LoadingState /></main>
      </AppLayout>
    );
  }

  if (error || !data) {
    return (
      <AppLayout>
        <main className="content"><ErrorState message={error ?? 'No data available.'} onRetry={fetchData} /></main>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <main className="content">
        <TopBar
          title="Planning Priorities"
          subtitle="Use analytical risk profiles and contributing indicators to identify districts requiring greater planning attention."
        />

        <section className="purpose-section">
          <h2 className="purpose-title">Priority Overview</h2>
          <p className="purpose-text">
            Current planning priorities are derived from the validated MRCDSS decision support system
            (historical MRCDSS data, 2008–2019). The DSS maps district-year risk classifications and
            contributing factors to priority levels using transparent rule-based logic. Persistent priority
            reflects consistent priority status across assessment periods. Recent HMIS evidence (2020–2025)
            is included as additional current context for the same districts and does not generate new risk
            classifications or planning priorities.
          </p>
          <div className="priority-summary-grid">
            <div className="priority-summary-item priority-summary-high">
              <span className="priority-summary-value">{data.priority_distribution['High Priority']?.toLocaleString() ?? 0}</span>
              <span className="priority-summary-label">High Priority</span>
            </div>
            <div className="priority-summary-item priority-summary-medium">
              <span className="priority-summary-value">{data.priority_distribution['Medium Priority']?.toLocaleString() ?? 0}</span>
              <span className="priority-summary-label">Medium Priority</span>
            </div>
            <div className="priority-summary-item priority-summary-low">
              <span className="priority-summary-value">{data.priority_distribution['Low Priority']?.toLocaleString() ?? 0}</span>
              <span className="priority-summary-label">Low Priority</span>
            </div>
            <div className="priority-summary-item">
              <span className="priority-summary-value">{data.persistent_priority_info.total_districts.toLocaleString()}</span>
              <span className="priority-summary-label">State–District Units</span>
            </div>
          </div>
        </section>

        <div className="dashboard-grid">
          <SectionBlock title="Persistent Priority">
            <p className="section-note">Districts maintaining priority status across multiple assessment periods.</p>
            <div className="priority-compact-grid">
              <div className={`priority-compact-item priority-compact-high`}>
                <span className="priority-compact-value">{data.persistent_priority_info.persistent_high.toLocaleString()}</span>
                <span className="priority-compact-label">Persistent High</span>
                <span className="priority-compact-percent">{((data.persistent_priority_info.persistent_high / data.persistent_priority_info.total_districts) * 100).toFixed(0)}%</span>
              </div>
              <div className={`priority-compact-item priority-compact-medium`}>
                <span className="priority-compact-value">{data.persistent_priority_info.persistent_medium.toLocaleString()}</span>
                <span className="priority-compact-label">Persistent Medium</span>
                <span className="priority-compact-percent">{((data.persistent_priority_info.persistent_medium / data.persistent_priority_info.total_districts) * 100).toFixed(0)}%</span>
              </div>
              <div className={`priority-compact-item priority-compact-low`}>
                <span className="priority-compact-value">{data.persistent_priority_info.persistent_low.toLocaleString()}</span>
                <span className="priority-compact-label">Persistent Low</span>
                <span className="priority-compact-percent">{((data.persistent_priority_info.persistent_low / data.persistent_priority_info.total_districts) * 100).toFixed(0)}%</span>
              </div>
            </div>
          </SectionBlock>
          <SectionBlock title="Decision Rules">
            <p className="section-note">Six indicators drive DSS planning priorities. Direction indicates whether higher values improve or worsen the assessment.</p>
            <MetricTable
              headers={['Feature', 'Planning Focus', 'Direction']}
              rows={data.planning_rules.map((rule) => [
                rule.feature.replace(/_Pct/g, '%').replace(/_/g, ' '),
                rule.planning_focus,
                rule.feature_direction,
              ])}
            />
          </SectionBlock>
        </div>

        <SectionBlock title="Contributing Indicators">
          <p className="section-note">Number of districts where each indicator contributes to the planning focus, ranked by influence.</p>
          <div className="table-container">
            <table className="district-table">
              <thead>
                <tr>
                  <th scope="col">Feature</th>
                  <th scope="col">Planning Focus</th>
                  <th scope="col">Districts Affected</th>
                </tr>
              </thead>
              <tbody>
                {data.feature_planning_focus_counts.map((item) => {
                  const rule = data.planning_rules.find((r) => r.feature === item.feature);
                  return (
                    <tr key={item.feature}>
                      <td>{item.feature.replace(/_Pct/g, '%').replace(/_/g, ' ')}</td>
                      <td>{rule?.planning_focus ?? '—'}</td>
                      <td>{item.count.toLocaleString()}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </SectionBlock>

        <SectionBlock title="District Priorities">
          <div className="filter-bar compact">
            <div className="filter-row">
              <div className="filter-group">
                <label htmlFor="planning-priority" className="filter-label">Priority</label>
                <select
                  id="planning-priority"
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
              <div className="filter-group">
                <label htmlFor="planning-search" className="filter-label">Search Districts</label>
                <input
                  id="planning-search"
                  type="text"
                  className="filter-search"
                  placeholder="Search by district name..."
                  value={searchTerm}
                  onChange={(e) => handleSearchChange(e.target.value)}
                />
              </div>
              <div className="filter-group filter-actions">
                <span className="filter-result-count">{filteredCount.toLocaleString()} districts</span>
              </div>
            </div>
          </div>
          <div className="table-container">
            <table className="district-table">
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
                {districts.map((record, index) => {
                  const contributingIndicator = focusToFeature[record.topPlanningFocus]
                    ? record.topPlanningFocus.replace(/_Pct/g, '%').replace(/_/g, ' ')
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
                      <td><span className={`priority-badge ${priorityBadgeClass[record.priority] ?? 'badge-low'}`}>{record.priority}</span></td>
                      <td>{contributingIndicator}</td>
                      <td>{record.topPlanningFocus}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {totalPages > 1 && (
            <div className="pagination-wrapper">
              <button type="button" className="pagination-button" disabled={currentPage === 1} onClick={() => handlePageChange(currentPage - 1)} aria-label="Previous page">Previous</button>
              <span className="pagination-info" aria-live="polite">Page {currentPage} of {totalPages}</span>
              <button type="button" className="pagination-button" disabled={currentPage === totalPages} onClick={() => handlePageChange(currentPage + 1)} aria-label="Next page">Next</button>
            </div>
          )}
        </SectionBlock>

        <div className="section-actions">
          <Link className="action-button-inline" to="/">Back to Overview</Link>
          <Link className="action-button-inline" to="/risk-analysis">Review Risk Analysis</Link>
        </div>
      </main>
    </AppLayout>
  );
}

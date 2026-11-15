import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import AppLayout from '../components/AppLayout';
import TopBar from '../components/TopBar';
import SectionBlock from '../components/SectionBlock';
import FilterBar from '../components/FilterBar';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import { getDistricts, getStates, getYears } from '../api/districts';
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

const RISK_BADGE: Record<string, { bg: string; color: string; border: string }> = {
  Low: { bg: '#e9f3ea', color: '#3a8248', border: 'rgba(58, 130, 72, 0.18)' },
  Medium: { bg: '#fdf3e3', color: '#c27d2f', border: 'rgba(194, 125, 47, 0.18)' },
  High: { bg: '#fbecea', color: '#b94538', border: 'rgba(185, 69, 56, 0.18)' },
};

export default function DistrictExplorer() {
  const navigate = useNavigate();
  const [stateFilter, setStateFilter] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [riskFilter, setRiskFilter] = useState<string>('');
  const [priorityFilter, setPriorityFilter] = useState<string>('');
  const [yearFilter, setYearFilter] = useState<number | ''>('');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [records, setRecords] = useState<DistrictRecord[]>([]);
  const [states, setStates] = useState<string[]>([]);
  const [years, setYears] = useState<number[]>([]);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [totalRecords, setTotalRecords] = useState<number>(0);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchFilters = useCallback(async () => {
    try {
      const [statesRes, yearsRes] = await Promise.all([getStates(), getYears()]);
      setStates(statesRes.states);
      setYears(yearsRes.years);
    } catch (err) {
      console.error('Failed to load filter options:', err);
    }
  }, []);

  const fetchRecords = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: {
        state?: string;
        district?: string;
        risk_class?: string;
        priority?: string;
        year?: number;
        page?: number;
        per_page?: number;
      } = { page: currentPage, per_page: PAGE_SIZE };
      if (stateFilter) params.state = stateFilter;
      if (searchTerm) params.district = searchTerm;
      if (riskFilter) params.risk_class = riskFilter;
      if (priorityFilter) params.priority = priorityFilter;
      if (yearFilter !== '') params.year = yearFilter;

      const response = await getDistricts(params);
      setRecords(response.records.map(mapApiRecord));
      setTotalPages(Math.max(Math.ceil(response.total / response.per_page), 1));
      setTotalRecords(response.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load district records.');
    } finally {
      setLoading(false);
      setInitialLoading(false);
    }
  }, [stateFilter, searchTerm, riskFilter, priorityFilter, yearFilter, currentPage]);

  useEffect(() => {
    fetchFilters();
    fetchRecords();
  }, [fetchFilters, fetchRecords]);

  useEffect(() => {
    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
    searchTimeoutRef.current = setTimeout(() => {
      setCurrentPage(1);
      fetchRecords();
    }, 300);
    return () => {
      if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
    };
  }, [searchTerm, fetchRecords]);

  const handleClear = useCallback(() => {
    setStateFilter('');
    setSearchTerm('');
    setRiskFilter('');
    setPriorityFilter('');
    setYearFilter('');
    setCurrentPage(1);
  }, []);

  const handlePageChange = useCallback((page: number) => setCurrentPage(page), []);

  const handleRowClick = useCallback((record: DistrictRecord) => {
    const stateParam = encodeURIComponent(record.state);
    const districtParam = encodeURIComponent(record.district);
    navigate(`/districts/${stateParam}/${districtParam}`);
  }, [navigate]);

  if (initialLoading && !error) {
    return (
      <AppLayout>
        <div className="content condensed">
          <TopBar title="District Explorer" subtitle="Explore district-level maternal health risk profiles and priorities across the dataset" />
          <LoadingState />
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="content">
        <div className="page-header">
          <div className="page-header-main">
            <span className="page-kicker">District Explorer</span>
            <h1 className="page-title">District Explorer</h1>
            <p className="page-subtitle">
              Browse and investigate {totalRecords.toLocaleString()} historical MRCDSS district-year records
              spanning {states.length} states{years.length >= 2 ? ` from ${years[0]}–${years[years.length - 1]}` : ''}.
              Filter by state, district, year, risk class, or priority to identify areas requiring attention,
              then select any district to view its complete unified history — the historical MRCDSS assessment
              together with recent HMIS evidence for the same district.
            </p>
            <div className="grid-4" style={{ marginTop: 'var(--space-4)', gap: 'var(--space-3)' }}>
              <div className="kpi-card" style={{ padding: 'var(--space-4)' }}>
                <span className="kpi-label">Total Records</span>
                <span className="kpi-value" style={{ fontSize: '1.7rem' }}>{totalRecords.toLocaleString('en-US')}</span>
              </div>
              <div className="kpi-card" style={{ padding: 'var(--space-4)' }}>
                <span className="kpi-label">States</span>
                <span className="kpi-value" style={{ fontSize: '1.7rem' }}>{String(states.length)}</span>
              </div>
              <div className="kpi-card" style={{ padding: 'var(--space-4)' }}>
                <span className="kpi-label">Years</span>
                <span className="kpi-value" style={{ fontSize: '1.7rem' }}>{String(years.length)}</span>
              </div>
              <div className="kpi-card" style={{ padding: 'var(--space-4)' }}>
                <span className="kpi-label">Currently Showing</span>
                <span className="kpi-value" style={{ fontSize: '1.7rem' }}>{records.length}</span>
              </div>
            </div>
          </div>
        </div>

        <SectionBlock>
          <FilterBar
            stateFilter={stateFilter}
            setStateFilter={setStateFilter}
            searchTerm={searchTerm}
            setSearchTerm={setSearchTerm}
            riskFilter={riskFilter}
            setRiskFilter={setRiskFilter}
            priorityFilter={priorityFilter}
            setPriorityFilter={setPriorityFilter}
            yearFilter={yearFilter}
            setYearFilter={setYearFilter}
            onClear={handleClear}
            states={states}
            years={years}
            loading={loading}
          />
        </SectionBlock>

        {error && (
          <div className="mt-6"><ErrorState message={error} onRetry={fetchRecords} /></div>
        )}

        <SectionBlock className="mt-6">
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th scope="col">State</th>
                  <th scope="col">District</th>
                  <th scope="col">Year</th>
                  <th scope="col">Risk</th>
                  <th scope="col">Priority</th>
                  <th scope="col">Top Planning Focus</th>
                </tr>
              </thead>
              <tbody>
                {records.map((record, index) => {
                  const style = RISK_BADGE[record.riskClass] ?? RISK_BADGE.Low;
                  return (
                    <tr
                      key={`${record.state}-${record.district}-${record.year}-${index}`}
                      className="row-link"
                      tabIndex={0}
                      onClick={() => handleRowClick(record)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          handleRowClick(record);
                        }
                      }}
                    >
                      <td>{record.state}</td>
                      <td>{record.district}</td>
                      <td>{record.year}</td>
                      <td>
                        <span className="badge" style={{ backgroundColor: style.bg, color: style.color, borderColor: style.border }}>
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
                    </tr>
                  );
                })}
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
        </SectionBlock>
      </div>
    </AppLayout>
  );
}

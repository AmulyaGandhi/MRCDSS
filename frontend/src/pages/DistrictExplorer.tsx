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
        <main className="content">
          <TopBar title="District Explorer" subtitle="Investigate district-level maternal health risk profiles and priorities" />
          <LoadingState />
        </main>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <main className="content">
        <TopBar title="District Explorer" subtitle="Explore district-level maternal health risk profiles and priorities across the dataset" />

        <section className="purpose-section">
          <h2 className="purpose-title">District Explorer</h2>
          <p className="purpose-text">
            Browse and investigate {totalRecords.toLocaleString()} historical MRCDSS district-year records
            spanning {states.length} states
            {years.length >= 2 ? ` from ${years[0]}–${years[years.length - 1]}` : ''}. Filter by state,
            district, year, risk class, or priority to identify areas requiring attention, then select any
            district to view its complete unified history — the historical MRCDSS assessment together with
            recent HMIS evidence for the same district.
          </p>
          <div className="purpose-facts">
            <div className="purpose-fact">
              <span className="purpose-fact-value">{totalRecords.toLocaleString()}</span>
              <span className="purpose-fact-label">Total Records</span>
            </div>
            <div className="purpose-fact">
              <span className="purpose-fact-value">{String(states.length)}</span>
              <span className="purpose-fact-label">States</span>
            </div>
            <div className="purpose-fact">
              <span className="purpose-fact-value">{String(years.length)}</span>
              <span className="purpose-fact-label">Years</span>
            </div>
            <div className="purpose-fact">
              <span className="purpose-fact-value">{records.length}</span>
              <span className="purpose-fact-label">Currently Showing</span>
            </div>
          </div>
        </section>

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

        {error && <div className="mt-16"><ErrorState message={error} onRetry={fetchRecords} /></div>}

        <SectionBlock className="mt-16">
          <div className="table-container">
            <table className="district-table">
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
                {records.map((record, index) => (
                  <tr
                    key={`${record.state}-${record.district}-${record.year}-${index}`}
                    className="district-row"
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
                      <span className={`priority-badge badge-${record.riskClass.toLowerCase()}`}>
                        {record.riskClass}
                      </span>
                    </td>
                    <td>
                      <span className={`priority-badge badge-${record.priority.toLowerCase()}`}>
                        {record.priority}
                      </span>
                    </td>
                    <td>{record.topPlanningFocus}</td>
                  </tr>
                ))}
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
      </main>
    </AppLayout>
  );
}

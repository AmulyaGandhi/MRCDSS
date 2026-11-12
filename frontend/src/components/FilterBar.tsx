interface FilterBarProps {
  stateFilter: string;
  setStateFilter: (value: string) => void;
  searchTerm: string;
  setSearchTerm: (value: string) => void;
  riskFilter: string;
  setRiskFilter: (value: string) => void;
  priorityFilter: string;
  setPriorityFilter: (value: string) => void;
  yearFilter: number | '';
  setYearFilter: (value: number | '') => void;
  onClear: () => void;
  states: string[];
  years: number[];
  loading: boolean;
}

export default function FilterBar({
  stateFilter,
  setStateFilter,
  searchTerm,
  setSearchTerm,
  riskFilter,
  setRiskFilter,
  priorityFilter,
  setPriorityFilter,
  yearFilter,
  setYearFilter,
  onClear,
  states,
  years,
  loading,
}: FilterBarProps) {
  return (
    <div className="filter-bar" role="search" aria-label="District filters">
      {loading && <p className="data-preview">Loading district data...</p>}
      <div className="filter-row">
        <div className="filter-group">
          <label htmlFor="filter-state" className="filter-label">State</label>
          <select
            id="filter-state"
            className="filter-select"
            value={stateFilter}
            onChange={(e) => setStateFilter(e.target.value)}
            aria-label="Filter by state"
            disabled={loading}
          >
            <option value="">All</option>
            {states.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
        <div className="filter-group">
          <label htmlFor="filter-district" className="filter-label">District</label>
          <input
            id="filter-district"
            type="text"
            className="filter-search"
            placeholder="Search districts..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            aria-label="Search by district name"
            disabled={loading}
          />
        </div>
        <div className="filter-group">
          <label htmlFor="filter-risk" className="filter-label">Risk Class</label>
          <select
            id="filter-risk"
            className="filter-select"
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            aria-label="Filter by risk class"
            disabled={loading}
          >
            <option value="">All</option>
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
          </select>
        </div>
        <div className="filter-group">
          <label htmlFor="filter-priority" className="filter-label">Priority</label>
          <select
            id="filter-priority"
            className="filter-select"
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            aria-label="Filter by priority"
            disabled={loading}
          >
            <option value="">All</option>
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
          </select>
        </div>
        <div className="filter-group">
          <label htmlFor="filter-year" className="filter-label">Year</label>
          <select
            id="filter-year"
            className="filter-select"
            value={yearFilter}
            onChange={(e) => setYearFilter(e.target.value === '' ? '' : Number(e.target.value))}
            aria-label="Filter by year"
            disabled={loading}
          >
            <option value="">All</option>
            {years.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>
        <div className="filter-group filter-actions">
          <button type="button" className="filter-clear" onClick={onClear} disabled={loading}>
            Clear Filters
          </button>
        </div>
      </div>
    </div>
  );
}

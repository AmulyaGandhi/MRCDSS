import type { DistrictRecord } from '../types';

interface DistrictTableProps {
  records: DistrictRecord[];
  onRowClick: (record: DistrictRecord) => void;
}

export default function DistrictTable({ records, onRowClick }: DistrictTableProps) {
  if (records.length === 0) {
    return (
      <div className="table-container">
        <p className="empty-state" role="status">No district records match the current filters. Adjust filters or clear them to see results.</p>
      </div>
    );
  }

  return (
    <div className="table-container">
      <table className="district-table">
        <thead>
          <tr>
            <th scope="col">State</th>
            <th scope="col">District</th>
            <th scope="col">Year</th>
            <th scope="col">Risk Class</th>
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
              onClick={() => onRowClick(record)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onRowClick(record);
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
  );
}

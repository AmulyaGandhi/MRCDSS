import { Link } from 'react-router-dom';
import type { LatestDistrictRecord } from '../api/districts';
import type { RecentHmisLatestRecord } from '../api/recentHmis';

export interface DistrictInfoPanelProps {
  record: LatestDistrictRecord | null;
  recent?: RecentHmisLatestRecord | null;
  loading: boolean;
  onClear: () => void;
}

function formatPct(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return '—';
  return `${value.toFixed(1)}%`;
}

function joinPresent(values: Array<string | null | undefined>): string {
  const present = values.filter((v): v is string => Boolean(v));
  return present.length > 0 ? present.join(' · ') : '—';
}

export default function DistrictInfoPanel({
  record,
  loading,
  onClear,
  recent = null,
}: DistrictInfoPanelProps) {
  if (loading) {
    return (
      <div className="district-info-panel">
        <div className="district-info-empty">Loading district…</div>
      </div>
    );
  }
  if (!record) {
    return (
      <div className="district-info-panel">
        <div className="district-info-label district-info-empty-label">District Details</div>
        <div className="district-info-empty">
          <span className="district-info-empty-title">Select a district</span>
          <span className="district-info-empty-text">
            Click a district on the map to view its unified MRCDSS profile — historical risk classification
            together with recent HMIS evidence for the same district.
          </span>
        </div>
      </div>
    );
  }

  const riskBadgeClass =
    record.risk_class === 'High Risk' ? 'badge-high' : record.risk_class === 'Medium Risk' ? 'badge-medium' : 'badge-low';
  const priorityBadgeClass =
    record.priority === 'High Priority' ? 'badge-high' : record.priority === 'Medium Priority' ? 'badge-medium' : 'badge-low';
  const stateParam = encodeURIComponent(record.state);
  const districtParam = encodeURIComponent(record.district);

  const contributors = joinPresent([
    record.top_contributing_feature_1,
    record.top_contributing_feature_2,
    record.top_contributing_feature_3,
  ]);
  const planningFocus = joinPresent([
    record.planning_focus_1,
    record.planning_focus_2,
    record.planning_focus_3,
  ]);

  return (
    <div className="district-info-panel">
      <div className="district-info-header">
        <div>
          <span className="district-info-label">District Health Profile</span>
          <span className="district-info-title">{record.district}</span>
          <span className="district-info-subtitle">{record.state}</span>
        </div>
        <button type="button" className="district-info-close" onClick={onClear} aria-label="Clear selection">
          ✕
        </button>
      </div>

      <div className="district-info-grid">
        <div className="district-info-item">
          <span className="district-info-item-label">Current MRCDSS Assessment</span>
          <span className="district-info-item-value">
            <span className={`priority-badge ${riskBadgeClass}`}>{record.risk_class}</span>{' '}
            <span className={`priority-badge ${priorityBadgeClass}`}>{record.priority}</span>
          </span>
        </div>
        <div className="district-info-item">
          <span className="district-info-item-label">Latest Assessment Year</span>
          <span className="district-info-item-value">{record.year}</span>
        </div>
      </div>

      <div className="district-info-planning">
        <span className="district-info-item-label">Key Contributing Indicators</span>
        <span className="district-info-planning-text">{contributors}</span>
      </div>

      <div className="district-info-planning">
        <span className="district-info-item-label">Planning Focus</span>
        <span className="district-info-planning-text">{planningFocus}</span>
      </div>

      <div className="district-info-recent">
        <span className="district-info-recent-label">Recent HMIS Evidence</span>
        {recent ? (
          <>
            <div className="district-info-grid">
              <div className="district-info-item">
                <span className="district-info-item-label">Latest Evidence Year</span>
                <span className="district-info-item-value">{recent.year}</span>
              </div>
              <div className="district-info-item">
                <span className="district-info-item-label">ANC First Trimester</span>
                <span className="district-info-item-value" style={{ color: '#1a5276' }}>
                  {formatPct(recent.ANC_First_Trimester_Pct)}
                </span>
              </div>
              <div className="district-info-item">
                <span className="district-info-item-label">TT2 / Booster</span>
                <span className="district-info-item-value">{formatPct(recent.TT2_Booster_Pct)}</span>
              </div>
              <div className="district-info-item">
                <span className="district-info-item-label">Severe Anemia</span>
                <span className="district-info-item-value">{formatPct(recent.Severe_Anemia_Pct)}</span>
              </div>
              <div className="district-info-item">
                <span className="district-info-item-label">Obstetric Complications</span>
                <span className="district-info-item-value">{formatPct(recent.Obstetric_Complications_Pct)}</span>
              </div>
            </div>
            <p className="district-info-recent-note">
              Recent HMIS evidence is additional current evidence for this district. It was not used to assign the
              historical MRCDSS risk class shown above.
            </p>
          </>
        ) : (
          <p className="district-info-recent-note">
            No recent HMIS evidence is currently available for this district.
          </p>
        )}
      </div>

      <div className="district-info-actions">
        <Link className="district-info-view" to={`/districts/${stateParam}/${districtParam}`}>
          View Full District Timeline →
        </Link>
      </div>
    </div>
  );
}
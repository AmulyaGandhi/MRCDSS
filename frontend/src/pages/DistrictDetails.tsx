import { useState, useEffect } from 'react';
import { useParams, useNavigate, Navigate, Link } from 'react-router-dom';
import { ArrowLeft, AlertTriangle, Target, Shield } from 'lucide-react';
import AppLayout from '../components/AppLayout';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import { getDistrictDetail, type PriorityHistory } from '../api/districtDetail';
import { getUnifiedDistrict, type UnifiedDistrictDetail } from '../api/unified';
import { type DistrictDetail } from '../types';

function formatPct(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return '—';
  return `${value.toFixed(1)}%`;
}

function riskColor(riskClass: string) {
  switch (riskClass) {
    case 'High': return '#b94538';
    case 'Medium': return '#c27d2f';
    case 'Low': return '#3a8248';
    default: return '#7a8797';
  }
}

export default function DistrictDetails() {
  const { state, district } = useParams<{ state: string; district: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<DistrictDetail | null>(null);
  const [history, setHistory] = useState<Array<{ year: number; riskClass: string; priority: string }>>([]);
  const [priorityHistory, setPriorityHistory] = useState<PriorityHistory | null>(null);
  const [unifiedDetail, setUnifiedDetail] = useState<UnifiedDistrictDetail | null>(null);

  useEffect(() => {
    if (!state || !district) return;
    async function fetchDetail() {
      setLoading(true);
      setError(null);
      try {
        const [response, unified] = await Promise.all([
          getDistrictDetail(state as string, district as string),
          getUnifiedDistrict(state as string, district as string).catch(() => null),
        ]);
        setUnifiedDetail(unified);
        if (response.records.length === 0) {
          setError('No data available for this district.');
          return;
        }
        const latestRecord = response.records.slice().sort((a, b) => b.year - a.year)[0];
        setDetail({
          state: recordState(latestRecord),
          district: recordDistrict(latestRecord),
          year: latestRecord.year,
          riskClass: latestRecord.risk_class.replace(' Risk', '') as DistrictDetail['riskClass'],
          priority: latestRecord.priority.replace(' Priority', '') as DistrictDetail['priority'],
          indicators: [
            { name: 'ANC First Trimester', value: latestRecord.ANC_First_Trimester_Pct, unit: '%', interpretation: 'Observed value; no clinical threshold applied.' },
            { name: 'TT2 Booster', value: latestRecord.TT2_Booster_Pct, unit: '%', interpretation: 'Observed value; no clinical threshold applied.' },
            { name: 'Severe Anemia', value: latestRecord.Severe_Anemia_Pct, unit: '%', interpretation: 'Observed value; no clinical threshold applied.' },
            { name: 'Institutional Delivery', value: latestRecord.Institutional_Delivery_Pct, unit: '%', interpretation: 'Observed value; no clinical threshold applied.' },
            { name: 'PNC within 48h', value: latestRecord.PNC_48h_Pct, unit: '%', interpretation: 'Observed value; no clinical threshold applied.' },
            { name: 'Obstetric Complications', value: latestRecord.Obstetric_Complications_Pct, unit: '%', interpretation: 'Observed value; no clinical threshold applied.' },
          ],
          contributingFactors: [
            { feature: latestRecord.top_contributing_feature_1, explanation: 'Ranked among the model\'s top contributors for this district-year record.' },
            { feature: latestRecord.top_contributing_feature_2, explanation: 'Ranked among the model\'s top contributors for this district-year record.' },
            { feature: latestRecord.top_contributing_feature_3, explanation: 'Ranked among the model\'s top contributors for this district-year record.' },
          ],
          planningPriorities: [latestRecord.planning_focus_1, latestRecord.planning_focus_2, latestRecord.planning_focus_3],
        });
        setPriorityHistory(response.priority_history);
        setHistory(response.records.slice().sort((a, b) => a.year - b.year).map((r) => ({
          year: r.year,
          riskClass: r.risk_class.replace(' Risk', ''),
          priority: r.priority.replace(' Priority', ''),
        })));
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load district details.');
      } finally {
        setLoading(false);
      }
    }
    fetchDetail();
  }, [state, district]);

  function recordState(r: { state: string }) { return r.state; }
  function recordDistrict(r: { district: string }) { return r.district; }

  if (!state || !district) {
    return <Navigate to="/districts" replace />;
  }

  if (loading) {
    return (
      <AppLayout>
        <div className="content condensed"><LoadingState /></div>
      </AppLayout>
    );
  }

  if (error) {
    return (
      <AppLayout>
        <div className="content condensed">
          <ErrorState message={error} onRetry={() => { setLoading(true); setError(null); }} />
        </div>
      </AppLayout>
    );
  }

  if (!detail) {
    return (
      <AppLayout>
        <div className="content condensed">
          <div className="card" style={{ padding: 'var(--space-8)', textAlign: 'center' }}>
            <h2 className="card-title">District Not Found</h2>
            <p className="note">
              No detailed information is available for &ldquo;{decodeURIComponent(district)}&rdquo; in{' '}
              &ldquo;{decodeURIComponent(state)}&rdquo;.
            </p>
            <Link className="btn btn-secondary" to="/districts">
              Back to District Explorer
            </Link>
          </div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="content">
        <div className="page-header">
          <div className="page-header-main">
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => navigate('/districts')}
              aria-label="Back to District Explorer"
            >
              <ArrowLeft size={16} strokeWidth={2} /> Back to District Explorer
            </button>
            <h1 className="page-title">{detail.district}, {detail.state}</h1>
            <p className="page-subtitle">
              District risk profile and planning priorities based on the latest historical assessment (Year{' '}
              {detail.year}). Historical MRCDSS assessment together with Recent HMIS evidence for the same
              district.
            </p>
          </div>
        </div>

        <div className="grid-4" style={{ gap: 'var(--space-3)' }}>
          <div className="kpi-card" style={{ padding: 'var(--space-4)' }}>
            <span className="kpi-label">Risk Class</span>
            <span
              className="kpi-value"
              style={{ fontSize: '1.6rem', color: riskColor(detail.riskClass) }}
            >
              {detail.riskClass}
            </span>
            <span className="kpi-delta kpi-delta-neutral" style={{ fontSize: '0.75rem' }}>
              {detail.riskClass} Risk
            </span>
          </div>
          <div className="kpi-card" style={{ padding: 'var(--space-4)', borderLeft: '4px solid var(--ink-2)' }}>
            <span className="kpi-label">Priority Level</span>
            <span className="kpi-value" style={{ fontSize: '1.6rem' }}>
              {detail.priority}
            </span>
            <span className="kpi-delta kpi-delta-neutral" style={{ fontSize: '0.75rem' }}>
              {detail.priority} Priority
            </span>
          </div>
          <div className="kpi-card" style={{ padding: 'var(--space-4)' }}>
            <span className="kpi-label">Latest Year</span>
            <span className="kpi-value" style={{ fontSize: '1.6rem' }}>{detail.year}</span>
          </div>
          <div className="kpi-card" style={{ padding: 'var(--space-4)' }}>
            <span className="kpi-label">Years of Data</span>
            <span className="kpi-value" style={{ fontSize: '1.6rem' }}>{history.length}</span>
          </div>
        </div>

        <section className="section">
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Risk & Priority</h2>
            </div>
            <div className="card-body" style={{ paddingTop: 0, display: 'flex', gap: 'var(--space-4)', flexWrap: 'wrap' }}>
              <div style={{ flex: 1, minWidth: 200, display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                <Target size={20} strokeWidth={2} color={riskColor(detail.riskClass)} />
                <div>
                  <span className="kpi-label" style={{ display: 'block', fontSize: '0.75rem' }}>Risk Class</span>
                  <span className="kpi-value" style={{ fontSize: '1.4rem', color: riskColor(detail.riskClass), fontWeight: '700' }}>
                    {detail.riskClass} Risk
                  </span>
                </div>
              </div>
              <div style={{ flex: 1, minWidth: 200, display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                <AlertTriangle size={20} strokeWidth={2} color="#c27d2f" />
                <div>
                  <span className="kpi-label" style={{ display: 'block', fontSize: '0.75rem' }}>Priority Level</span>
                  <span className="kpi-value" style={{ fontSize: '1.4rem', color: '#c27d2f', fontWeight: '700' }}>
                    {detail.priority} Priority
                  </span>
                </div>
              </div>
              {detail.riskClass === 'High' && (
                <div className="callout warn" style={{ flex: 1, minWidth: 280 }}>
                  <span className="callout-icon">
                    <AlertTriangle size={16} strokeWidth={2} />
                  </span>
                  <div className="callout-body">
                    <p className="callout-text" style={{ margin: 0, fontSize: '0.85rem' }}>
                      Historical assessment indicates this district requires planning attention. Not a clinical
                      diagnosis or current status.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>

        <section className="section">
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Historical District Risk Timeline (MRCDSS)</h2>
            </div>
            <div className="card-body" style={{ paddingTop: 0 }}>
              {priorityHistory && (
                <div className="callout info" style={{ marginBottom: 'var(--space-4)' }}>
                  <span className="callout-icon">
                    <Shield size={16} strokeWidth={2} />
                  </span>
                  <div className="callout-body">
                    <p className="callout-title" style={{ margin: 0, fontSize: '0.9rem' }}>
                      {priorityHistory.repeated_priority}
                    </p>
                    <p className="callout-text" style={{ margin: 0, fontSize: '0.85rem' }}>
                      Based on {priorityHistory.years_observed} observed historical years:{' '}
                      {priorityHistory.high_risk_years} High ({(priorityHistory.high_risk_proportion * 100).toFixed(1)}%),{' '}
                      {priorityHistory.medium_risk_years} Medium ({(priorityHistory.medium_risk_proportion * 100).toFixed(1)}%),{' '}
                      and {priorityHistory.low_risk_years} Low ({(priorityHistory.low_risk_proportion * 100).toFixed(1)}%).
                      Latest historical assessment: {priorityHistory.latest_year} ({priorityHistory.latest_risk_class},
                      {priorityHistory.latest_priority}). This repeated label is not the latest priority.
                    </p>
                    <p className="note text-small mt-2" style={{ margin: 0 }}>{priorityHistory.rule}</p>
                  </div>
                </div>
              )}
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th scope="col">Year</th>
                      <th scope="col">Risk Class</th>
                      <th scope="col">Priority Level</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((h) => (
                      <tr key={h.year}>
                        <td>{h.year}</td>
                        <td>
                          <span
                            className="badge"
                            style={{
                              backgroundColor: `${riskColor(h.riskClass)}15`,
                              color: riskColor(h.riskClass),
                              borderColor: `${riskColor(h.riskClass)}30`,
                            }}
                          >
                            {h.riskClass}
                          </span>
                        </td>
                        <td>
                          <span className="badge badge-outline">{h.priority}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>

        <div className="grid-2">
          <section className="section">
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Maternal Health Indicators</h2>
                <p className="note text-small mb-0">
                  Observed values from the latest historical assessment. No clinical threshold applied.
                </p>
              </div>
              <div className="card-body" style={{ paddingTop: 0 }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 'var(--space-3)' }}>
                  {detail.indicators.map((indicator) => (
                    <div
                      key={indicator.name}
                      className="card"
                      style={{ padding: 'var(--space-3)', border: '1px solid var(--line-soft)' }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 'var(--space-2)' }}>
                        <span className="kpi-label" style={{ fontSize: '0.8rem' }}>{indicator.name}</span>
                        <span className="kpi-value" style={{ fontSize: '1.1rem' }}>
                          {formatPct(indicator.value)}
                        </span>
                      </div>
                      <p className="note text-small" style={{ margin: 'var(--space-1) 0 0' }}>{indicator.interpretation}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>

          <section className="section">
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Planning Focus</h2>
                <p className="note text-small mb-0">
                  Model-attributed planning focus areas. Public-health planning guidance, not individual medical
                  recommendations.
                </p>
              </div>
              <div className="card-body" style={{ paddingTop: 0 }}>
                <ol className="planning-list-compact" style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                  {detail.planningPriorities.map((priority, index) => (
                    <li key={`${priority}-${index}`} style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--space-2_5)', padding: 'var(--space-1_5) 0', borderBottom: '1px solid var(--line-soft)' }}>
                      <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '24px', height: '24px', backgroundColor: 'var(--navy-deep)', color: '#ffffff', fontSize: '0.75rem', fontWeight: '700', borderRadius: '4px', flexShrink: 0 }}>
                        {index + 1}
                      </span>
                      <span className="planning-list-text" style={{ color: 'var(--ink-2)', fontSize: '0.88rem', lineHeight: 1.5 }}>{priority}</span>
                    </li>
                  ))}
                </ol>
              </div>
            </div>
          </section>
        </div>

        <section className="section">
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Contributing Factors</h2>
              <p className="note text-small mb-0">
                Features are ranked by the saved model attribution. Signed district-specific SHAP direction is
                not available for this detail view, so no direction is inferred. Attribution does not establish
                causality.
              </p>
            </div>
            <div className="card-body" style={{ paddingTop: 0 }}>
              <ol className="factor-list-compact" style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                {detail.contributingFactors.map((factor, index) => (
                  <li key={factor.feature} style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--space-2_5)', padding: 'var(--space-1_5) 0', borderBottom: '1px solid var(--line-soft)' }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '24px', height: '24px', backgroundColor: 'var(--surface-2)', color: 'var(--ink-2)', fontSize: '0.75rem', fontWeight: '700', borderRadius: '4px', flexShrink: 0 }}>
                      {index + 1}
                    </span>
                    <div className="factor-list-content" style={{ display: 'flex', flexDirection: 'column', gap: '2px', flex: 1 }}>
                      <span className="factor-list-name" style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: '0.82rem', color: 'var(--ink)', fontWeight: '500' }}>
                        {factor.feature}
                      </span>
                      <span className="factor-list-direction" style={{ fontSize: '0.78rem', color: 'var(--ink-3)' }}>
                        Contribution direction unavailable
                      </span>
                      <span className="factor-list-explanation" style={{ fontSize: '0.75rem', color: 'var(--ink-3)' }}>{factor.explanation}</span>
                    </div>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </section>

        <section className="section">
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Recent HMIS Evidence</h2>
              <p className="note text-small mb-0">
                Latest acquired Recent HMIS (Dataset 3) observations for this district. Values reflect current
                HMIS reporting. No risk classification is assigned to Recent HMIS records.
              </p>
            </div>
            <div className="card-body" style={{ paddingTop: 0 }}>
              {unifiedDetail && unifiedDetail.recent.length > 0 ? (
                <>
                  <div className="table-wrap">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th scope="col">Year</th>
                          <th scope="col">ANC First Trimester</th>
                          <th scope="col">TT2 / Booster</th>
                          <th scope="col">Severe Anemia</th>
                          <th scope="col">Obstetric Complications</th>
                          <th scope="col">Source File</th>
                        </tr>
                      </thead>
                      <tbody>
                        {unifiedDetail.recent.map((r) => (
                          <tr key={r.Year}>
                            <td>{r.Year}</td>
                            <td>{formatPct(r.ANC_First_Trimester_Pct)}</td>
                            <td>{formatPct(r.TT2_Booster_Pct)}</td>
                            <td>{formatPct(r.Severe_Anemia_Pct)}</td>
                            <td>{formatPct(r.Obstetric_Complications_Pct)}</td>
                            <td>{r.hmis_source_file ?? '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="callout info" style={{ marginTop: 'var(--space-4)' }}>
                    <span className="callout-icon">
                      <Shield size={16} strokeWidth={2} />
                    </span>
                    <div className="callout-body">
                      <p className="callout-text" style={{ margin: 0, fontSize: '0.85rem' }}>
                        {unifiedDetail.recent[0].indicator_definition_status}
                      </p>
                    </div>
                  </div>
                </>
              ) : (
                <div className="empty-state" style={{ padding: 'var(--space-6) var(--space-4)' }}>
                  <span className="icon" aria-hidden="true">
                    <Shield size={32} strokeWidth={2} />
                  </span>
                  <h2>No Recent HMIS observations</h2>
                  <p>No Recent HMIS observations are available for this district.</p>
                </div>
              )}
            </div>
          </div>
        </section>
      </div>
    </AppLayout>
  );
}

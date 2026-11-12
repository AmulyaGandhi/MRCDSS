import { useState, useEffect } from 'react';
import { useParams, useNavigate, Navigate, Link } from 'react-router-dom';
import { ArrowLeft, TrendingUp, AlertTriangle, Target } from 'lucide-react';
import AppLayout from '../components/AppLayout';
import TopBar from '../components/TopBar';
import SectionBlock from '../components/SectionBlock';
import IndicatorBarChart from '../components/charts/IndicatorBarChart';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import { getDistrictDetail } from '../api/districtDetail';
import { getUnifiedDistrict, type UnifiedDistrictDetail } from '../api/unified';
import { type DistrictDetail } from '../types';

function formatPct(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return '—';
  return `${value.toFixed(1)}%`;
}

function getInterpretationForIndicator(name: string, value: number): string {
  const isBad = name === 'Severe Anemia' || name === 'Obstetric Complications';
  if (isBad) {
    if (value <= 15) return 'Within acceptable range.';
    if (value <= 25) return 'Moderate - improvement recommended.';
    return 'Elevated - intervention needed.';
  }
  if (value >= 50) return 'Above target.';
  if (value >= 30) return 'Moderate - improvement recommended.';
  return 'Below target - improvement needed.';
}

function mapApiRecordToDetail(record: {
  state: string;
  district: string;
  year: number;
  risk_class: string;
  priority: string;
  top_contributing_feature_1: string;
  top_contributing_feature_2: string;
  top_contributing_feature_3: string;
  planning_focus_1: string;
  planning_focus_2: string;
  planning_focus_3: string;
  ANC_First_Trimester_Pct: number;
  TT2_Booster_Pct: number;
  Severe_Anemia_Pct: number;
  Institutional_Delivery_Pct: number;
  PNC_48h_Pct: number;
  Obstetric_Complications_Pct: number;
}): DistrictDetail {
  const indicators = [
    { name: 'ANC First Trimester', value: record.ANC_First_Trimester_Pct, unit: '%', interpretation: getInterpretationForIndicator('ANC First Trimester', record.ANC_First_Trimester_Pct) },
    { name: 'TT2 Booster', value: record.TT2_Booster_Pct, unit: '%', interpretation: getInterpretationForIndicator('TT2 Booster', record.TT2_Booster_Pct) },
    { name: 'Severe Anemia', value: record.Severe_Anemia_Pct, unit: '%', interpretation: getInterpretationForIndicator('Severe Anemia', record.Severe_Anemia_Pct) },
    { name: 'Institutional Delivery', value: record.Institutional_Delivery_Pct, unit: '%', interpretation: getInterpretationForIndicator('Institutional Delivery', record.Institutional_Delivery_Pct) },
    { name: 'PNC within 48h', value: record.PNC_48h_Pct, unit: '%', interpretation: getInterpretationForIndicator('PNC within 48h', record.PNC_48h_Pct) },
    { name: 'Obstetric Complications', value: record.Obstetric_Complications_Pct, unit: '%', interpretation: getInterpretationForIndicator('Obstetric Complications', record.Obstetric_Complications_Pct) },
  ];

  const contributingFactors = [
    { feature: record.top_contributing_feature_1, direction: 'positive' as const, explanation: 'Top contributor to district risk classification.' },
    { feature: record.top_contributing_feature_2, direction: 'positive' as const, explanation: 'Significant contributor to district risk classification.' },
    { feature: record.top_contributing_feature_3, direction: 'positive' as const, explanation: 'Notable contributor to district risk classification.' },
  ];

  return {
    state: record.state,
    district: record.district,
    year: record.year,
    riskClass: record.risk_class.replace(' Risk', '') as DistrictDetail['riskClass'],
    priority: record.priority.replace(' Priority', '') as DistrictDetail['priority'],
    indicators,
    contributingFactors,
    planningPriorities: [record.planning_focus_1, record.planning_focus_2, record.planning_focus_3],
  };
}

export default function DistrictDetails() {
  const { state, district } = useParams<{ state: string; district: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<DistrictDetail | null>(null);
  const [history, setHistory] = useState<Array<{ year: number; riskClass: string; priority: string }>>([]);
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
        setDetail(mapApiRecordToDetail(latestRecord));
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

  if (!state || !district) {
    return <Navigate to="/districts" replace />;
  }

  if (loading) {
    return (
      <AppLayout>
        <main className="content">
          <TopBar title="District Details" />
          <LoadingState />
        </main>
      </AppLayout>
    );
  }

  if (error) {
    return (
      <AppLayout>
        <main className="content">
          <TopBar title="District Details" />
          <ErrorState message={error} onRetry={() => { setLoading(true); setError(null); }} />
        </main>
      </AppLayout>
    );
  }

  if (!detail) {
    return (
      <AppLayout>
        <main className="content">
          <TopBar title="District Details" />
          <div className="not-found">
            <h2 className="not-found-title">District Not Found</h2>
            <p className="not-found-text">
              No detailed information is available for &ldquo;{decodeURIComponent(district)}&rdquo; in &ldquo;{decodeURIComponent(state)}&rdquo;.
            </p>
            <Link className="not-found-link" to="/districts">Back to District Explorer</Link>
          </div>
        </main>
      </AppLayout>
    );
  }

  const chartData = detail.indicators.map((i) => ({
    name: i.name,
    value: i.value,
  }));

  return (
    <AppLayout>
      <main className="content">
        <TopBar
          title={`${detail.district}, ${detail.state}`}
          subtitle={`District risk profile and planning priorities (Year ${detail.year})`}
        />

        <div className="mt-8 mb-16">
          <button type="button" className="back-button" onClick={() => navigate('/districts')}>
            <ArrowLeft size={16} style={{ marginRight: '0.5rem' }} />
            Back to District Explorer
          </button>
        </div>

        <div className="dashboard-grid">
          <div className="purpose-section" style={{ marginBottom: 0 }}>
            <h2 className="purpose-title">District Intelligence</h2>
            <p className="purpose-text">
              {detail.district} ({detail.state}) shows a {detail.riskClass.toLowerCase()} risk profile with
              {detail.priority.toLowerCase()} priority designation based on DSS decision rules.
            </p>
            <div className="purpose-facts">
              <div className="purpose-fact">
                <span className="purpose-fact-value">{detail.riskClass}</span>
                <span className="purpose-fact-label">Risk Class</span>
              </div>
              <div className="purpose-fact">
                <span className="purpose-fact-value">{detail.priority}</span>
                <span className="purpose-fact-label">Priority</span>
              </div>
              <div className="purpose-fact">
                <span className="purpose-fact-value">{detail.year}</span>
                <span className="purpose-fact-label">Latest Year</span>
              </div>
              <div className="purpose-fact">
                <span className="purpose-fact-value">{history.length}</span>
                <span className="purpose-fact-label">Years of Data</span>
              </div>
            </div>
          </div>
          <SectionBlock title="Risk & Priority">
            <div className="detail-mapping">
              <div className="detail-mapping-item">
                <TrendingUp size={18} className="detail-mapping-icon" />
                <div>
                  <span className="detail-mapping-label">Risk Class</span>
                  <span className="detail-mapping-value">{detail.riskClass} Risk</span>
                </div>
              </div>
              <div className="detail-mapping-item">
                <Target size={18} className="detail-mapping-icon" />
                <div>
                  <span className="detail-mapping-label">Priority Level</span>
                  <span className="detail-mapping-value">{detail.priority} Priority</span>
                </div>
              </div>
              {detail.riskClass === 'High' && (
                <div className="detail-mapping-item detail-mapping-alert">
                  <AlertTriangle size={18} className="detail-mapping-icon" />
                  <div>
                    <span className="detail-mapping-label">Status</span>
                    <span className="detail-mapping-value">Requires Attention</span>
                  </div>
                </div>
              )}
            </div>
          </SectionBlock>
        </div>

        <SectionBlock title="Historical District Risk Timeline (MRCDSS)">
          <div className="table-container">
            <table className="district-table">
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
                    <td><span className={`priority-badge badge-${h.riskClass.toLowerCase()}`}>{h.riskClass}</span></td>
                    <td><span className={`priority-badge badge-${h.priority.toLowerCase()}`}>{h.priority}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SectionBlock>

        <SectionBlock title="Recent HMIS Evidence">
          {unifiedDetail && unifiedDetail.recent.length > 0 ? (
            <>
              <p className="section-note">
                Latest acquired Recent HMIS (Dataset 3) observations for this district. Values reflect current
                HMIS reporting; imported at their native district representation. No risk classification is
                assigned to Recent HMIS records.
              </p>
              <div className="table-container">
                <table className="district-table">
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
              <div className="callout-box">
                <p className="body-text">
                  {unifiedDetail.recent[0].indicator_definition_status}
                </p>
              </div>
            </>
          ) : (
            <p className="section-note">
              No Recent HMIS observations are available for this district.
            </p>
          )}
        </SectionBlock>

        <div className="dashboard-grid">
          <SectionBlock title="Maternal Health Indicators">
            <IndicatorBarChart data={chartData} />
          </SectionBlock>
          <SectionBlock title="Planning Focus">
            <ol className="planning-list-compact">
              {detail.planningPriorities.map((priority, index) => (
                <li key={`${priority}-${index}`} className="planning-list-item">
                  <span className="planning-list-number">{index + 1}</span>
                  <span className="planning-list-text">{priority}</span>
                </li>
              ))}
            </ol>
          </SectionBlock>
        </div>

        <SectionBlock title="Contributing Factors">
          <p className="section-note">
            SHAP values indicate how features contributed to the model classification. They do not establish causality.
          </p>
          <ol className="factor-list-compact">
            {detail.contributingFactors.map((factor, index) => (
              <li key={factor.feature} className="factor-list-item">
                <span className="factor-list-rank">{index + 1}</span>
                <div className="factor-list-content">
                  <span className="factor-list-name">{factor.feature}</span>
                  <span className="factor-list-direction">
                    {factor.direction === 'positive' ? 'Increases risk' : 'Decreases risk'}
                  </span>
                  <span className="factor-list-explanation">{factor.explanation}</span>
                </div>
              </li>
            ))}
          </ol>
        </SectionBlock>
      </main>
    </AppLayout>
  );
}

import { useState, useEffect, useCallback } from 'react';
import AppLayout from '../components/AppLayout';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import { getRiskAnalysis } from '../api/riskAnalysis';
import { getRecentHmisIndicators, type RecentHmisIndicatorsData } from '../api/recentHmis';
import { AlertTriangle, Info } from 'lucide-react';

function formatMetric(value: number, decimals: number): string {
  return value.toFixed(decimals);
}

export default function RiskAnalysis() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<{
    risk_counts: Record<string, number>;
    cluster_profiles: Array<{
      cluster_id: number;
      cluster_size: number;
      ANC_First_Trimester_Pct: number;
      TT2_Booster_Pct: number;
      Severe_Anemia_Pct: number;
      Institutional_Delivery_Pct: number;
      PNC_48h_Pct: number;
      Obstetric_Complications_Pct: number;
    }>;
    clustering_metrics: {
      silhouette_score: number;
      davies_bouldin_index: number;
      calinski_harabasz_index: number;
    };
    clustering_notes: {
      k_selection: string;
      silhouette_interpretation: string;
      label_sensitivity: string;
    };
    model_comparison: Array<{
      model: string;
      accuracy: number;
      precision: number;
      recall: number;
      f1: number;
      roc_auc: number;
    }>;
    confusion_matrix: Array<{
      actual: string;
      predicted_High_Risk: number;
      predicted_Low_Risk: number;
      predicted_Medium_Risk: number;
    }>;
    evaluation_design: {
      label_source: string;
      selection_metric: string;
      test_records: number;
      test_units: number;
      test_units_also_in_training: number;
      test_records_sharing_units_with_training: number;
      test_records_sharing_units_with_training_proportion: number;
      grouped_or_temporal_validation_completed: boolean;
      note: string;
    };
    shap_summary: {
      class_label: string;
      records: number;
      features: Array<{
        feature: string;
        positive_mean: number;
        negative_mean: number;
        mean_abs_shap: number;
        positive_count: number;
        negative_count: number;
      }>;
      note: string;
    };
    sensitivity_analysis: {
      primary_features: number;
      sensitivity_features: number;
      primary_silhouette: number;
      sensitivity_silhouette: number;
      primary_high_risk_size: number;
      sensitivity_high_risk_size: number;
      risk_class_changed: number;
      risk_class_change_proportion: number;
      risk_class_agreement: number;
    };
  } | null>(null);
  const [recentIndicators, setRecentIndicators] = useState<RecentHmisIndicatorsData | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [analysis, recent] = await Promise.all([
        getRiskAnalysis(),
        getRecentHmisIndicators().catch(() => null),
      ]);
      setData(analysis);
      setRecentIndicators(recent);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load risk analysis.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

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

  const riskCounts = data.risk_counts;
  const totalRecords = Object.values(riskCounts).reduce((s, v) => s + v, 0);

  const RISK_LABEL_COLOR: Record<string, string> = {
    'Low Risk': '#3a8248',
    'Medium Risk': '#c27d2f',
    'High Risk': '#b94538',
  };

  const shapSummaryRows = data.shap_summary.features.map((f) => [
    f.feature.replace(/_Pct/g, '%').replace(/_/g, ' '),
    formatMetric(f.positive_mean, 3),
    formatMetric(f.negative_mean, 3),
    formatMetric(f.mean_abs_shap, 3),
    `${f.positive_count.toLocaleString()} / ${f.negative_count.toLocaleString()}`,
  ]);

  return (
    <AppLayout>
      <div className="content">
        <div className="page-header">
          <div className="page-header-main">
            <span className="page-kicker">Analytical Validity</span>
            <h1 className="page-title">Risk Analysis</h1>
            <p className="page-subtitle">
              District-year records from the historical MRCDSS dataset (2008–2019) are classified into risk
              classes using K-Means clustering (K=3). Supervised models replicate these derived profiles using
              the same six-feature space. Risk classes are derived analytical groups, not clinical diagnoses.
            </p>
          </div>
        </div>

        <section className="section">
          <div className="card elevated">
            <div className="card-header">
              <div className="flex-between">
                <div>
                  <h2 className="card-title">Evaluation Scope & Disclosure</h2>
                  <p className="note text-small mb-0">
                    Supervised metrics measure reproduction of K-Means-derived labels on seen units — they are
                    <strong>not</strong> evidence of external or clinical predictive accuracy.
                  </p>
                </div>
                <span className="badge badge-outline">
                  Record-level 80/20 split
                </span>
              </div>
            </div>
            <div className="card-body" style={{ paddingTop: 0 }}>
              <div className="callout info" style={{ marginBottom: 'var(--space-4)' }}>
                <span className="callout-icon">
                  <Info size={16} strokeWidth={2} />
                </span>
                <div className="callout-body">
                  <p className="callout-text" style={{ margin: 0 }}>
                    {data.evaluation_design.test_records.toLocaleString()} test records from{' '}
                    {data.evaluation_design.test_units.toLocaleString()} State–District units.
                    <strong>{data.evaluation_design.test_records_sharing_units_with_training.toLocaleString()} of{' '}
                    {data.evaluation_design.test_records.toLocaleString()} test records ({(data.evaluation_design.test_records_sharing_units_with_training_proportion * 100).toFixed(1)}%)</strong>{' '}
                    belong to units also present in training. Labels come from{' '}
                    {data.evaluation_design.label_source}; the selected model was chosen by{' '}
                    {data.evaluation_design.selection_metric}. Grouped or temporal validation has not been
                    completed.
                  </p>
                </div>
              </div>
              <div className="grid-4" style={{ gap: 'var(--space-3)' }}>
                <div className="kpi-card" style={{ padding: 'var(--space-3)' }}>
                  <span className="kpi-label">Silhouette Score</span>
                  <span className="kpi-value" style={{ fontSize: '1.5rem' }}>
                    {formatMetric(data.clustering_metrics.silhouette_score, 6)}
                  </span>
                  <span className="kpi-delta kpi-delta-neutral" style={{ fontSize: '0.75rem' }}>
                    Weak–moderate separation
                  </span>
                </div>
                <div className="kpi-card" style={{ padding: 'var(--space-3)' }}>
                  <span className="kpi-label">High Risk Size</span>
                  <span className="kpi-value" style={{ fontSize: '1.5rem' }}>
                    {data.sensitivity_analysis.primary_high_risk_size.toLocaleString()}
                  </span>
                </div>
                <div className="kpi-card" style={{ padding: 'var(--space-3)' }}>
                  <span className="kpi-label">Test Units Also in Train</span>
                  <span className="kpi-value" style={{ fontSize: '1.3rem' }}>
                    {data.evaluation_design.test_units_also_in_training.toLocaleString()}
                  </span>
                </div>
                <div className="kpi-card" style={{ padding: 'var(--space-3)' }}>
                  <span className="kpi-label">Sensitivity Class Change</span>
                  <span className="kpi-value" style={{ fontSize: '1.3rem' }}>
                    {formatMetric(data.sensitivity_analysis.risk_class_change_proportion * 100, 2)}%
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
                <h2 className="card-title">Risk Distribution</h2>
              </div>
              <div className="card-body" style={{ paddingTop: 0, display: 'flex', gap: 'var(--space-4)', alignItems: 'center' }}>
                <div style={{ flex: 1 }}>
                  <div className="distribution" style={{ padding: 'var(--space-4)' }}>
                    {Object.entries(riskCounts).map(([name, value]) => {
                      const share = totalRecords ? value / totalRecords : 0;
                      const color = RISK_LABEL_COLOR[name] ?? '#7a8797';
                      return (
                        <>
                          <div className="dist-bar">
                            <div
                              className="dist-seg"
                              style={{ width: `${share * 100}%`, backgroundColor: color }}
                            />
                          </div>
                          <div className="dist-legend">
                            <span className="dist-swatch" style={{ backgroundColor: color }} />
                            <span>{name.replace(' Risk', '')}</span>
                            <span style={{ marginLeft: 'auto' }}>{value.toLocaleString()}</span>
                            <span className="dist-legend-share" style={{ color: 'var(--ink-3)' }}>
                              {(share * 100).toFixed(1)}%
                            </span>
                          </div>
                        </>
                      );
                    })}
                  </div>
                </div>
                <div style={{ minWidth: 220 }}>
                  <MetricTableSmall
                    headers={['Risk Class', 'Count', 'Share']}
                    rows={Object.entries(riskCounts).map(([name, value]) => [
                      name,
                      value.toLocaleString(),
                      ((value / totalRecords) * 100).toFixed(1) + '%',
                    ])}
                  />
                </div>
              </div>
            </div>
          </section>

          <section className="section">
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">K-Means Risk Profiles (Cluster Means)</h2>
                <p className="note text-small mb-0 mt-2">
                  Data-derived groupings for analytical purposes. Not clinical ground truth.
                </p>
              </div>
              <div className="card-body" style={{ paddingTop: 0 }}>
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th scope="col">Profile</th>
                        <th scope="col">ANC 1st Tri</th>
                        <th scope="col">TT2 Booster</th>
                        <th scope="col">Severe Anemia</th>
                        <th scope="col">Inst. Delivery</th>
                        <th scope="col">PNC 48h</th>
                        <th scope="col">Obst. Compl.</th>
                        <th scope="col">Size</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.cluster_profiles.map((p) => {
                        const label =
                          p.cluster_id === 0 ? 'Low Risk' : p.cluster_id === 1 ? 'Medium Risk' : 'High Risk';
                        const color = RISK_LABEL_COLOR[label] ?? '#7a8797';
                        return (
                          <tr key={p.cluster_id}>
                            <td>
                              <span className="badge" style={{ backgroundColor: `${color}15`, color, borderColor: `${color}30` }}>
                                {label}
                              </span>
                            </td>
                            <td>{formatMetric(p.ANC_First_Trimester_Pct, 1)}%</td>
                            <td>{formatMetric(p.TT2_Booster_Pct, 1)}%</td>
                            <td>{formatMetric(p.Severe_Anemia_Pct, 1)}%</td>
                            <td>{formatMetric(p.Institutional_Delivery_Pct, 1)}%</td>
                            <td>{formatMetric(p.PNC_48h_Pct, 1)}%</td>
                            <td>{formatMetric(p.Obstetric_Complications_Pct, 1)}%</td>
                            <td>{p.cluster_size.toLocaleString()}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </section>
        </div>

        <section className="section">
          <div className="card elevated">
            <div className="card-header">
              <h2 className="card-title">Classification Model Performance</h2>
              <p className="note text-small mb-0">
                Comparison of accuracy, macro-precision, macro-recall, and macro-F1 across the four evaluated
                models. Logistic Regression was selected by macro-F1.
              </p>
            </div>
            <div className="card-body" style={{ paddingTop: 0 }}>
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th scope="col">Model</th>
                      <th scope="col">Accuracy</th>
                      <th scope="col">Precision</th>
                      <th scope="col">Recall</th>
                      <th scope="col">F1</th>
                      <th scope="col">ROC-AUC</th>
                      <th scope="col">Selected</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.model_comparison.map((m) => {
                      const isSelected = m.model === 'Logistic Regression';
                      return (
                        <tr key={m.model}>
                          <td>
                            <strong>{m.model}</strong>{isSelected && '  ·  selected by macro-F1'}
                          </td>
                          <td>{formatMetric(m.accuracy, 4)}</td>
                          <td>{formatMetric(m.precision, 4)}</td>
                          <td>{formatMetric(m.recall, 4)}</td>
                          <td>{formatMetric(m.f1, 4)}</td>
                          <td>{formatMetric(m.roc_auc, 6)}</td>
                          <td>
                            <span className={`badge ${isSelected ? 'badge-low' : 'badge-neutral'}`}>
                              {isSelected ? 'Yes' : '—'}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <p className="note mt-4">
                The reported accuracy and ROC-AUC describe reproduction of K-Means-derived labels on a
                record-level split, not independent clinical accuracy.
              </p>
            </div>
          </div>
        </section>

        <section className="section">
          <div className="card">
            <div className="card-header">
              <div className="flex-between">
                <div>
                  <h2 className="card-title">SHAP — Global High Risk Class Summary</h2>
                  <p className="note text-small mb-0 mt-2">
                    Mean absolute SHAP magnitude. Positive values push toward High Risk; negative values push
                    away. Global summaries, not signed explanations for a single district-year.
                  </p>
                </div>
              </div>
            </div>
            <div className="card-body" style={{ paddingTop: 0 }}>
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th scope="col">Feature</th>
                      <th scope="col">Mean Positive SHAP</th>
                      <th scope="col">Mean Negative SHAP</th>
                      <th scope="col">Mean Abs SHAP</th>
                      <th scope="col">Pos / Neg Records</th>
                    </tr>
                  </thead>
                  <tbody>
                    {shapSummaryRows.map((row, index) => (
                      <tr key={index}>
                        {row.map((cell, cellIndex) => (
                          <td key={cellIndex}>{cell}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="note mt-4">{data.shap_summary.note}</p>
              <p className="note">
                SHAP indicates model contribution, not causation. Signed district-specific direction is not
                stored for this detail view.
              </p>
            </div>
          </div>
        </section>

        <section className="section">
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Sensitivity / Robustness</h2>
              <p className="note text-small mb-0">
                Removing Severe Anemia is a sensitivity check, not a replacement model. Severe Anemia has
                cross-dataset harmonization uncertainty (D1 median 3.6% vs D2 median 51.5%).
              </p>
            </div>
            <div className="card-body" style={{ paddingTop: 0 }}>
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th scope="col">Analysis</th>
                      <th scope="col">Features</th>
                      <th scope="col">Silhouette Score</th>
                      <th scope="col">High Risk Size</th>
                      <th scope="col">Risk Class Changed</th>
                      <th scope="col">Agreement</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>Primary (6 features)</td>
                      <td>{data.sensitivity_analysis.primary_features}</td>
                      <td>{formatMetric(data.sensitivity_analysis.primary_silhouette, 6)}</td>
                      <td>{data.sensitivity_analysis.primary_high_risk_size.toLocaleString()}</td>
                      <td>—</td>
                      <td>—</td>
                    </tr>
                    <tr>
                      <td>Sensitivity (5 features, excl. Severe Anemia)</td>
                      <td>{data.sensitivity_analysis.sensitivity_features}</td>
                      <td>{formatMetric(data.sensitivity_analysis.sensitivity_silhouette, 6)}</td>
                      <td>{data.sensitivity_analysis.sensitivity_high_risk_size.toLocaleString()}</td>
                      <td>{data.sensitivity_analysis.risk_class_changed.toLocaleString()}</td>
                      <td>{formatMetric(data.sensitivity_analysis.risk_class_agreement * 100, 1)}%</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p className="note mt-4">
                It changes the risk class of{' '}
                {data.sensitivity_analysis.risk_class_changed.toLocaleString()} of{' '}
                {(data.sensitivity_analysis.risk_class_changed / (1 - data.sensitivity_analysis.risk_class_agreement || 1)).toLocaleString()}
                records ({(data.sensitivity_analysis.risk_class_change_proportion * 100).toFixed(2)}%), so the
                labels are materially sensitive. The near-similar silhouette scores do not demonstrate
                robustness.
              </p>
            </div>
          </div>
        </section>

        <section className="section">
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Recent HMIS Evidence</h2>
              <p className="note text-small mb-0">
                Dataset 3 (2020–2025) extends the system with current HMIS evidence, shown here as context.
                Recent records are not assigned a risk class and were not used to retrain the historical model.
              </p>
            </div>
            <div className="card-body" style={{ paddingTop: 0 }}>
              {recentIndicators ? (
                <>
                  <div className="table-wrap">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th scope="col">Indicator</th>
                          <th scope="col">Available</th>
                          <th scope="col">Missing</th>
                          <th scope="col">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {recentIndicators.indicators.map((ind) => (
                          <tr key={ind.key}>
                            <td>{ind.name}</td>
                            <td>{ind.valid.toLocaleString('en-US')}</td>
                            <td>{ind.missing.toLocaleString('en-US')}</td>
                            <td>
                              <span className="badge badge-outline">{ind.status}</span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="callout info" style={{ marginTop: 'var(--space-4)' }}>
                    <span className="callout-icon">
                      <AlertTriangle size={16} strokeWidth={2} />
                    </span>
                    <div className="callout-body">
                      <p className="callout-text" style={{ margin: 0 }}>
                        {recentIndicators.disclaimer}
                      </p>
                    </div>
                  </div>
                </>
              ) : (
                <p className="note">Recent HMIS indicator data is not available.</p>
              )}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              <h3 className="card-title" style={{ fontSize: 'var(--fs-lg)' }}>Methodological Caveats</h3>
              <div className="grid-2" style={{ gap: 'var(--space-3)' }}>
                {[
                  { h: 'Risk Classes', t: 'Derived from unsupervised K-Means clustering, not clinical diagnoses.' },
                  { h: 'Supervised Models', t: 'Replicate derived risk profiles, not independent clinical outcomes.' },
                  { h: 'Shared Units / Feature Space', t: 'All test records belong to units also seen in training; the same six features generate labels and train classifiers.' },
                  { h: 'Cluster Separation', t: 'Silhouette ≈ 0.238, weak–moderate separation. K=3 fixed for the Low/Medium/High design.' },
                  { h: 'Label Sensitivity', t: 'Excluding Severe Anemia changes 54.35% of records; labels are materially sensitive.' },
                  { h: 'Severe Anemia', t: 'Cross-dataset harmonization uncertainty (D1 median 3.6% vs D2 median 51.5%).' },
                  { h: 'No External Validation', t: 'Results are not validated against external clinical datasets.' },
                  { h: 'SHAP Values', t: 'Indicate model contribution, not causation.' },
                ].map((c, i) => (
                  <div key={i} className="card" style={{ padding: 'var(--space-3)' }}>
                    <h4 className="card-title" style={{ fontSize: '0.85rem', marginBottom: 'var(--space-1)' }}>{c.h}</h4>
                    <p className="note text-small" style={{ margin: 0 }}>{c.t}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </div>
    </AppLayout>
  );
}

function MetricTableSmall({ headers, rows }: { headers: string[]; rows: (string | number)[][] }) {
  return (
    <table className="data-table" style={{ width: '100%' }}>
      <thead>
        <tr>
          {headers.map((h) => (
            <th key={h} scope="col" style={{ fontSize: '0.72rem' }}>
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i}>
            {row.map((cell, j) => (
              <td key={j} style={{ fontSize: '0.85rem' }}>
                {cell}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

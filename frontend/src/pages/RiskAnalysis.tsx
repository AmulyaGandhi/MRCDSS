import { useState, useEffect, useCallback } from 'react';
import AppLayout from '../components/AppLayout';
import TopBar from '../components/TopBar';
import SectionBlock from '../components/SectionBlock';
import MetricTable from '../components/MetricTable';
import RiskDonutChart from '../components/charts/RiskDonutChart';
import ModelBarChart from '../components/charts/ModelBarChart';
import ModelPerformanceChart from '../components/charts/ModelPerformanceChart';
import FeatureBarChart from '../components/charts/FeatureBarChart';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import { getRiskAnalysis } from '../api/riskAnalysis';
import { getOverview } from '../api/overview';
import { getRecentHmisIndicators, type RecentHmisIndicatorsData } from '../api/recentHmis';

function formatMetric(value: number, decimals: number): string {
  return value.toFixed(decimals);
}

export default function RiskAnalysis() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<{
    risk_counts: Record<string, number>;
    cluster_profiles: Array<{ cluster_id: number; cluster_size: number; ANC_First_Trimester_Pct: number; TT2_Booster_Pct: number; Severe_Anemia_Pct: number; Institutional_Delivery_Pct: number; PNC_48h_Pct: number; Obstetric_Complications_Pct: number }>;
    clustering_metrics: { silhouette_score: number; davies_bouldin_index: number; calinski_harabasz_index: number };
    model_comparison: Array<{ model: string; accuracy: number; precision: number; recall: number; f1: number; roc_auc: number }>;
    confusion_matrix: Array<{ actual: string; predicted_High_Risk: number; predicted_Low_Risk: number; predicted_Medium_Risk: number }>;
    sensitivity_analysis: { primary_features: number; sensitivity_features: number; primary_silhouette: number; sensitivity_silhouette: number; sensitivity_high_risk_size: number };
  } | null>(null);
  const [featureData, setFeatureData] = useState<Array<{ feature: string; mean_abs_shap: number }> | null>(null);
  const [recentIndicators, setRecentIndicators] = useState<RecentHmisIndicatorsData | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [analysis, overview, recent] = await Promise.all([
        getRiskAnalysis(),
        getOverview(),
        getRecentHmisIndicators().catch(() => null),
      ]);
      setData(analysis);
      setFeatureData(overview.feature_ranking);
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

  const riskCounts = data.risk_counts;
  const totalRecords = Object.values(riskCounts).reduce((s, v) => s + v, 0);

  const bestModel = data.model_comparison.find((m) => m.model === 'Logistic Regression') ?? data.model_comparison[0];

  const riskChartData = Object.entries(riskCounts).map(([name, value]) => ({
    name: name.replace(' Risk', ''),
    value,
  }));

  const modelChartData = data.model_comparison.map((m) => ({
    model: m.model,
    Accuracy: m.accuracy,
    F1: m.f1,
    'ROC-AUC': m.roc_auc,
  }));

  const confusionRows = data.confusion_matrix.map((row) => [
    row.actual,
    row.predicted_High_Risk.toLocaleString(),
    row.predicted_Low_Risk.toLocaleString(),
    row.predicted_Medium_Risk.toLocaleString(),
  ]);

  const shapData = featureData?.map((f) => ({
    name: f.feature.replace(/_Pct/g, '%').replace(/_/g, ' '),
    value: f.mean_abs_shap,
  })) ?? [];

  const pipelineSteps = [
    { label: '6 Indicators', description: 'ANC First Trimester, TT2 Booster, Severe Anemia, Institutional Delivery, PNC 48h, Obstetric Complications' },
    { label: 'StandardScaler', description: 'Normalize all features to zero mean and unit variance' },
    { label: 'K-Means (K=3)', description: 'Unsupervised clustering produces Low, Medium, High risk profiles' },
    { label: 'Risk Profiles', description: 'Distinct patterns of maternal-health indicator values per cluster' },
  ];

  const modelRows = data.model_comparison.map((m) => {
    const isSelected = m.model === 'Logistic Regression';
    return [
      <span key="m" style={{ fontWeight: isSelected ? 700 : 400, color: isSelected ? '#1a5276' : undefined }}>{m.model}</span>,
      formatMetric(m.accuracy, 4),
      formatMetric(m.precision, 4),
      formatMetric(m.recall, 4),
      formatMetric(m.f1, 4),
      formatMetric(m.roc_auc, 4),
    ];
  });

  return (
    <AppLayout>
      <main className="content">
        <TopBar
          title="Risk Analysis"
          subtitle="Risk classification, clustering quality, model performance, and feature explainability"
        />

        <section className="purpose-section">
          <h2 className="purpose-title">Historical MRCDSS Risk Analysis</h2>
          <p className="purpose-text">
            District-year records from the historical MRCDSS dataset (2008–2019) are classified into risk
            classes using K-Means clustering (K=3) on StandardScaler-normalized maternal-health indicators.
            Supervised models replicate these derived profiles using the same six-feature space. Risk classes
            are derived analytical groups, not clinical diagnoses.
          </p>
          <div className="pipeline-list">
            {pipelineSteps.map((step, index) => (
              <div key={step.label} className="decision-journey-step">
                <span className="decision-journey-number">{index + 1}</span>
                <div className="decision-journey-content">
                  <span className="decision-journey-label">{step.label}</span>
                  <span className="decision-journey-description">{step.description}</span>
                </div>
                {index < pipelineSteps.length - 1 && <span className="decision-journey-arrow" aria-hidden="true">→</span>}
              </div>
            ))}
          </div>
          <p className="section-note">
            K-Means provides derived risk profiles, not clinical ground truth.
          </p>
        </section>

        <div className="dashboard-grid">
          <SectionBlock title="Risk Distribution">
            <RiskDonutChart data={riskChartData} />
            <div className="mt-16">
              <MetricTable headers={['Risk Class', 'Count', 'Share']} rows={Object.entries(riskCounts).map(([name, value]) => [
                name,
                value.toLocaleString(),
                ((value / totalRecords) * 100).toFixed(1) + '%',
              ])} />
            </div>
          </SectionBlock>
          <SectionBlock title="K-Means Risk Profiles">
            <p className="section-note">Each profile represents a distinct pattern of maternal-health indicator values. These are data-derived groupings for analytical purposes.</p>
            <MetricTable
              headers={['Profile', 'ANC 1st Tri', 'TT2 Booster', 'Severe Anemia', 'Inst. Delivery', 'PNC 48h', 'Obst. Compl.']}
              rows={data.cluster_profiles.map((p) => [
                p.cluster_id === 0 ? 'Low Risk' : p.cluster_id === 1 ? 'Medium Risk' : 'High Risk',
                formatMetric(p.ANC_First_Trimester_Pct, 1) + '%',
                formatMetric(p.TT2_Booster_Pct, 1) + '%',
                formatMetric(p.Severe_Anemia_Pct, 1) + '%',
                formatMetric(p.Institutional_Delivery_Pct, 1) + '%',
                formatMetric(p.PNC_48h_Pct, 1) + '%',
                formatMetric(p.Obstetric_Complications_Pct, 1) + '%',
              ])}
            />
          </SectionBlock>
        </div>

        <SectionBlock>
          <figure className="research-figure">
            <h3 className="figure-title">Classification Model Performance</h3>
            <p className="figure-subtitle">
              Comparison of accuracy, macro-precision, macro-recall, and macro-F1 across the four evaluated models.
            </p>
            <ModelPerformanceChart data={data.model_comparison} />
            <figcaption className="figure-note">
              Evaluation metrics are based on the held-out test set. Because the risk classes were derived from
              K-Means clustering rather than independent clinical ground truth, these results indicate how well the
              supervised models reproduce the derived risk profiles; they should not be interpreted as clinical
              prediction accuracy.
            </figcaption>
          </figure>
        </SectionBlock>

        <div className="dashboard-grid">
          <SectionBlock title="Model Comparison">
            <ModelBarChart data={modelChartData} />
          </SectionBlock>
          <SectionBlock title={`Selected Model: ${bestModel.model}`}>
            <div className="selected-model-block">
              <div className="selected-model-header">
                <span className="selected-model-label">Selected Model</span>
                <span className="selected-model-name">{bestModel.model}</span>
                <span className="selection-reason">Selected based on highest accuracy</span>
              </div>
              <div className="selected-model-metrics">
                <div className="metric-mini">
                  <span className="metric-mini-label">Accuracy</span>
                  <span className="metric-mini-value">{formatMetric(bestModel.accuracy, 4)}</span>
                </div>
                <div className="metric-mini">
                  <span className="metric-mini-label">Precision</span>
                  <span className="metric-mini-value">{formatMetric(bestModel.precision, 4)}</span>
                </div>
                <div className="metric-mini">
                  <span className="metric-mini-label">Recall</span>
                  <span className="metric-mini-value">{formatMetric(bestModel.recall, 4)}</span>
                </div>
                <div className="metric-mini">
                  <span className="metric-mini-label">F1</span>
                  <span className="metric-mini-value">{formatMetric(bestModel.f1, 4)}</span>
                </div>
                <div className="metric-mini">
                  <span className="metric-mini-label">ROC-AUC</span>
                  <span className="metric-mini-value">{formatMetric(bestModel.roc_auc, 4)}</span>
                </div>
              </div>
              <p className="section-note">Supervised models replicate K-Means-derived labels using the same six-feature space. High accuracy reflects consistency with derived profiles, not independent clinical validity.</p>
            </div>
          </SectionBlock>
        </div>

        <div className="dashboard-grid">
          <SectionBlock title="Confusion Matrix">
            <MetricTable headers={['Actual \ Predicted', 'High', 'Low', 'Medium']} rows={confusionRows} />
          </SectionBlock>
          <SectionBlock title="Interpretation">
            <p className="purpose-text">
              Of the {totalRecords.toLocaleString()} records classified as High Risk by the model,
              {data.confusion_matrix.find((r) => r.actual === 'High Risk')?.predicted_High_Risk.toLocaleString()}
              {' '}were correctly predicted. {data.confusion_matrix.find((r) => r.actual === 'High Risk')?.predicted_Low_Risk.toLocaleString()}
              {' '}were misclassified as Low Risk. Overall accuracy of the selected Logistic Regression model
              is {formatMetric(bestModel.accuracy, 4)}.
            </p>
          </SectionBlock>
        </div>

        <div className="dashboard-grid">
          <SectionBlock title="Performance Metrics">
            <div className="metrics-grid">
              <div className="metric-card">
                <span className="metric-card-label">Accuracy</span>
                <span className="metric-card-value">{formatMetric(bestModel.accuracy, 4)}</span>
              </div>
              <div className="metric-card">
                <span className="metric-card-label">Precision</span>
                <span className="metric-card-value">{formatMetric(bestModel.precision, 4)}</span>
              </div>
              <div className="metric-card">
                <span className="metric-card-label">Recall</span>
                <span className="metric-card-value">{formatMetric(bestModel.recall, 4)}</span>
              </div>
              <div className="metric-card">
                <span className="metric-card-label">F1</span>
                <span className="metric-card-value">{formatMetric(bestModel.f1, 4)}</span>
              </div>
            </div>
          </SectionBlock>
          <SectionBlock title="All Models">
            <div className="table-container">
              <table className="district-table">
                <thead>
                  <tr>
                    <th scope="col">Model</th>
                    <th scope="col">Accuracy</th>
                    <th scope="col">Precision</th>
                    <th scope="col">Recall</th>
                    <th scope="col">F1</th>
                    <th scope="col">ROC-AUC</th>
                  </tr>
                </thead>
                <tbody>
                  {modelRows.map((row, i) => (
                    <tr key={i}>
                      {row.map((cell, j) => (
                        <td key={j}>{cell}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </SectionBlock>
        </div>

        <SectionBlock title="SHAP / Global Feature Importance">
          {shapData.length > 0 && <FeatureBarChart data={shapData} />}
          <p className="section-note">
            SHAP (SHapley Additive exPlanations) values were computed on the Logistic Regression model to explain which features contributed
            to each classification decision. SHAP values indicate contribution direction and magnitude, not causation.
            Features are shown by mean absolute SHAP value across all predictions.
          </p>
        </SectionBlock>

        <SectionBlock title="Sensitivity / Robustness">
          <div className="table-container">
            <table className="district-table">
              <thead>
                <tr>
                  <th scope="col">Analysis</th>
                  <th scope="col">Features</th>
                  <th scope="col">Silhouette Score</th>
                  <th scope="col">High Risk Size</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Primary (6 features)</td>
                  <td>{data.sensitivity_analysis.primary_features}</td>
                  <td>{formatMetric(data.sensitivity_analysis.primary_silhouette, 6)}</td>
                  <td>—</td>
                </tr>
                <tr>
                  <td>Sensitivity (5 features, excluding Severe Anemia)</td>
                  <td>{data.sensitivity_analysis.sensitivity_features}</td>
                  <td>{formatMetric(data.sensitivity_analysis.sensitivity_silhouette, 6)}</td>
                  <td>{data.sensitivity_analysis.sensitivity_high_risk_size.toLocaleString()}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p className="section-note" style={{ marginTop: '1rem' }}>
            The five-feature analysis excluding Severe Anemia was used as a sensitivity analysis because Severe Anemia
            had cross-dataset harmonization uncertainty (D1 median 3.6% vs D2 median 51.5%). This is not a replacement
            for the primary model. The marginal difference in silhouette scores (0.231 vs 0.238) indicates robustness.
          </p>
        </SectionBlock>

        <SectionBlock title="Recent HMIS Evidence">
          {recentIndicators ? (
            <>
              <p className="section-note">
                Dataset 3 (2020–2025) extends the same MRCDSS system with current HMIS evidence, shown here as
                context alongside the historical analysis. Recent records are not assigned a risk class and were
                not used to retrain the historical model.
              </p>
              <MetricTable
                headers={['Indicator', 'Available', 'Missing', 'Status']}
                rows={recentIndicators.indicators.map((ind) => [
                  ind.name,
                  ind.valid.toLocaleString('en-US'),
                  ind.missing.toLocaleString('en-US'),
                  ind.status,
                ])}
              />
              <div className="callout-box">
                <p className="body-text">{recentIndicators.disclaimer}</p>
                {recentIndicators.harmonization.length > 0 && (
                  <ul className="harmonization-list">
                    {recentIndicators.harmonization.map((h) => (
                      <li key={h.indicator} className="harmonization-item">
                        <strong>{h.indicator}</strong>: {h.status} — {h.reason}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </>
          ) : (
            <p className="section-note">Recent HMIS indicator data is not available.</p>
          )}
        </SectionBlock>

        <SectionBlock title="Methodological Caveats">
          <div className="caveat-grid">
            <div className="caveat-item">
              <h4 className="caveat-heading">Risk Classes</h4>
              <p className="caveat-text">Derived from unsupervised K-Means clustering, not clinical diagnoses.</p>
            </div>
            <div className="caveat-item">
              <h4 className="caveat-heading">Supervised Models</h4>
              <p className="caveat-text">Replicate derived risk profiles, not independent clinical outcomes.</p>
            </div>
            <div className="caveat-item">
              <h4 className="caveat-heading">Feature Space</h4>
              <p className="caveat-text">Same features contribute to both label generation and classification, potentially inflating performance.</p>
            </div>
            <div className="caveat-item">
              <h4 className="caveat-heading">Severe Anemia</h4>
              <p className="caveat-text">Cross-dataset harmonization uncertainty (D1 median 3.6% vs D2 median 51.5%).</p>
            </div>
            <div className="caveat-item">
              <h4 className="caveat-heading">No External Validation</h4>
              <p className="caveat-text">Results are not validated against external clinical datasets.</p>
            </div>
            <div className="caveat-item">
              <h4 className="caveat-heading">SHAP Values</h4>
              <p className="caveat-text">Indicate model contribution, not causation.</p>
            </div>
            <div className="caveat-item">
              <h4 className="caveat-heading">Public-Health Planning</h4>
              <p className="caveat-text">For public-health planning support, not clinical diagnosis or treatment.</p>
            </div>
          </div>
        </SectionBlock>
      </main>
    </AppLayout>
  );
}

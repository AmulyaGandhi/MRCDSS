import { useState, useEffect } from 'react';
import AppLayout from '../components/AppLayout';
import TopBar from '../components/TopBar';
import SectionBlock from '../components/SectionBlock';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import { getMethodology } from '../api/methodology';

export default function Methodology() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<Array<{ category: string; title: string; value: string }> | null>(null);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      setError(null);
      try {
        const data = await getMethodology();
        setItems(data.items);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load methodology.');
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <AppLayout>
        <main className="content"><LoadingState /></main>
      </AppLayout>
    );
  }

  if (error || !items) {
    return (
      <AppLayout>
        <main className="content"><ErrorState message={error ?? 'No data available.'} onRetry={() => window.location.reload()} /></main>
      </AppLayout>
    );
  }

  const keyFacts = [
    { label: 'Records', value: '8,405' },
    { label: 'State–District Units', value: '707' },
    { label: 'States', value: '36' },
    { label: 'Coverage', value: '2008–2019' },
    { label: 'Final Features', value: '6' },
  ];

  const exclusions = [
    'IFA (Iron-Folic Acid) — excluded due to cross-dataset harmonization uncertainty (D1 and D2 use different tablet targets/coverage definitions)',
    'SBA Home Delivery — excluded because denominator definitions were not sufficiently comparable',
  ];

  const caveats = [
    'K-Means provides derived risk profiles, not clinical ground truth.',
    'Supervised models replicate derived profiles, not independent clinical outcomes.',
    'SHAP values indicate model contribution, not causation.',
    'Planning priorities are public-health guidance, not individual medical recommendations.',
  ];

  const pipelineSteps = [
    { step: 1, label: 'Data Source', description: 'NDAP/HMIS district-level maternal health records' },
    { step: 2, label: 'Preprocess', description: 'Data cleaning, validation, and transformation' },
    { step: 3, label: 'Feature Harmonization', description: '8 indicators → 6 validated features with cross-dataset comparability' },
    { step: 4, label: '6 Final Features', description: 'ANC First Trimester, TT2 Booster, Severe Anemia, Institutional Delivery, PNC 48h, Obstetric Complications' },
    { step: 5, label: 'K-Means Risk Profiling', description: 'Unsupervised clustering (K=3) on StandardScaler-normalized features' },
    { step: 6, label: 'Supervised ML Comparison', description: 'Logistic Regression, Decision Tree, Random Forest, XGBoost' },
    { step: 7, label: 'Logistic Regression', description: 'Selected model based on highest accuracy and balanced performance' },
    { step: 8, label: 'SHAP Explainability', description: 'SHAP values explain feature contribution direction and magnitude' },
    { step: 9, label: 'DSS Prioritization', description: 'Transparent rule-based mapping of risk classes to priority levels' },
    { step: 10, label: 'Planning Focus', description: 'Actionable planning focus areas from contributing factors and decision rules' },
  ];

  return (
    <AppLayout>
      <main className="content">
        <TopBar
          title="Methodology"
          subtitle="Understanding the analytical pipeline from raw data to decision support"
        />

        <SectionBlock title="System Facts">
          <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(5, 1fr)' }}>
            {keyFacts.map((fact) => (
              <div key={fact.label} className="kpi-card">
                <span className="kpi-label">{fact.label}</span>
                <span className="kpi-value">{fact.value}</span>
              </div>
            ))}
          </div>
        </SectionBlock>

        <SectionBlock title="One Unified MRCDSS System">
          <p className="section-note">
            Data set 1, data set 2, and data set 3 together form a single MRCDSS decision-support system that
            combines historical risk classification with newer district-level evidence.
          </p>
          <ul className="caveat-list">
            <li>Data set 1 + Data set 2 form the historical MRCDSS modelling period, producing the risk classifications shown on the district map.</li>
            <li>Data set 3 extends the system with newer HMIS evidence for the same districts.</li>
            <li>Data set 3 has not been used to retrain the historical model because several indicator definitions are not directly comparable across the periods.</li>
            <li>This is a methodological strength — historical risk classes remain stable while recent HMIS evidence adds current context — not a UI separation.</li>
          </ul>
        </SectionBlock>

        <SectionBlock title="Analytical Pipeline">
          <div className="pipeline-visual">
            {pipelineSteps.map((step, index) => (
              <div key={step.step} className="pipeline-step">
                <span className="pipeline-step-number">{step.step}</span>
                <div className="pipeline-step-content">
                  <span className="pipeline-step-title">{step.label}</span>
                </div>
                {index < pipelineSteps.length - 1 && (
                  <span className="pipeline-arrow" aria-hidden="true">↓</span>
                )}
              </div>
            ))}
          </div>
          <p className="section-note">
            Each step builds on the previous one, transforming raw data into actionable planning intelligence.
            SHAP values indicate model contribution, not causation.
          </p>
        </SectionBlock>

        <div className="dashboard-grid">
          <SectionBlock title="Excluded Features">
            <ul className="caveat-list">
              {exclusions.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </SectionBlock>
          <SectionBlock title="Caveats">
            <ul className="caveat-list">
              {caveats.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </SectionBlock>
        </div>

        <SectionBlock title="Methodology Detail">
          <div className="methodology-detail">
            {items.map((item) => (
              <div key={item.title} className="methodology-detail-item">
                <span className="methodology-detail-category">{item.category}</span>
                <span className="methodology-detail-title">{item.title}</span>
                <span className="methodology-detail-value">{item.value}</span>
              </div>
            ))}
          </div>
        </SectionBlock>
      </main>
    </AppLayout>
  );
}

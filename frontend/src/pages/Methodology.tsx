import { useState, useEffect } from 'react';
import AppLayout from '../components/AppLayout';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import { getMethodology } from '../api/methodology';
import { AlertTriangle } from 'lucide-react';

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
        <div className="content condensed"><LoadingState /></div>
      </AppLayout>
    );
  }

  if (error || !items) {
    return (
      <AppLayout>
        <div className="content condensed">
          <ErrorState message={error ?? 'No data available.'} onRetry={() => window.location.reload()} />
        </div>
      </AppLayout>
    );
  }

  const keyFacts = [
    { label: 'Historical Records', value: '8,405' },
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
    { step: 3, label: 'Feature Harmonization', description: '8 indicators → 6 selected features with cross-dataset comparability' },
    { step: 4, label: '6 Final Features', description: 'ANC First Trimester, TT2 Booster, Severe Anemia, Institutional Delivery, PNC 48h, Obstetric Complications' },
    { step: 5, label: 'K-Means Risk Profiling', description: 'Unsupervised clustering (K=3) on StandardScaler-normalized features' },
    { step: 6, label: 'Supervised ML Comparison', description: 'Logistic Regression, Decision Tree, Random Forest, XGBoost' },
    { step: 7, label: 'Logistic Regression', description: 'Selected model based on highest macro-F1' },
    { step: 8, label: 'SHAP Explainability', description: 'SHAP values explain global High Risk class attribution; not causation and not district-specific direction' },
    { step: 9, label: 'DSS Prioritization', description: 'Transparent rule-based mapping of risk classes to priority levels' },
    { step: 10, label: 'Planning Focus', description: 'Actionable planning focus areas from contributing factors and decision rules' },
  ];

  return (
    <AppLayout>
      <div className="content">
        <div className="page-header">
          <div className="page-header-main">
            <span className="page-kicker">Technical Documentation</span>
            <h1 className="page-title">Methodology</h1>
            <p className="page-subtitle">
              Understanding the analytical pipeline from raw data to decision support. All figures reflect the
              actual saved artifacts; no model is retrained at runtime.
            </p>
          </div>
        </div>

        <section className="section">
          <div className="card elevated">
            <div className="card-header">
              <h2 className="card-title">System Facts</h2>
            </div>
            <div className="card-body" style={{ paddingTop: 0 }}>
              <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(5, 1fr)', gap: 'var(--space-3)' }}>
                {keyFacts.map((fact) => (
                  <div key={fact.label} className="kpi-card" style={{ padding: 'var(--space-4)' }}>
                    <span className="kpi-label">{fact.label}</span>
                    <span className="kpi-value" style={{ fontSize: '1.7rem' }}>{fact.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="section">
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">One Unified MRCDSS System</h2>
            </div>
            <div className="card-body" style={{ paddingTop: 0 }}>
              <p className="note">
                Dataset 1 + Dataset 2 form the historical MRCDSS modelling period, producing the risk
                classifications shown on the district map. Dataset 3 extends the system with newer HMIS
                evidence for the same districts.
              </p>
              <ul className="caveat-list">
                <li>Data set 1 + Data set 2 form the historical MRCDSS modelling period, producing the risk classifications shown on the district map.</li>
                <li>Data set 3 extends the system with newer HMIS evidence for the same districts.</li>
                <li>Data set 3 has not been used to retrain the historical model because several indicator definitions are not directly comparable across the periods.</li>
                <li>This keeps historical risk classes stable while recent HMIS evidence adds current context.</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="section">
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Analytical Pipeline</h2>
            </div>
            <div className="card-body" style={{ paddingTop: 0 }}>
              <div className="pipeline-visual">
                {pipelineSteps.map((step, index) => (
                  <div key={step.step} className="pipeline-step">
                    <span className="pipeline-step-number">{step.step}</span>
                    <div className="pipeline-step-content">
                      <span className="pipeline-step-title">{step.label}</span>
                      <span className="pipeline-step-description">{step.description}</span>
                    </div>
                    {index < pipelineSteps.length - 1 && (
                      <span className="pipeline-arrow" aria-hidden="true">→</span>
                    )}
                  </div>
                ))}
              </div>
              <p className="section-note" style={{ marginTop: 'var(--space-4)' }}>
                Each step builds on the previous one, transforming raw data into actionable planning
                intelligence. SHAP values indicate model contribution, not causation.
              </p>
            </div>
          </div>
        </section>

        <div className="grid-2">
          <section className="section">
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Excluded Features</h2>
              </div>
              <div className="card-body" style={{ paddingTop: 0 }}>
                <ul className="caveat-list">
                  {exclusions.map((item) => <li key={item}>{item}</li>)}
                </ul>
              </div>
            </div>
          </section>
          <section className="section">
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Caveats</h2>
                <span className="badge badge-outline" style={{ fontSize: '0.75rem' }}>
                  Read before interpreting
                </span>
              </div>
              <div className="card-body" style={{ paddingTop: 0 }}>
                <ul className="caveat-list">
                  {caveats.map((item) => <li key={item}>{item}</li>)}
                </ul>
              </div>
            </div>
          </section>
        </div>

        <section className="section">
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Methodology Detail</h2>
            </div>
            <div className="card-body" style={{ paddingTop: 0 }}>
              <div className="methodology-detail">
                {items.map((item) => (
                  <div key={item.title} className="methodology-detail-item">
                    <span className="methodology-detail-category">{item.category}</span>
                    <span className="methodology-detail-title">{item.title}</span>
                    <span className="methodology-detail-value">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="section">
          <div className="card callout info" style={{ padding: 'var(--space-5)' }}>
            <div className="flex-between" style={{ alignItems: 'flex-start' }}>
              <div>
                <h2 className="card-title" style={{ fontSize: 'var(--fs-lg)', marginBottom: 'var(--space-1)' }}>
                  <AlertTriangle size={20} strokeWidth={2} style={{ marginRight: 'var(--space-2)' }} /> Intended Use & Limitations
                </h2>
                <p className="note text-small" style={{ margin: 0, lineHeight: 1.7 }}>
                  MRCDSS is a research prototype for district-level public-health planning support. Risk classes
                  are derived analytical groups, not clinical diagnoses. Supervised metrics reproduce derived
                  labels on seen units — there is no external clinical validation. SHAP indicates model
                  contribution, not causation. Recent HMIS evidence is contextual and was not used to retrain
                  the model. Do not use this system for clinical decisions or as evidence of predictive
                  performance.
                </p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AppLayout>
  );
}

import AppLayout from '../components/AppLayout';
import { Info } from 'lucide-react';

export default function About() {
  return (
    <AppLayout>
      <div className="content">
        <div className="page-header">
          <div className="page-header-main">
            <span className="page-kicker">System Information</span>
            <h1 className="page-title">About MRCDSS</h1>
            <p className="page-subtitle">
              The District-Level Maternal Health Risk Decision Support System (MRCDSS) supports public-health
              planning teams in understanding district-level maternal health risk patterns. Risk classes are
              derived analytical groups, not clinical diagnoses.
            </p>
          </div>
        </div>

        <section className="section">
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">System Purpose</h2>
            </div>
            <div className="card-body" style={{ paddingTop: 0 }}>
              <p className="note">
                MRCDSS analyzes district-year maternal health indicators to derive risk profiles, identify
                priority areas, and inform resource allocation decisions. It is designed for district health
                planning, not to provide clinical diagnoses or individual medical advice.
              </p>
            </div>
          </div>
        </section>

        <div className="grid-2">
          <section className="section">
            <div className="card">
              <div className="card-header">
                <div className="flex-between" style={{ alignItems: 'center' }}>
                  <h2 className="card-title">Intended Users</h2>
                  <span className="badge badge-outline">
                    Public-health planning
                  </span>
                </div>
              </div>
              <div className="card-body" style={{ paddingTop: 0 }}>
                <ul className="caveat-list">
                  <li>Public-health planning teams at state and district levels</li>
                  <li>Health program managers and policymakers</li>
                  <li>Maternal-health researchers and analysts</li>
                  <li>Government officials responsible for health resource allocation</li>
                </ul>
              </div>
            </div>
          </section>
          <section className="section">
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Data Source</h2>
              </div>
              <div className="card-body" style={{ paddingTop: 0 }}>
                <p className="note">
                  District-level maternal health data from NDAP/HMIS sources covering 8,405 district-year
                  records across 707 state-district units in 36 states, spanning 2008–2019. A Recent HMIS
                  extension (Dataset 3, 2020–2025) adds 3,306 contextual indicator observations across 812
                  units.
                </p>
              </div>
            </div>
          </section>
        </div>

        <section className="section">
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Technology Stack</h2>
            </div>
            <div className="card-body" style={{ paddingTop: 0 }}>
              <div className="tech-stack" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
                <div className="tech-item">
                  <span className="tech-label">Frontend</span>
                  <span className="tech-value">React + TypeScript + Vite</span>
                </div>
                <div className="tech-item">
                  <span className="tech-label">Backend</span>
                  <span className="tech-value">FastAPI (Python)</span>
                </div>
                <div className="tech-item">
                  <span className="tech-label">Data Processing</span>
                  <span className="tech-value">pandas, scikit-learn</span>
                </div>
                <div className="tech-item">
                  <span className="tech-label">Clustering</span>
                  <span className="tech-value">K-Means (K=3)</span>
                </div>
                <div className="tech-item">
                  <span className="tech-label">ML Models</span>
                  <span className="tech-value">Logistic Regression, Decision Tree, Random Forest, XGBoost</span>
                </div>
                <div className="tech-item">
                  <span className="tech-label">Explainability</span>
                  <span className="tech-value">SHAP</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="section">
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Limitations</h2>
              <span className="badge badge-outline">
                Disclosed
              </span>
            </div>
            <div className="card-body" style={{ paddingTop: 0 }}>
              <ul className="caveat-list">
                <li>Risk classes are derived from unsupervised clustering and are not clinical diagnoses.</li>
                <li>SHAP values explain model contribution, not causal relationships.</li>
                <li>Supervised models replicate derived profiles, not independent clinical outcomes.</li>
                <li>IFA and SBA Home Delivery were excluded due to cross-dataset harmonization issues.</li>
                <li>Planning priorities are public-health planning guidance, not individual medical recommendations.</li>
                <li>No external clinical validation exists; recent HMIS is contextual evidence only.</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="section">
          <div className="card callout info" style={{ padding: 'var(--space-5)' }}>
            <div className="flex-between" style={{ alignItems: 'flex-start' }}>
              <div>
                <h2 className="card-title" style={{ fontSize: 'var(--fs-lg)', marginBottom: 'var(--space-1)' }}>
                  <Info size={20} strokeWidth={2} style={{ marginRight: 'var(--space-2)' }} /> Disclaimer
                </h2>
                <p className="note text-small" style={{ margin: 0, lineHeight: 1.7 }}>
                  This system supports district-level public-health planning. Risk classes are derived from HMIS
                  indicators and are not clinical diagnoses or individual medical recommendations. This is a
                  public-health planning Decision Support System, not a clinical diagnosis or treatment system.
                </p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AppLayout>
  );
}

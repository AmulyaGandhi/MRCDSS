import AppLayout from '../components/AppLayout';
import TopBar from '../components/TopBar';
import SectionBlock from '../components/SectionBlock';

export default function About() {
  return (
    <AppLayout>
      <main className="content">
        <TopBar
          title="About"
          subtitle="System information, purpose, and limitations"
        />

        <SectionBlock title="System Purpose">
          <p className="body-text">
            The District-Level Maternal Health Risk Decision Support System (MRCDSS) supports public-health
            planning teams in understanding district-level maternal health risk patterns. It analyzes district-year
            maternal health indicators to derive risk profiles, identify priority areas, and inform resource
            allocation decisions. Risk classes are derived analytical groups, not clinical diagnoses.
          </p>
        </SectionBlock>

        <div className="dashboard-grid">
          <SectionBlock title="Intended Users">
            <ul className="caveat-list">
              <li>Public-health planning teams at state and district levels</li>
              <li>Health program managers and policymakers</li>
              <li>Maternal-health researchers and analysts</li>
              <li>Government officials responsible for health resource allocation</li>
            </ul>
          </SectionBlock>
          <SectionBlock title="Data Source">
            <p className="body-text">
              District-level maternal health data from NDAP/HMIS sources covering 8,405 district-year
              records across 707 state-district units in 36 states, spanning 2008–2019.
            </p>
          </SectionBlock>
        </div>

        <SectionBlock title="Technology Stack">
          <div className="tech-stack">
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
        </SectionBlock>

        <SectionBlock title="Limitations">
          <ul className="caveat-list">
            <li>Risk classes are derived from unsupervised clustering and are not clinical diagnoses.</li>
            <li>SHAP values explain model contribution, not causal relationships.</li>
            <li>Supervised models replicate derived profiles, not independent clinical outcomes.</li>
            <li>IFA and SBA Home Delivery were excluded due to cross-dataset harmonization issues.</li>
            <li>Planning priorities are public-health planning guidance, not individual medical recommendations.</li>
          </ul>
        </SectionBlock>

        <SectionBlock title="Disclaimer">
          <p className="disclaimer-text">
            This system supports district-level public-health planning. Risk classes are derived from
            HMIS indicators and are not clinical diagnoses or individual medical recommendations. This
            is a public-health planning Decision Support System, not a clinical diagnosis or treatment system.
          </p>
        </SectionBlock>
      </main>
    </AppLayout>
  );
}

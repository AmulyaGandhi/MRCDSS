import type { DistrictDetail } from '../types';

interface RiskSummaryProps {
  detail: DistrictDetail;
}

export default function RiskSummary({ detail }: RiskSummaryProps) {
  return (
    <section className="section">
      <h2 className="section-title">Risk Summary</h2>
      <dl className="risk-summary-list">
        <div className="risk-summary-item">
          <dt>Risk Class</dt>
          <dd>
            <span className={`priority-badge badge-${detail.riskClass.toLowerCase()}`}>
              {detail.riskClass} Risk
            </span>
          </dd>
        </div>
        <div className="risk-summary-item">
          <dt>Priority Level</dt>
          <dd>
            <span className={`priority-badge badge-${detail.priority.toLowerCase()}`}>
              {detail.priority} Priority
            </span>
          </dd>
        </div>
        <div className="risk-summary-item">
          <dt>Year</dt>
          <dd className="risk-summary-year">{detail.year}</dd>
        </div>
        <div className="risk-summary-item risk-mapping">
          <dt>Mapping</dt>
          <dd>{detail.riskClass} Risk &rarr; {detail.priority} Priority</dd>
        </div>
      </dl>
    </section>
  );
}

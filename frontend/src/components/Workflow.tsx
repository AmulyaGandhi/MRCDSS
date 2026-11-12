import { workflowSteps } from '../data/overviewData';

export default function Workflow() {
  return (
    <section className="section">
      <h2 className="section-title">System Workflow</h2>
      <ol className="workflow-list">
        {workflowSteps.map((item) => (
          <li className="workflow-step" key={item.step}>
            <span className="workflow-step-number">{item.step}</span>
            <span className="workflow-step-label">{item.label}</span>
            {item.step < workflowSteps.length && (
              <span className="workflow-arrow" aria-hidden="true">→</span>
            )}
          </li>
        ))}
      </ol>
    </section>
  );
}

interface PlanningFocusProps {
  priorities: string[];
}

export default function PlanningFocus({ priorities }: PlanningFocusProps) {
  return (
    <section className="section">
      <h2 className="section-title">Planning Focus</h2>
      <ol className="planning-list">
        {priorities.map((priority, index) => (
          <li key={`${priority}-${index}`} className="planning-item">
            <span className="planning-number" aria-hidden="true">{index + 1}</span>
            <span className="planning-text">{priority}</span>
          </li>
        ))}
      </ol>
      <p className="planning-disclaimer">
        Planning priorities are derived from DSS rules based on HMIS indicators. They are not individual medical advice or treatment recommendations.
      </p>
    </section>
  );
}

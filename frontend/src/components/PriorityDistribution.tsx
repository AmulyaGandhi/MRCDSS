interface PriorityInfo {
  riskClass: string;
  priorityLevel: string;
  count: number;
}

interface PriorityDistributionProps {
  data: PriorityInfo[];
}

export default function PriorityDistribution({ data }: PriorityDistributionProps) {
  const total = data.reduce((sum, d) => sum + d.count, 0);

  return (
    <section className="section">
      <h2 className="section-title">Priority Overview</h2>
      <p className="section-note">Risk Class → Priority Level</p>
      <ul className="priority-list">
        {data.map((item) => {
          const percentage = ((item.count / total) * 100).toFixed(1);
          return (
            <li className="priority-item" key={item.priorityLevel}>
              <div className="priority-header">
                <span className="priority-label">{item.priorityLevel}</span>
                <span className="priority-count">{item.count.toLocaleString()}</span>
              </div>
              <div className="priority-mapping">
                <span className="priority-risk">{item.riskClass}</span>
                <span className="priority-arrow">→</span>
                <span className="priority-level">{item.priorityLevel}</span>
              </div>
              <div className="priority-bar-track">
                <div
                  className="priority-bar-fill"
                  style={{ width: `${percentage}%` }}
                  aria-label={`${item.priorityLevel}: ${percentage}%`}
                  role="progressbar"
                  aria-valuenow={Number(percentage)}
                  aria-valuemin={0}
                  aria-valuemax={100}
                />
              </div>
              <span className="priority-percentage">{percentage}%</span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

interface KpiCardProps {
  label: string;
  value: string;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
}

export default function KpiCard({ label, value, change, changeType }: KpiCardProps) {
  return (
    <div className="kpi-card">
      <span className="kpi-label">{label}</span>
      <span className="kpi-value">{value}</span>
      {change && (
        <span className={`kpi-change ${changeType ? `kpi-change-${changeType}` : ''}`}>
          {change}
        </span>
      )}
    </div>
  );
}

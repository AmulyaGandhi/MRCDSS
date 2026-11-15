interface KpiCardProps {
  label: string;
  value: string;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon?: React.ReactNode;
}

export default function KpiCard({
  label,
  value,
  change,
  changeType,
  icon,
}: KpiCardProps) {
  return (
    <div className="kpi-card">
      <div className="kpi-head">
        <span className="kpi-label">{label}</span>
        {icon && <span className="kpi-icon">{icon}</span>}
      </div>
      <span className="kpi-value">{value}</span>
      {change && (
        <span className={`kpi-delta ${changeType ? `kpi-delta-${changeType}` : 'kpi-delta-neutral'}`}>
          {change}
        </span>
      )}
    </div>
  );
}

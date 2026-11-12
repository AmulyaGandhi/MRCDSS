import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface Props {
  title: string;
  bins: Array<{ label: string; count: number }>;
  totalValues: number;
}

export default function IndicatorDistributionChart({ title, bins, totalValues }: Props) {
  const payload = bins.map((b) => ({ name: b.label, count: b.count }));
  return (
    <div className="indicator-distribution">
      <div className="indicator-distribution-title">{title}</div>
      <div className="indicator-distribution-note">
        Distribution across {totalValues.toLocaleString('en-US')} non-missing district-year values
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={payload} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#ecf0f1" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} axisLine={{ stroke: '#d5dbdb' }} interval={0} angle={-45} textAnchor="end" height={48} />
          <YAxis tick={{ fontSize: 11 }} axisLine={{ stroke: '#d5dbdb' }} allowDecimals={false} />
          <Tooltip formatter={(value) => [value, 'District-year values']} />
          <Bar dataKey="count" fill="#1a5276" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
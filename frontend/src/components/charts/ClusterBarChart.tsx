import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface ClusterBarProps {
  data: Array<Record<string, number | string>>;
}

export default function ClusterBarChart({ data }: ClusterBarProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#ecf0f1" />
        <XAxis dataKey="cluster" tick={{ fontSize: 12 }} axisLine={{ stroke: '#d5dbdb' }} />
        <YAxis tick={{ fontSize: 12 }} axisLine={{ stroke: '#d5dbdb' }} />
        <Tooltip formatter={(value) => (value as number)?.toFixed(1) ?? ''} />
        <Bar dataKey="ANC First Trimester" fill="#2e86c1" radius={[4, 4, 0, 0]} />
        <Bar dataKey="TT2 Booster" fill="#1a5276" radius={[4, 4, 0, 0]} />
        <Bar dataKey="Severe Anemia" fill="#e67e22" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

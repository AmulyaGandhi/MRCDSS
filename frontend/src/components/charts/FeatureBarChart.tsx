import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface FeatureBarProps {
  data: Array<{ name: string; value: number }>;
}

export default function FeatureBarChart({ data }: FeatureBarProps) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} layout="vertical" margin={{ top: 10, right: 30, left: 80, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#ecf0f1" />
        <XAxis type="number" tick={{ fontSize: 12 }} axisLine={{ stroke: '#d5dbdb' }} />
        <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} width={80} axisLine={{ stroke: '#d5dbdb' }} />
        <Tooltip formatter={(value) => (value as number)?.toFixed(2) ?? ''} />
        <Bar dataKey="value" fill="#1a5276" radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

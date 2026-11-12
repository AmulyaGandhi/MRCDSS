import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface PriorityBarProps {
  data: Array<{ name: string; value: number }>;
}

export default function PriorityBarChart({ data }: PriorityBarProps) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#ecf0f1" />
        <XAxis dataKey="name" tick={{ fontSize: 12 }} axisLine={{ stroke: '#d5dbdb' }} />
        <YAxis tick={{ fontSize: 12 }} axisLine={{ stroke: '#d5dbdb' }} />
        <Tooltip formatter={(value) => (value as number)?.toLocaleString() ?? ''} />
        <Bar dataKey="value" fill="#2e86c1" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

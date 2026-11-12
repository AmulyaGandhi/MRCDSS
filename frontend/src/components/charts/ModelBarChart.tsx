import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface ModelBarProps {
  data: Array<Record<string, number | string>>;
}

export default function ModelBarChart({ data }: ModelBarProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#ecf0f1" />
        <XAxis dataKey="model" tick={{ fontSize: 11 }} axisLine={{ stroke: '#d5dbdb' }} />
        <YAxis tick={{ fontSize: 12 }} domain={[0.9, 1]} axisLine={{ stroke: '#d5dbdb' }} />
        <Tooltip formatter={(value) => (value as number)?.toFixed(4) ?? ''} />
        <Bar dataKey="Accuracy" fill="#2e86c1" radius={[4, 4, 0, 0]} />
        <Bar dataKey="F1" fill="#1a5276" radius={[4, 4, 0, 0]} />
        <Bar dataKey="ROC-AUC" fill="#27ae60" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

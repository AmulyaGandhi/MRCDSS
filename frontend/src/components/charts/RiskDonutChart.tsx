import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';

interface RiskDonutProps {
  data: Array<{ name: string; value: number }>;
}

const COLORS = ['#27ae60', '#f39c12', '#e74c3c'];

export default function RiskDonutChart({ data }: RiskDonutProps) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          cx="50%"
          cy="50%"
          outerRadius={90}
          label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
        >
          {data.map((_, index) => (
            <Cell key={index} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip formatter={(value) => (value as number)?.toLocaleString() ?? ''} />
      </PieChart>
    </ResponsiveContainer>
  );
}

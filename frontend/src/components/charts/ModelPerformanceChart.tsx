import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export interface ModelPerformanceDatum {
  model: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
}

interface ModelPerformanceChartProps {
  data: ModelPerformanceDatum[];
}

const series = [
  { key: 'accuracy', label: 'Accuracy', color: '#1f4e79' },
  { key: 'precision', label: 'Precision', color: '#4e92c4' },
  { key: 'recall', label: 'Recall', color: '#5aa469' },
  { key: 'f1', label: 'F1-score', color: '#d98e32' },
] as const;

const INK = '#1f2a37';
const INK_2 = '#46505c';
const AXIS_LINE = '#cfd7e0';
const GRID = '#e8edf3';

function toPercent(value: number): number {
  return Math.round(value * 10000) / 100;
}

function formatPercent(value: number): string {
  return `${value.toFixed(2)}%`;
}

export default function ModelPerformanceChart({ data }: ModelPerformanceChartProps) {
  const chartData = data.map((m) => ({
    model: m.model,
    accuracy: toPercent(m.accuracy),
    precision: toPercent(m.precision),
    recall: toPercent(m.recall),
    f1: toPercent(m.f1),
  }));

  return (
    <ResponsiveContainer width="100%" height={340}>
      <BarChart
        data={chartData}
        margin={{ top: 12, right: 16, left: 4, bottom: 4 }}
        barGap={2}
        barCategoryGap="18%"
        maxBarSize={30}
        style={{ backgroundColor: '#ffffff' }}
      >
        <CartesianGrid stroke={GRID} strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="model"
          tick={{ fontSize: 11, fill: INK_2 }}
          tickLine={false}
          axisLine={{ stroke: AXIS_LINE }}
          interval={0}
        />
        <YAxis
          domain={[0, 100]}
          ticks={[0, 20, 40, 60, 80, 100]}
          tick={{ fontSize: 11, fill: INK_2 }}
          tickLine={false}
          axisLine={{ stroke: AXIS_LINE }}
          tickFormatter={(value) => `${value}%`}
          label={{
            value: 'Performance (%)',
            angle: -90,
            position: 'insideLeft',
            style: { fontSize: 11, fill: '#7b8694' },
          }}
        />
        <Tooltip
          cursor={{ fill: 'rgba(31, 42, 55, 0.05)' }}
          contentStyle={{
            background: '#ffffff',
            border: '1px solid #e3e8ee',
            borderRadius: 4,
            fontSize: 12,
            color: INK,
            boxShadow: 'none',
          }}
          labelStyle={{ color: INK, fontWeight: 600 }}
          formatter={(value) => formatPercent(value as number)}
        />
        <Legend
          wrapperStyle={{ fontSize: 12, color: INK_2, paddingTop: 8 }}
          iconType="square"
          iconSize={10}
        />
        {series.map((s) => (
          <Bar
            key={s.key}
            dataKey={s.key}
            name={s.label}
            fill={s.color}
            isAnimationActive={false}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

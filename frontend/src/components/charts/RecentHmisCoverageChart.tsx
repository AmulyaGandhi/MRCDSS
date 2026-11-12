import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer } from 'recharts';

interface CoverageDatum {
  fiscal_year: string;
  observations: number;
  states: number;
  partial: boolean;
}

interface Props {
  data: CoverageDatum[];
}

const fullColor = '#1a5276';
const partialColor = '#7f8c8d';

export default function RecentHmisCoverageChart({ data }: Props) {
  const payload = data.map((d) => ({
    fiscal_year: d.fiscal_year,
    observations: d.observations,
    states: d.states,
    partial: d.partial,
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={payload} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#ecf0f1" vertical={false} />
        <XAxis dataKey="fiscal_year" tick={{ fontSize: 12 }} axisLine={{ stroke: '#d5dbdb' }} />
        <YAxis tick={{ fontSize: 12 }} axisLine={{ stroke: '#d5dbdb' }} allowDecimals={false} />
        <Tooltip
          content={({ active, payload: tooltipPayload }) => {
            if (!active || !tooltipPayload || tooltipPayload.length === 0) return null;
            const row = tooltipPayload[0].payload as (typeof payload)[number];
            return (
              <div className="chart-tooltip">
                <div><strong>{row.fiscal_year}</strong></div>
                <div>Observations: {row.observations.toLocaleString('en-US')}</div>
                <div>States: {row.states}</div>
                <div>{row.partial ? 'Partial coverage (UpTo_Mar files for 17 states)' : 'Complete annual coverage'}</div>
              </div>
            );
          }}
        />
        <Bar dataKey="observations" radius={[4, 4, 0, 0]}>
          {payload.map((entry) => (
            <Cell key={entry.fiscal_year} fill={entry.partial ? partialColor : fullColor} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
import type { HealthIndicator } from '../types';

interface HealthIndicatorsProps {
  indicators: HealthIndicator[];
}

export default function HealthIndicators({ indicators }: HealthIndicatorsProps) {
  return (
    <section className="section">
      <h2 className="section-title">Maternal Health Indicators</h2>
      <table className="indicators-table">
        <thead>
          <tr>
            <th scope="col">Indicator</th>
            <th scope="col">Value</th>
            <th scope="col">Interpretation</th>
          </tr>
        </thead>
        <tbody>
          {indicators.map((indicator) => (
            <tr key={indicator.name}>
              <td>{indicator.name}</td>
              <td>
                <span className="indicator-value">
                  {indicator.value}{indicator.unit}
                </span>
              </td>
              <td>{indicator.interpretation}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

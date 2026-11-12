import type { HealthIndicator } from '../types';

interface HealthIndicatorsProps {
  indicators: HealthIndicator[];
}

function getInterpretationClass(value: number, name: string): string {
  if (name === 'Severe Anemia' || name === 'Obstetric Complications') {
    return value <= 15 ? 'indicator-good' : value <= 25 ? 'indicator-moderate' : 'indicator-concerning';
  }
  return value >= 50 ? 'indicator-good' : value >= 30 ? 'indicator-moderate' : 'indicator-concerning';
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
                <span className={`indicator-value ${getInterpretationClass(indicator.value, indicator.name)}`}>
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

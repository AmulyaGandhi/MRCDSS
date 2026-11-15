interface ContributingFactorDisplay {
  feature: string;
  value?: number;
  direction?: 'positive' | 'negative';
  explanation?: string;
}

interface ContributingFactorsProps {
  factors: ContributingFactorDisplay[];
}

export default function ContributingFactors({ factors }: ContributingFactorsProps) {
  return (
    <section className="section">
      <h2 className="section-title">Model Contributing Factors</h2>
      <p className="section-note">
        SHAP values indicate how features contributed to the model&apos;s classification; they do not establish causation.
      </p>
      <ol className="factors-list">
        {factors.map((factor, index) => (
          <li key={factor.feature} className="factor-item">
            <span className="factor-rank">{index + 1}</span>
            <div className="factor-content">
              <span className="factor-name">{factor.feature}</span>
              {factor.direction && (
                <span className="factor-direction">
                  {factor.direction === 'positive' ? 'Pushes toward High Risk' : 'Pushes away from High Risk'}
                </span>
              )}
              {factor.value !== undefined && (
                <span className="factor-value">SHAP: {factor.value.toFixed(2)}</span>
              )}
              {factor.explanation && (
                <span className="factor-explanation">{factor.explanation}</span>
              )}
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}

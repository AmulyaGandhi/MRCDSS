import type { FeatureRank } from '../types';

interface FeatureRankingProps {
  data: FeatureRank[];
}

export default function FeatureRanking({ data }: FeatureRankingProps) {
  return (
    <section className="section">
      <h2 className="section-title">Top Contributing Indicators</h2>
      <p className="section-note">SHAP-derived global feature ranking</p>
      <ol className="ranking-list">
        {data.map((item) => (
          <li className="ranking-item" key={item.variableName}>
            <span className="ranking-number" aria-hidden="true">{item.rank}</span>
            <span className="ranking-name">{item.displayName}</span>
            <span className="ranking-variable" aria-label={`Variable: ${item.variableName}`}>
              {item.variableName}
            </span>
          </li>
        ))}
      </ol>
    </section>
  );
}

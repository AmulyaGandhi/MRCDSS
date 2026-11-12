

export default function MethodologyContext() {
  return (
    <section className="section">
      <h2 className="section-title">Methodology Context</h2>
      <dl className="methodology-list">
        <div className="methodology-item">
          <dt>Risk Profile Derivation</dt>
          <dd>K-Means clustering</dd>
        </div>
        <div className="methodology-item">
          <dt>Supervised Models Evaluated</dt>
          <dd>Logistic Regression, Decision Tree, Random Forest, XGBoost</dd>
        </div>
        <div className="methodology-item">
          <dt>Selected Model</dt>
          <dd>Logistic Regression</dd>
        </div>
        <div className="methodology-item">
          <dt>Explainability</dt>
          <dd>SHAP</dd>
        </div>
        <div className="methodology-item">
          <dt>DSS</dt>
          <dd>Risk classification + contributing factors &rarr; district priority / planning focus</dd>
        </div>
      </dl>
    </section>
  );
}

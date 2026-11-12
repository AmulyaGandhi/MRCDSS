interface TopBarProps {
  title: string;
  subtitle?: string;
  meta?: string[];
}

export default function TopBar({ title, subtitle, meta }: TopBarProps) {
  return (
    <header className="topbar">
      <div className="topbar-content">
        <div className="topbar-head">
          <h1 className="topbar-title">{title}</h1>
          {meta && meta.length > 0 && (
            <div className="topbar-meta">
              {meta.map((m, i) => (
                <span key={i} className="topbar-meta-item">
                  {i > 0 && <span className="topbar-meta-sep" aria-hidden="true">•</span>}
                  <span className="topbar-meta-text">{m}</span>
                </span>
              ))}
            </div>
          )}
        </div>
        {subtitle && <p className="topbar-subtitle">{subtitle}</p>}
      </div>
    </header>
  );
}
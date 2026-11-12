import { NavLink } from 'react-router-dom';

const navItems = [
  { to: '/', label: 'Overview', end: true },
  { to: '/districts', label: 'District Explorer' },
  { to: '/risk-analysis', label: 'Risk Analysis' },
  { to: '/planning', label: 'Planning Priorities' },
  { to: '/methodology', label: 'Methodology' },
  { to: '/about', label: 'About' },
];

export default function AppHeader() {
  return (
    <header className="app-header">
      <div className="header-inner">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true" />
          <div className="brand-text">
            <span className="brand-name">MRCDSS</span>
            <span className="brand-tag">Maternal Health Decision Support</span>
          </div>
        </div>
        <nav className="topnav" aria-label="Primary">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `topnav-link${isActive ? ' active' : ''}`}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}
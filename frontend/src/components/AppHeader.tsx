import { NavLink, useNavigate } from 'react-router-dom';
import { Shield } from 'lucide-react';

export default function AppHeader() {
  const navigate = useNavigate();

  return (
    <header className="app-header" role="banner">
      <div className="header-inner">
        <nav className="topnav" aria-label="Primary">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `topnav-link${isActive ? ' active' : ''}`
            }
          >
            <Shield size={16} strokeWidth={2} />
            <span>MRCDSS</span>
          </NavLink>
        </nav>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => navigate('/about')}
            title="About"
            aria-label="About MRCDSS"
          >
            About
          </button>
        </div>
      </div>
    </header>
  );
}

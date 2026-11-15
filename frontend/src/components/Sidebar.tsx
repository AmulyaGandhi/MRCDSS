import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  BarChart3,
  List,
  HelpCircle,
  Shield,
  Activity,
  Menu,
  X,
  ChevronRight,
  MapPin,
} from 'lucide-react';

const navItems = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/districts', label: 'District Explorer', icon: MapPin },
  { to: '/risk-analysis', label: 'Risk Analysis', icon: BarChart3 },
  { to: '/planning', label: 'Planning Priorities', icon: List },
  { to: '/methodology', label: 'Methodology', icon: Activity },
  { to: '/about', label: 'About', icon: HelpCircle },
];

export default function Sidebar() {
  const location = useLocation();
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        className="mobile-menu-toggle"
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? 'Close navigation' : 'Open navigation'}
        aria-expanded={open}
      >
        {open ? <X size={18} strokeWidth={2} /> : <Menu size={18} strokeWidth={2} />}
      </button>
      {open && <div className="sidebar-backdrop visible" onClick={() => setOpen(false)} />}
      <aside
        className={`sidebar ${open ? 'open' : ''}`}
        aria-label="Primary navigation"
      >
        <div className="sidebar-inner">
          <div className="sidebar-brand">
            <span className="brand-mark" aria-hidden="true">
              <Shield size={20} strokeWidth={2.5} />
            </span>
            <div className="brand-text">
              <span className="brand-name">MRCDSS</span>
              <span className="brand-tag">Maternal Health Decision Support</span>
            </div>
          </div>
          <nav className="sidebar-nav">
            <div className="sidebar-section">
              <div className="sidebar-label">Dashboard</div>
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.to ||
                  (item.to !== '/' && location.pathname.startsWith(item.to));
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.to === '/'}
                    className={({ isActive }) =>
                      `sidebar-item${isActive ? ' active' : ''}`
                    }
                    onClick={() => setOpen(false)}
                  >
                    <Icon size={18} strokeWidth={2} />
                    <span>{item.label}</span>
                    {isActive && <ChevronRight size={14} strokeWidth={2} />}
                  </NavLink>
                );
              })}
            </div>
          </nav>
          <div className="sidebar-footer">
            District-Level Maternal Health Risk Decision Support System —
            research prototype. Not a clinical diagnostic tool.
          </div>
        </div>
      </aside>
    </>
  );
}

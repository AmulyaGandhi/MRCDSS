import { ReactNode } from 'react';
import Sidebar from './Sidebar';
import AppHeader from './AppHeader';

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-body">
        <div className="app-main">
          <AppHeader />
          <div className="content">{children}</div>
        </div>
      </div>
    </div>
  );
}

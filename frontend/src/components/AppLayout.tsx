import { ReactNode } from 'react';
import AppHeader from './AppHeader';

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <AppHeader />
      <div className="app-main">
        {children}
      </div>
    </div>
  );
}
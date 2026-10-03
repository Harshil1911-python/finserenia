/**
 * SERENIA ACCOUNTING — components/layout/AppLayout.tsx
 * =======================================================
 * Wraps all authenticated pages with Sidebar + Topbar.
 */

import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';

export const AppLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-surface-50 dark:bg-surface-dark">
      <Sidebar collapsed={collapsed} />
      <div className={`transition-all duration-200 ${collapsed ? 'ml-sidebar-collapsed' : 'ml-sidebar'}`}>
        <Topbar onToggleSidebar={() => setCollapsed((c) => !c)} />
        <main className="p-4 lg:p-6 max-w-[1600px] mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

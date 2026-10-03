/**
 * SERENIA ACCOUNTING — App.tsx
 * ===============================
 * Root application component: routing, providers, protected routes.
 */

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { AppLayout } from './components/layout/AppLayout';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';

// Lazy-loaded route placeholders — implement progressively.
import { LedgerList } from './pages/ledger/LedgerList';
import { ChartOfAccounts } from './pages/ledger/ChartOfAccounts';
import { JournalList } from './pages/ledger/JournalList';
import { VoucherForm } from './pages/vouchers/VoucherForm';
import { TrialBalanceReport } from './pages/reports/TrialBalanceReport';
import { ProfitAndLossReport } from './pages/reports/ProfitAndLossReport';
import { BalanceSheetReport } from './pages/reports/BalanceSheetReport';
import { DeveloperMode } from './pages/developer/DeveloperMode';
import { CompaniesPage } from './pages/companies/CompaniesPage';
import { SettingsPage } from './pages/settings/SettingsPage';
import { NotFound } from './pages/NotFound';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface-50 dark:bg-surface-dark">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-500 to-teal-500 flex items-center justify-center text-white font-bold animate-pulse">S</div>
          <p className="text-sm text-surface-300">Loading Serenia...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

const SuperAdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  if (user?.role !== 'super_admin') {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
};

const AppRoutes: React.FC = () => (
  <Routes>
    <Route path="/login" element={<Login />} />

    <Route
      path="/"
      element={
        <ProtectedRoute>
          <AppLayout />
        </ProtectedRoute>
      }
    >
      <Route index element={<Dashboard />} />

      {/* Ledger / Chart of Accounts */}
      <Route path="ledger/chart-of-accounts" element={<ChartOfAccounts />} />
      <Route path="ledger/ledgers" element={<LedgerList />} />
      <Route path="ledger/journals" element={<JournalList />} />
      <Route path="ledger/cost-centers" element={<div>Cost Centers — implement next</div>} />

      {/* Vouchers */}
      <Route path="vouchers/:type" element={<VoucherForm />} />

      {/* Reports */}
      <Route path="reports/trial-balance" element={<TrialBalanceReport />} />
      <Route path="reports/profit-and-loss" element={<ProfitAndLossReport />} />
      <Route path="reports/balance-sheet" element={<BalanceSheetReport />} />
      <Route path="reports/cash-flow" element={<div>Cash Flow Statement — implement next</div>} />
      <Route path="reports/day-book" element={<div>Day Book — implement next</div>} />

      {/* Taxation */}
      <Route path="taxation/gst" element={<div>GST Returns — implement next</div>} />
      <Route path="taxation/tds" element={<div>TDS Management — implement next</div>} />
      <Route path="taxation/reports" element={<div>Tax Reports — implement next</div>} />

      {/* Inventory */}
      <Route path="inventory/items" element={<div>Items — implement next</div>} />
      <Route path="inventory/warehouses" element={<div>Warehouses — implement next</div>} />
      <Route path="inventory/purchase-orders" element={<div>Purchase Orders — implement next</div>} />
      <Route path="inventory/sales-orders" element={<div>Sales Orders — implement next</div>} />
      <Route path="inventory/stock-reports" element={<div>Stock Reports — implement next</div>} />

      {/* Banking */}
      <Route path="banking/accounts" element={<div>Bank Accounts — implement next</div>} />
      <Route path="banking/reconciliation" element={<div>Bank Reconciliation — implement next</div>} />

      {/* Payroll */}
      <Route path="payroll/employees" element={<div>Employees — implement next</div>} />
      <Route path="payroll/runs" element={<div>Payroll Runs — implement next</div>} />
      <Route path="payroll/payslips" element={<div>Payslips — implement next</div>} />

      {/* Audit */}
      <Route path="audit/plans" element={<div>Audit Plans — implement next</div>} />
      <Route path="audit/working-papers" element={<div>Working Papers — implement next</div>} />
      <Route path="audit/observations" element={<div>Observations — implement next</div>} />

      {/* Compliance */}
      <Route path="compliance/calendar" element={<div>Filing Calendar — implement next</div>} />
      <Route path="compliance/reports" element={<div>Regulatory Reports — implement next</div>} />

      {/* Advisory */}
      <Route path="advisory" element={<div>Corporate Advisory — implement next</div>} />

      {/* Companies */}
      <Route path="companies" element={<CompaniesPage />} />

      {/* Developer Mode */}
      <Route
        path="developer"
        element={
          <SuperAdminRoute>
            <DeveloperMode />
          </SuperAdminRoute>
        }
      />

      {/* Settings */}
      <Route path="settings" element={<SettingsPage />} />

      <Route path="*" element={<NotFound />} />
    </Route>
  </Routes>
);

const App: React.FC = () => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider>
      <BrowserRouter>
        <AuthProvider>
          <AppRoutes />
          <Toaster position="top-right" toastOptions={{ duration: 3500 }} />
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  </QueryClientProvider>
);

export default App;

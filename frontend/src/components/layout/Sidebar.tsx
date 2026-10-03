/**
 * SERENIA ACCOUNTING — components/layout/Sidebar.tsx
 * =====================================================
 * Primary navigation. Module visibility driven by user role
 * and Developer Mode feature flags.
 */

import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  HomeIcon, BookOpenIcon, DocumentTextIcon, ChartBarIcon,
  ReceiptPercentIcon, UsersIcon, CubeIcon, BanknotesIcon,
  ClipboardDocumentCheckIcon, ShieldCheckIcon, PresentationChartLineIcon,
  CodeBracketIcon, ChevronDownIcon, BuildingOffice2Icon, Cog6ToothIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';

interface NavItem {
  label: string;
  to?: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  roles?: string[];
  children?: { label: string; to: string }[];
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', to: '/', icon: HomeIcon },
  {
    label: 'Accounting', icon: BookOpenIcon,
    children: [
      { label: 'Chart of Accounts', to: '/ledger/chart-of-accounts' },
      { label: 'Ledgers', to: '/ledger/ledgers' },
      { label: 'Journal Entries', to: '/ledger/journals' },
      { label: 'Cost Centers', to: '/ledger/cost-centers' },
    ],
  },
  {
    label: 'Vouchers', icon: DocumentTextIcon,
    children: [
      { label: 'Payment Voucher', to: '/vouchers/payment' },
      { label: 'Receipt Voucher', to: '/vouchers/receipt' },
      { label: 'Contra Voucher', to: '/vouchers/contra' },
      { label: 'Sales Voucher', to: '/vouchers/sales' },
      { label: 'Purchase Voucher', to: '/vouchers/purchase' },
      { label: 'Credit / Debit Notes', to: '/vouchers/notes' },
    ],
  },
  {
    label: 'Reports', icon: ChartBarIcon,
    children: [
      { label: 'Trial Balance', to: '/reports/trial-balance' },
      { label: 'Profit & Loss', to: '/reports/profit-and-loss' },
      { label: 'Balance Sheet', to: '/reports/balance-sheet' },
      { label: 'Cash Flow', to: '/reports/cash-flow' },
      { label: 'Day Book', to: '/reports/day-book' },
    ],
  },
  {
    label: 'Taxation', icon: ReceiptPercentIcon,
    children: [
      { label: 'GST Returns', to: '/taxation/gst' },
      { label: 'TDS Management', to: '/taxation/tds' },
      { label: 'Tax Reports', to: '/taxation/reports' },
    ],
  },
  {
    label: 'Inventory', icon: CubeIcon,
    children: [
      { label: 'Items', to: '/inventory/items' },
      { label: 'Warehouses', to: '/inventory/warehouses' },
      { label: 'Purchase Orders', to: '/inventory/purchase-orders' },
      { label: 'Sales Orders', to: '/inventory/sales-orders' },
      { label: 'Stock Reports', to: '/inventory/stock-reports' },
    ],
  },
  {
    label: 'Banking', icon: BanknotesIcon,
    children: [
      { label: 'Bank Accounts', to: '/banking/accounts' },
      { label: 'Reconciliation', to: '/banking/reconciliation' },
    ],
  },
  {
    label: 'Payroll', icon: UsersIcon,
    children: [
      { label: 'Employees', to: '/payroll/employees' },
      { label: 'Payroll Runs', to: '/payroll/runs' },
      { label: 'Payslips', to: '/payroll/payslips' },
    ],
  },
  {
    label: 'Audit', icon: ClipboardDocumentCheckIcon, roles: ['super_admin', 'ca', 'auditor', 'admin'],
    children: [
      { label: 'Audit Plans', to: '/audit/plans' },
      { label: 'Working Papers', to: '/audit/working-papers' },
      { label: 'Observations', to: '/audit/observations' },
    ],
  },
  {
    label: 'Compliance', icon: ShieldCheckIcon,
    children: [
      { label: 'Filing Calendar', to: '/compliance/calendar' },
      { label: 'Regulatory Reports', to: '/compliance/reports' },
    ],
  },
  { label: 'Advisory', to: '/advisory', icon: PresentationChartLineIcon },
  { label: 'Companies', to: '/companies', icon: BuildingOffice2Icon },
  { label: 'Developer Mode', to: '/developer', icon: CodeBracketIcon, roles: ['super_admin'] },
  { label: 'Settings', to: '/settings', icon: Cog6ToothIcon },
];

export const Sidebar: React.FC<{ collapsed: boolean }> = ({ collapsed }) => {
  const { user, activeCompany } = useAuth();
  const [openGroups, setOpenGroups] = useState<Set<string>>(new Set(['Accounting']));

  const toggleGroup = (label: string) => {
    setOpenGroups((prev) => {
      const next = new Set(prev);
      next.has(label) ? next.delete(label) : next.add(label);
      return next;
    });
  };

  const visibleItems = NAV_ITEMS.filter((item) => !item.roles || (user && item.roles.includes(user.role)));

  return (
    <aside
      className={`
        fixed left-0 top-0 h-screen bg-white dark:bg-surface-dark-elevated
        border-r border-surface-200 dark:border-surface-dark-border
        shadow-sidebar transition-all duration-200 z-30 flex flex-col
        ${collapsed ? 'w-sidebar-collapsed' : 'w-sidebar'}
      `}
    >
      {/* Logo */}
      <div className="h-topbar flex items-center px-4 border-b border-surface-200 dark:border-surface-dark-border">
        <div className="w-8 h-8 rounded-md bg-gradient-to-br from-primary-500 to-teal-500 flex items-center justify-center text-white font-bold text-sm shrink-0">
          S
        </div>
        {!collapsed && (
          <span className="ml-2.5 font-display font-bold text-lg text-surface-dark dark:text-white tracking-tight">
            Serenia
          </span>
        )}
      </div>

      {/* Active company indicator */}
      {!collapsed && activeCompany && (
        <div className="px-4 py-3 border-b border-surface-200 dark:border-surface-dark-border">
          <p className="text-2xs uppercase tracking-wide text-surface-300 font-medium mb-0.5">Company</p>
          <p className="text-sm font-semibold text-surface-dark dark:text-white truncate">{activeCompany.name}</p>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-2 px-2 space-y-0.5">
        {visibleItems.map((item) => (
          <div key={item.label}>
            {item.children ? (
              <>
                <button
                  onClick={() => toggleGroup(item.label)}
                  className="w-full flex items-center justify-between px-3 py-2 rounded-md text-sm font-medium text-surface-dark dark:text-surface-100 hover:bg-surface-50 dark:hover:bg-surface-dark transition-colors"
                >
                  <span className="flex items-center gap-3">
                    <item.icon className="w-5 h-5 shrink-0" />
                    {!collapsed && item.label}
                  </span>
                  {!collapsed && (
                    <ChevronDownIcon
                      className={`w-4 h-4 text-surface-300 transition-transform ${openGroups.has(item.label) ? 'rotate-180' : ''}`}
                    />
                  )}
                </button>
                {!collapsed && openGroups.has(item.label) && (
                  <div className="mt-0.5 ml-4 pl-4 border-l border-surface-200 dark:border-surface-dark-border space-y-0.5">
                    {item.children.map((child) => (
                      <NavLink
                        key={child.to}
                        to={child.to}
                        className={({ isActive }) =>
                          `block px-3 py-1.5 rounded-md text-sm transition-colors ${
                            isActive
                              ? 'bg-primary-50 text-primary-600 dark:bg-primary-900/30 dark:text-primary-300 font-medium'
                              : 'text-surface-300 hover:text-surface-dark dark:hover:text-white hover:bg-surface-50 dark:hover:bg-surface-dark'
                          }`
                        }
                      >
                        {child.label}
                      </NavLink>
                    ))}
                  </div>
                )}
              </>
            ) : (
              <NavLink
                to={item.to!}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-primary-50 text-primary-600 dark:bg-primary-900/30 dark:text-primary-300'
                      : 'text-surface-dark dark:text-surface-100 hover:bg-surface-50 dark:hover:bg-surface-dark'
                  }`
                }
              >
                <item.icon className="w-5 h-5 shrink-0" />
                {!collapsed && item.label}
              </NavLink>
            )}
          </div>
        ))}
      </nav>
    </aside>
  );
};

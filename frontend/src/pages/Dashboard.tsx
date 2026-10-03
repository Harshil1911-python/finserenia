/**
 * SERENIA ACCOUNTING — pages/Dashboard.tsx
 * ===========================================
 * Professional accounting dashboard.
 * Fetches summary data from /api/v1/dashboard/summary/
 * (cached server-side in Redis for 5 minutes).
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  CurrencyRupeeIcon, ArrowTrendingDownIcon, ArrowTrendingUpIcon,
  BanknotesIcon, ReceiptPercentIcon, CubeIcon, UsersIcon, ScaleIcon,
} from '@heroicons/react/24/outline';
import { Line, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, ArcElement, Tooltip, Legend, Filler,
} from 'chart.js';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardHeader, CardTitle, CardBody, Skeleton, Badge } from '../components/ui/Card';
import { KPICard } from '../components/dashboard/KPICard';
import type { DashboardSummary } from '../types';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, ArcElement, Tooltip, Legend, Filler);

const formatCurrency = (value: string | number, currency = 'INR') => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency, maximumFractionDigits: 0 }).format(num || 0);
};

export const Dashboard: React.FC = () => {
  const { user, activeCompany } = useAuth();

  const { data, isLoading } = useQuery<DashboardSummary>({
    queryKey: ['dashboard-summary', activeCompany?.id],
    queryFn: async () => {
      const { data } = await api.get<DashboardSummary>('/dashboard/summary/');
      return data;
    },
    enabled: !!activeCompany,
    staleTime: 1000 * 60 * 5, // 5 minutes — matches backend cache TTL
  });

  const currency = activeCompany?.currency || 'INR';

  const trendChartData = {
    labels: data?.monthly_trend?.map((m) => m.month) || [],
    datasets: [
      {
        label: 'Revenue',
        data: data?.monthly_trend?.map((m) => m.revenue) || [],
        borderColor: '#6C5CE7',
        backgroundColor: 'rgba(108,92,231,0.08)',
        fill: true,
        tension: 0.35,
        pointRadius: 0,
      },
      {
        label: 'Expenses',
        data: data?.monthly_trend?.map((m) => m.expenses) || [],
        borderColor: '#FDCB6E',
        backgroundColor: 'rgba(253,203,110,0.08)',
        fill: true,
        tension: 0.35,
        pointRadius: 0,
      },
    ],
  };

  const receivablesPayables = {
    labels: ['Receivables', 'Payables'],
    datasets: [{
      data: [parseFloat(data?.receivables || '0'), parseFloat(data?.payables || '0')],
      backgroundColor: ['#00B894', '#D63031'],
      borderWidth: 0,
    }],
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <h1 className="text-2xl font-bold text-surface-dark dark:text-white font-display">
            Welcome back, {user?.first_name}
          </h1>
          <p className="text-sm text-surface-300 mt-0.5">
            {activeCompany?.name} {activeCompany?.current_fy && `· ${activeCompany.current_fy.label}`}
          </p>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {isLoading ? (
          Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-28 rounded-lg" />)
        ) : (
          <>
            <KPICard label="Revenue" value={formatCurrency(data?.revenue || 0, currency)} icon={ArrowTrendingUpIcon} iconColor="text-teal-500" trend={{ value: 12, isPositive: true }} subtext="vs last month" />
            <KPICard label="Expenses" value={formatCurrency(data?.expenses || 0, currency)} icon={ArrowTrendingDownIcon} iconColor="text-amber-500" trend={{ value: 4, isPositive: false }} subtext="vs last month" />
            <KPICard label="Net Profit" value={formatCurrency(data?.profit || 0, currency)} icon={CurrencyRupeeIcon} iconColor="text-primary-500" subtext={`${data?.profit_percent || 0}% margin`} />
            <KPICard label="Cash Position" value={formatCurrency(data?.cash_position || 0, currency)} icon={BanknotesIcon} iconColor="text-blue-500" />
            <KPICard label="Receivables" value={formatCurrency(data?.receivables || 0, currency)} icon={ScaleIcon} iconColor="text-teal-500" subtext="Outstanding" />
            <KPICard label="Payables" value={formatCurrency(data?.payables || 0, currency)} icon={ScaleIcon} iconColor="text-danger" subtext="Outstanding" />
            <KPICard label="Tax Liability" value={formatCurrency(data?.tax_liability || 0, currency)} icon={ReceiptPercentIcon} iconColor="text-purple-500" subtext="Current period" />
            <KPICard label="Inventory Value" value={formatCurrency(data?.inventory_value || 0, currency)} icon={CubeIcon} iconColor="text-orange-500" />
          </>
        )}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2 p-5">
          <CardTitle>Revenue vs Expenses</CardTitle>
          <p className="text-xs text-surface-300 mb-4">Last 6 months trend</p>
          {isLoading ? <Skeleton className="h-64" /> : (
            <div className="h-64">
              <Line
                data={trendChartData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } } },
                  scales: {
                    y: { ticks: { font: { size: 10 } }, grid: { color: 'rgba(0,0,0,0.04)' } },
                    x: { ticks: { font: { size: 10 } }, grid: { display: false } },
                  },
                }}
              />
            </div>
          )}
        </Card>

        <Card className="p-5">
          <CardTitle>Receivables vs Payables</CardTitle>
          <p className="text-xs text-surface-300 mb-4">Outstanding balances</p>
          {isLoading ? <Skeleton className="h-64" /> : (
            <div className="h-64 flex items-center justify-center">
              <Doughnut
                data={receivablesPayables}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } } },
                  cutout: '65%',
                }}
              />
            </div>
          )}
        </Card>
      </div>

      {/* Recent Transactions & Payroll/Banking Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader className="flex items-center justify-between">
            <CardTitle>Recent Transactions</CardTitle>
            <a href="/ledger/journals" className="text-xs font-medium text-primary-500 hover:text-primary-600">View all</a>
          </CardHeader>
          <CardBody className="p-0">
            {isLoading ? (
              <div className="p-5 space-y-3">
                {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-10" />)}
              </div>
            ) : data?.recent_transactions?.length ? (
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-2xs uppercase tracking-wide text-surface-300 border-b border-surface-200 dark:border-surface-dark-border">
                    <th className="px-5 py-2.5 font-medium">Date</th>
                    <th className="px-5 py-2.5 font-medium">Voucher</th>
                    <th className="px-5 py-2.5 font-medium">Party</th>
                    <th className="px-5 py-2.5 font-medium">Status</th>
                    <th className="px-5 py-2.5 font-medium text-right">Amount</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-100 dark:divide-surface-dark-border">
                  {data.recent_transactions.slice(0, 6).map((t) => (
                    <tr key={t.id} className="hover:bg-surface-50 dark:hover:bg-surface-dark transition-colors">
                      <td className="px-5 py-2.5 text-surface-300">{new Date(t.date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })}</td>
                      <td className="px-5 py-2.5 font-medium text-surface-dark dark:text-white capitalize">
                        {t.voucher_type} #{t.voucher_number}
                      </td>
                      <td className="px-5 py-2.5 text-surface-dark dark:text-surface-100">{t.party_name || '—'}</td>
                      <td className="px-5 py-2.5">
                        <Badge variant={t.status === 'posted' ? 'success' : t.status === 'pending_approval' ? 'warning' : 'default'}>
                          {t.status.replace('_', ' ')}
                        </Badge>
                      </td>
                      <td className="px-5 py-2.5 text-right font-medium tabular-nums">{formatCurrency(t.total_amount, currency)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="p-8 text-center text-sm text-surface-300">No recent transactions</div>
            )}
          </CardBody>
        </Card>

        <div className="space-y-4">
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-primary-50 dark:bg-primary-900/30 text-primary-500">
                <UsersIcon className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs text-surface-300">Payroll This Month</p>
                <p className="text-lg font-bold text-surface-dark dark:text-white">{formatCurrency(data?.payroll_this_month || 0, currency)}</p>
              </div>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-teal-50 dark:bg-teal-900/30 text-teal-500">
                <BanknotesIcon className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs text-surface-300">Bank Balance</p>
                <p className="text-lg font-bold text-surface-dark dark:text-white">{formatCurrency(data?.bank_balance || 0, currency)}</p>
              </div>
            </div>
          </Card>
          <Card className="p-4">
            <CardTitle className="mb-3 text-sm">Top Ledgers</CardTitle>
            <div className="space-y-2">
              {data?.top_ledgers_by_balance?.slice(0, 4).map((l, i) => (
                <div key={i} className="flex items-center justify-between text-sm">
                  <span className="text-surface-dark dark:text-surface-100 truncate">{l.name}</span>
                  <span className="font-medium tabular-nums">{formatCurrency(l.balance, currency)} <span className="text-2xs text-surface-300">{l.type}</span></span>
                </div>
              )) || <p className="text-xs text-surface-300">No data available</p>}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

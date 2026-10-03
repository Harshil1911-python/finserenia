/**
 * SERENIA ACCOUNTING — pages/reports/BalanceSheetReport.tsx
 * ============================================================
 * Assets vs Liabilities + Capital, side-by-side layout.
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import { Card, CardHeader, CardTitle, CardBody, Skeleton, Badge } from '../../components/ui/Card';

const formatCurrency = (value: string | number, currency = 'INR') => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency, maximumFractionDigits: 2 }).format(num || 0);
};

interface BalanceSheetData {
  company: string;
  financial_year: string;
  as_of_date: string;
  assets: { groups: Record<string, string>; total: string };
  liabilities: { groups: Record<string, string>; total: string };
  capital: { groups: Record<string, string>; total: string };
  is_balanced: boolean;
  difference: string;
}

const Side: React.FC<{ title: string; groups: Record<string, string>; total: string; currency: string; accent: string }> = ({ title, groups, total, currency, accent }) => (
  <div>
    <h4 className={`text-xs font-semibold uppercase tracking-wide mb-3 ${accent}`}>{title}</h4>
    <table className="w-full text-sm">
      <tbody className="divide-y divide-surface-100 dark:divide-surface-dark-border">
        {Object.entries(groups).length ? Object.entries(groups).map(([name, amount]) => (
          <tr key={name}>
            <td className="py-2 text-surface-dark dark:text-surface-100">{name}</td>
            <td className="py-2 text-right tabular-nums font-medium">{formatCurrency(amount, currency)}</td>
          </tr>
        )) : (
          <tr><td className="py-2 text-surface-300" colSpan={2}>No entries</td></tr>
        )}
      </tbody>
      <tfoot>
        <tr className="border-t-2 border-surface-200 dark:border-surface-dark-border font-bold">
          <td className="py-2.5">Total</td>
          <td className="py-2.5 text-right tabular-nums">{formatCurrency(total, currency)}</td>
        </tr>
      </tfoot>
    </table>
  </div>
);

export const BalanceSheetReport: React.FC = () => {
  const { activeCompany } = useAuth();
  const currency = activeCompany?.currency || 'INR';

  const { data, isLoading } = useQuery<BalanceSheetData>({
    queryKey: ['balance-sheet', activeCompany?.id],
    queryFn: async () => {
      const { data } = await api.get<BalanceSheetData>('/reports/balance-sheet/');
      return data;
    },
    enabled: !!activeCompany,
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  const liabAndCapTotal = (parseFloat(data?.liabilities.total || '0') + parseFloat(data?.capital.total || '0')).toFixed(2);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-surface-dark dark:text-white font-display">Balance Sheet</h1>
          <p className="text-sm text-surface-300 mt-0.5">As of {data?.as_of_date} · {data?.financial_year}</p>
        </div>
        {data && (
          <Badge variant={data.is_balanced ? 'success' : 'danger'}>
            {data.is_balanced ? '✓ Balanced' : `⚠ Out of balance by ${formatCurrency(data.difference, currency)}`}
          </Badge>
        )}
      </div>

      <Card>
        <CardHeader><CardTitle>Statement of Financial Position</CardTitle></CardHeader>
        <CardBody className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <Side title="Assets" groups={data?.assets.groups || {}} total={data?.assets.total || '0'} currency={currency} accent="text-blue-500" />
          <div className="space-y-6">
            <Side title="Liabilities" groups={data?.liabilities.groups || {}} total={data?.liabilities.total || '0'} currency={currency} accent="text-red-500" />
            <Side title="Capital & Equity" groups={data?.capital.groups || {}} total={data?.capital.total || '0'} currency={currency} accent="text-purple-500" />
            <div className="pt-3 border-t-2 border-surface-dark dark:border-white flex items-center justify-between font-bold text-base">
              <span>Total Liabilities + Capital</span>
              <span className="tabular-nums">{formatCurrency(liabAndCapTotal, currency)}</span>
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  );
};

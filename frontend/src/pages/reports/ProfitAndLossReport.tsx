/**
 * SERENIA ACCOUNTING — pages/reports/ProfitAndLossReport.tsx
 * =============================================================
 * Trading Account + Profit & Loss statement view.
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { ArrowTrendingUpIcon, ArrowTrendingDownIcon } from '@heroicons/react/24/outline';
import api from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import { Card, CardHeader, CardTitle, CardBody, Skeleton, Badge } from '../../components/ui/Card';

const formatCurrency = (value: string | number, currency = 'INR') => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency, maximumFractionDigits: 2 }).format(num || 0);
};

interface PnLData {
  company: string;
  financial_year: string;
  period: string;
  trading_account: {
    income: Record<string, string>;
    expenses: Record<string, string>;
    gross_profit: string;
    gross_profit_ratio: string;
  };
  profit_and_loss: {
    other_income: Record<string, string>;
    other_expenses: Record<string, string>;
    net_profit: string;
    net_profit_ratio: string;
  };
  summary: {
    total_income: string;
    total_expenses: string;
    net_profit: string;
    is_profit: boolean;
  };
}

const LineItemTable: React.FC<{ items: Record<string, string>; currency: string }> = ({ items, currency }) => (
  <table className="w-full text-sm">
    <tbody className="divide-y divide-surface-100 dark:divide-surface-dark-border">
      {Object.entries(items).length ? Object.entries(items).map(([name, amount]) => (
        <tr key={name}>
          <td className="py-2 text-surface-dark dark:text-surface-100">{name}</td>
          <td className="py-2 text-right tabular-nums font-medium">{formatCurrency(amount, currency)}</td>
        </tr>
      )) : (
        <tr><td className="py-2 text-surface-300 text-sm" colSpan={2}>No entries</td></tr>
      )}
    </tbody>
  </table>
);

export const ProfitAndLossReport: React.FC = () => {
  const { activeCompany } = useAuth();
  const currency = activeCompany?.currency || 'INR';

  const { data, isLoading } = useQuery<PnLData>({
    queryKey: ['profit-and-loss', activeCompany?.id],
    queryFn: async () => {
      const { data } = await api.get<PnLData>('/reports/profit-and-loss/');
      return data;
    },
    enabled: !!activeCompany,
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-64" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-surface-dark dark:text-white font-display">Profit &amp; Loss Statement</h1>
          <p className="text-sm text-surface-300 mt-0.5">{data?.period}</p>
        </div>
        {data && (
          <Badge variant={data.summary.is_profit ? 'success' : 'danger'}>
            <span className="flex items-center gap-1">
              {data.summary.is_profit ? <ArrowTrendingUpIcon className="w-3.5 h-3.5" /> : <ArrowTrendingDownIcon className="w-3.5 h-3.5" />}
              Net {data.summary.is_profit ? 'Profit' : 'Loss'}: {formatCurrency(data.summary.net_profit, currency)}
            </span>
          </Badge>
        )}
      </div>

      {/* Trading Account */}
      <Card>
        <CardHeader><CardTitle>Trading Account</CardTitle></CardHeader>
        <CardBody className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wide text-surface-300 mb-2">Direct Income</h4>
            {data && <LineItemTable items={data.trading_account.income} currency={currency} />}
          </div>
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wide text-surface-300 mb-2">Direct Expenses</h4>
            {data && <LineItemTable items={data.trading_account.expenses} currency={currency} />}
          </div>
          <div className="sm:col-span-2 pt-3 border-t border-surface-200 dark:border-surface-dark-border flex items-center justify-between">
            <span className="font-semibold text-surface-dark dark:text-white">Gross Profit ({data?.trading_account.gross_profit_ratio}%)</span>
            <span className="text-lg font-bold tabular-nums text-teal-600 dark:text-teal-400">{data && formatCurrency(data.trading_account.gross_profit, currency)}</span>
          </div>
        </CardBody>
      </Card>

      {/* Profit & Loss */}
      <Card>
        <CardHeader><CardTitle>Profit &amp; Loss Account</CardTitle></CardHeader>
        <CardBody className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wide text-surface-300 mb-2">Other Income</h4>
            {data && <LineItemTable items={data.profit_and_loss.other_income} currency={currency} />}
          </div>
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wide text-surface-300 mb-2">Indirect Expenses</h4>
            {data && <LineItemTable items={data.profit_and_loss.other_expenses} currency={currency} />}
          </div>
          <div className="sm:col-span-2 pt-3 border-t border-surface-200 dark:border-surface-dark-border flex items-center justify-between">
            <span className="font-semibold text-surface-dark dark:text-white">Net Profit ({data?.profit_and_loss.net_profit_ratio}%)</span>
            <span className={`text-xl font-bold tabular-nums ${data?.summary.is_profit ? 'text-teal-600 dark:text-teal-400' : 'text-danger'}`}>
              {data && formatCurrency(data.profit_and_loss.net_profit, currency)}
            </span>
          </div>
        </CardBody>
      </Card>
    </div>
  );
};

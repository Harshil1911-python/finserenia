/**
 * SERENIA ACCOUNTING — pages/reports/TrialBalanceReport.tsx
 * ============================================================
 * Displays Trial Balance with export to PDF/Excel.
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { DocumentArrowDownIcon, TableCellsIcon } from '@heroicons/react/24/outline';
import api from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import { Card, CardHeader, CardTitle, Skeleton, Badge, Input } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import type { TrialBalance } from '../../types';

const formatCurrency = (value: string | number, currency = 'INR') => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency, maximumFractionDigits: 2 }).format(num || 0);
};

export const TrialBalanceReport: React.FC = () => {
  const { activeCompany } = useAuth();
  const [asOfDate, setAsOfDate] = useState('');

  const { data, isLoading } = useQuery<TrialBalance>({
    queryKey: ['trial-balance', activeCompany?.id, asOfDate],
    queryFn: async () => {
      const { data } = await api.get<TrialBalance>('/reports/trial-balance/', {
        params: { as_of_date: asOfDate || undefined },
      });
      return data;
    },
    enabled: !!activeCompany,
  });

  const currency = activeCompany?.currency || 'INR';

  const handleExport = (format: 'pdf' | 'excel') => {
    const params = new URLSearchParams({ format, ...(asOfDate ? { as_of_date: asOfDate } : {}) });
    window.open(`${api.defaults.baseURL}/reports/trial-balance/?${params}`, '_blank');
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-surface-dark dark:text-white font-display">Trial Balance</h1>
          <p className="text-sm text-surface-300 mt-0.5">{data?.financial_year || 'Current financial year'}</p>
        </div>
        <div className="flex items-center gap-2">
          <Input type="date" value={asOfDate} onChange={(e) => setAsOfDate(e.target.value)} placeholder="As of date" />
          <Button variant="outline" leftIcon={<TableCellsIcon className="w-4 h-4" />} onClick={() => handleExport('excel')}>Excel</Button>
          <Button variant="outline" leftIcon={<DocumentArrowDownIcon className="w-4 h-4" />} onClick={() => handleExport('pdf')}>PDF</Button>
        </div>
      </div>

      {data && (
        <div className="flex items-center gap-3">
          <Badge variant={data.totals.is_balanced ? 'success' : 'danger'}>
            {data.totals.is_balanced ? '✓ Balanced' : `⚠ Out of balance by ${formatCurrency(data.totals.difference, currency)}`}
          </Badge>
          <span className="text-xs text-surface-300">As of {data.as_of_date}</span>
        </div>
      )}

      <Card className="overflow-hidden">
        {isLoading ? (
          <div className="p-5 space-y-3">
            {Array.from({ length: 10 }).map((_, i) => <Skeleton key={i} className="h-10" />)}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-2xs uppercase tracking-wide text-surface-300 border-b border-surface-200 dark:border-surface-dark-border">
                  <th className="px-5 py-3 font-medium">Ledger</th>
                  <th className="px-5 py-3 font-medium">Group</th>
                  <th className="px-5 py-3 font-medium text-right">Debit</th>
                  <th className="px-5 py-3 font-medium text-right">Credit</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-100 dark:divide-surface-dark-border">
                {data?.rows.map((row) => (
                  <tr key={row.ledger_id} className="hover:bg-surface-50 dark:hover:bg-surface-dark transition-colors">
                    <td className="px-5 py-2.5 font-medium text-surface-dark dark:text-white">{row.ledger_name}</td>
                    <td className="px-5 py-2.5 text-surface-300">{row.group}</td>
                    <td className="px-5 py-2.5 text-right tabular-nums">{row.balance_type === 'Dr' ? formatCurrency(row.balance, currency) : '—'}</td>
                    <td className="px-5 py-2.5 text-right tabular-nums">{row.balance_type === 'Cr' ? formatCurrency(row.balance, currency) : '—'}</td>
                  </tr>
                ))}
              </tbody>
              {data && (
                <tfoot>
                  <tr className="border-t-2 border-surface-200 dark:border-surface-dark-border font-bold">
                    <td className="px-5 py-3" colSpan={2}>Total</td>
                    <td className="px-5 py-3 text-right tabular-nums">{formatCurrency(data.totals.debit, currency)}</td>
                    <td className="px-5 py-3 text-right tabular-nums">{formatCurrency(data.totals.credit, currency)}</td>
                  </tr>
                </tfoot>
              )}
            </table>
          </div>
        )}
      </Card>
    </div>
  );
};

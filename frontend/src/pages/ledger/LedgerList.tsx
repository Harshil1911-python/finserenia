/**
 * SERENIA ACCOUNTING — pages/ledger/LedgerList.tsx
 * ===================================================
 * Paginated, searchable, filterable list of all ledgers
 * with current balances. Supports create/edit/reconcile.
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { PlusIcon, MagnifyingGlassIcon, BanknotesIcon } from '@heroicons/react/24/outline';
import api from '../../services/api';
import { Card, Badge, Skeleton, EmptyState, Input, Select } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import type { Ledger, PaginatedResponse, AccountNature } from '../../types';

const formatCurrency = (value: string | number, currency = 'INR') => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency, maximumFractionDigits: 2 }).format(num || 0);
};

export const LedgerList: React.FC = () => {
  const [search, setSearch] = useState('');
  const [natureFilter, setNatureFilter] = useState('');
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery<PaginatedResponse<Ledger>>({
    queryKey: ['ledgers', search, natureFilter, page],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<Ledger>>('/ledger/ledgers/', {
        params: { search, nature: natureFilter || undefined, page },
      });
      return data;
    },
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-surface-dark dark:text-white font-display">Ledgers</h1>
          <p className="text-sm text-surface-300 mt-0.5">Manage all your accounts and view balances</p>
        </div>
        <Button leftIcon={<PlusIcon className="w-4 h-4" />}>New Ledger</Button>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <Input
          placeholder="Search by name, code, GSTIN..."
          leftAddon={<MagnifyingGlassIcon className="w-4 h-4" />}
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="sm:w-72"
        />
        <Select
          placeholder="All account types"
          value={natureFilter}
          onChange={(e) => { setNatureFilter(e.target.value); setPage(1); }}
          options={[
            { value: 'assets', label: 'Assets' },
            { value: 'liabilities', label: 'Liabilities' },
            { value: 'capital', label: 'Capital & Equity' },
            { value: 'income', label: 'Income' },
            { value: 'expenses', label: 'Expenses' },
          ] as Array<{ value: AccountNature; label: string }>}
          className="sm:w-48"
        />
      </div>

      <Card className="overflow-hidden">
        {isLoading ? (
          <div className="p-5 space-y-3">
            {Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-12" />)}
          </div>
        ) : data?.results?.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-2xs uppercase tracking-wide text-surface-300 border-b border-surface-200 dark:border-surface-dark-border">
                  <th className="px-5 py-3 font-medium">Ledger Name</th>
                  <th className="px-5 py-3 font-medium">Group</th>
                  <th className="px-5 py-3 font-medium">Type</th>
                  <th className="px-5 py-3 font-medium text-right">Balance</th>
                  <th className="px-5 py-3 font-medium text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-100 dark:divide-surface-dark-border">
                {data.results.map((ledger) => (
                  <tr key={ledger.id} className="hover:bg-surface-50 dark:hover:bg-surface-dark transition-colors cursor-pointer">
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2.5">
                        {ledger.is_bank_account && <BanknotesIcon className="w-4 h-4 text-blue-500 shrink-0" />}
                        <div>
                          <p className="font-medium text-surface-dark dark:text-white">{ledger.name}</p>
                          {ledger.code && <p className="text-2xs text-surface-300">{ledger.code}</p>}
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3 text-surface-300">{ledger.group_name || '—'}</td>
                    <td className="px-5 py-3">
                      {ledger.is_party_ledger && <Badge variant="info">Party</Badge>}
                      {ledger.is_bank_account && <Badge variant="primary" className="ml-1">Bank</Badge>}
                      {ledger.is_tds_applicable && <Badge variant="warning" className="ml-1">TDS</Badge>}
                    </td>
                    <td className="px-5 py-3 text-right font-medium tabular-nums">
                      {formatCurrency(ledger.current_balance || ledger.opening_balance, ledger.currency)}{' '}
                      <span className="text-2xs text-surface-300">{ledger.current_balance_type || ledger.opening_balance_type}</span>
                    </td>
                    <td className="px-5 py-3 text-center">
                      <Badge variant={ledger.is_active ? 'success' : 'default'}>{ledger.is_active ? 'Active' : 'Inactive'}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            icon={<BanknotesIcon className="w-10 h-10" />}
            title="No ledgers found"
            description="Create your first ledger to start recording transactions."
            action={<Button leftIcon={<PlusIcon className="w-4 h-4" />}>New Ledger</Button>}
          />
        )}

        {/* Pagination */}
        {data && data.count > 0 && (
          <div className="flex items-center justify-between px-5 py-3 border-t border-surface-200 dark:border-surface-dark-border text-sm">
            <p className="text-surface-300">Showing {data.results.length} of {data.count} ledgers</p>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" disabled={!data.previous} onClick={() => setPage((p) => p - 1)}>Previous</Button>
              <Button variant="outline" size="sm" disabled={!data.next} onClick={() => setPage((p) => p + 1)}>Next</Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};

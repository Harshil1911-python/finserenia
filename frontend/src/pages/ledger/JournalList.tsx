/**
 * SERENIA ACCOUNTING — pages/ledger/JournalList.tsx
 * ====================================================
 * List of all journal entries / vouchers with status,
 * approval workflow actions, and filtering by type/date.
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PlusIcon, CheckCircleIcon, XCircleIcon, EyeIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import api, { normalizeError } from '../../services/api';
import { Card, Badge, Skeleton, EmptyState, Select, Input } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import type { JournalEntry, PaginatedResponse, VoucherType, VoucherStatus } from '../../types';

const STATUS_VARIANT: Record<VoucherStatus, 'default' | 'success' | 'warning' | 'danger' | 'info' | 'primary'> = {
  draft: 'default',
  pending_approval: 'warning',
  approved: 'info',
  posted: 'success',
  rejected: 'danger',
  cancelled: 'default',
};

const formatCurrency = (value: string | number, currency = 'INR') => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency, maximumFractionDigits: 2 }).format(num || 0);
};

export const JournalList: React.FC = () => {
  const queryClient = useQueryClient();
  const [voucherType, setVoucherType] = useState('');
  const [status, setStatus] = useState('');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery<PaginatedResponse<JournalEntry>>({
    queryKey: ['journals', voucherType, status, fromDate, toDate, page],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<JournalEntry>>('/journals/', {
        params: {
          voucher_type: voucherType || undefined,
          status: status || undefined,
          date_after: fromDate || undefined,
          date_before: toDate || undefined,
          page,
        },
      });
      return data;
    },
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => api.post(`/journals/${id}/approve/`),
    onSuccess: () => {
      toast.success('Journal entry approved and posted');
      queryClient.invalidateQueries({ queryKey: ['journals'] });
    },
    onError: (err) => toast.error(normalizeError(err).message),
  });

  const rejectMutation = useMutation({
    mutationFn: (id: string) => api.post(`/journals/${id}/reject/`),
    onSuccess: () => {
      toast.success('Journal entry rejected');
      queryClient.invalidateQueries({ queryKey: ['journals'] });
    },
    onError: (err) => toast.error(normalizeError(err).message),
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-surface-dark dark:text-white font-display">Journal Entries</h1>
          <p className="text-sm text-surface-300 mt-0.5">All vouchers and journal entries with approval workflow</p>
        </div>
        <Button leftIcon={<PlusIcon className="w-4 h-4" />} onClick={() => window.location.assign('/vouchers/journal')}>
          New Journal Entry
        </Button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Select
          placeholder="All voucher types"
          value={voucherType}
          onChange={(e) => { setVoucherType(e.target.value); setPage(1); }}
          options={[
            { value: 'payment', label: 'Payment' },
            { value: 'receipt', label: 'Receipt' },
            { value: 'contra', label: 'Contra' },
            { value: 'journal', label: 'Journal' },
            { value: 'sales', label: 'Sales' },
            { value: 'purchase', label: 'Purchase' },
            { value: 'credit_note', label: 'Credit Note' },
            { value: 'debit_note', label: 'Debit Note' },
          ] as Array<{ value: VoucherType; label: string }>}
        />
        <Select
          placeholder="All statuses"
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          options={[
            { value: 'draft', label: 'Draft' },
            { value: 'pending_approval', label: 'Pending Approval' },
            { value: 'approved', label: 'Approved' },
            { value: 'posted', label: 'Posted' },
            { value: 'rejected', label: 'Rejected' },
          ] as Array<{ value: VoucherStatus; label: string }>}
        />
        <Input type="date" value={fromDate} onChange={(e) => { setFromDate(e.target.value); setPage(1); }} />
        <Input type="date" value={toDate} onChange={(e) => { setToDate(e.target.value); setPage(1); }} />
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
                  <th className="px-5 py-3 font-medium">Date</th>
                  <th className="px-5 py-3 font-medium">Voucher No.</th>
                  <th className="px-5 py-3 font-medium">Type</th>
                  <th className="px-5 py-3 font-medium">Party / Narration</th>
                  <th className="px-5 py-3 font-medium text-right">Amount</th>
                  <th className="px-5 py-3 font-medium text-center">Status</th>
                  <th className="px-5 py-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-100 dark:divide-surface-dark-border">
                {data.results.map((j) => (
                  <tr key={j.id} className="hover:bg-surface-50 dark:hover:bg-surface-dark transition-colors">
                    <td className="px-5 py-3 text-surface-300 whitespace-nowrap">{new Date(j.date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}</td>
                    <td className="px-5 py-3 font-medium text-surface-dark dark:text-white">#{j.voucher_number}</td>
                    <td className="px-5 py-3 capitalize text-surface-300">{j.voucher_type.replace('_', ' ')}</td>
                    <td className="px-5 py-3 max-w-xs truncate">{j.party_name || j.narration || '—'}</td>
                    <td className="px-5 py-3 text-right font-medium tabular-nums">{formatCurrency(j.total_amount, j.currency)}</td>
                    <td className="px-5 py-3 text-center">
                      <Badge variant={STATUS_VARIANT[j.status]}>{j.status.replace('_', ' ')}</Badge>
                    </td>
                    <td className="px-5 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button variant="ghost" size="sm" title="View"><EyeIcon className="w-4 h-4" /></Button>
                        {j.status === 'pending_approval' && (
                          <>
                            <Button variant="ghost" size="sm" title="Approve" className="text-teal-500" onClick={() => approveMutation.mutate(j.id)}>
                              <CheckCircleIcon className="w-4 h-4" />
                            </Button>
                            <Button variant="ghost" size="sm" title="Reject" className="text-danger" onClick={() => rejectMutation.mutate(j.id)}>
                              <XCircleIcon className="w-4 h-4" />
                            </Button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState title="No journal entries found" description="Create a voucher to record your first transaction." />
        )}

        {data && data.count > 0 && (
          <div className="flex items-center justify-between px-5 py-3 border-t border-surface-200 dark:border-surface-dark-border text-sm">
            <p className="text-surface-300">Showing {data.results.length} of {data.count} entries</p>
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

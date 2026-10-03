/**
 * SERENIA ACCOUNTING — pages/vouchers/VoucherForm.tsx
 * ======================================================
 * Unified voucher entry form for Payment, Receipt, Contra,
 * Journal, Sales, Purchase, Credit Note, Debit Note.
 * Enforces debit = credit balance before submission.
 */

import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import api, { normalizeError } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import { Card, CardHeader, CardTitle, CardBody, Input, Select } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import type { Ledger, JournalLine, VoucherType } from '../../types';

const VOUCHER_LABELS: Record<string, string> = {
  payment: 'Payment Voucher',
  receipt: 'Receipt Voucher',
  contra: 'Contra Voucher',
  journal: 'Journal Voucher',
  sales: 'Sales Voucher',
  purchase: 'Purchase Voucher',
  notes: 'Credit / Debit Note',
};

interface LineRow extends JournalLine {
  key: string;
}

const newLine = (): LineRow => ({
  key: Math.random().toString(36).slice(2),
  ledger: '',
  debit_amount: '',
  credit_amount: '',
  narration: '',
});

export const VoucherForm: React.FC = () => {
  const { type } = useParams<{ type: string }>();
  const navigate = useNavigate();
  const { activeCompany } = useAuth();

  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [narration, setNarration] = useState('');
  const [reference, setReference] = useState('');
  const [lines, setLines] = useState<LineRow[]>([newLine(), newLine()]);

  const { data: ledgers } = useQuery<Ledger[]>({
    queryKey: ['ledgers-all', activeCompany?.id],
    queryFn: async () => {
      const { data } = await api.get('/ledger/ledgers/', { params: { page_size: 500, is_active: true } });
      return data.results;
    },
    enabled: !!activeCompany,
  });

  const ledgerOptions = useMemo(
    () => ledgers?.map((l) => ({ value: l.id, label: `${l.name}${l.code ? ` (${l.code})` : ''}` })) || [],
    [ledgers]
  );

  const totals = useMemo(() => {
    const totalDr = lines.reduce((sum, l) => sum + (parseFloat(l.debit_amount) || 0), 0);
    const totalCr = lines.reduce((sum, l) => sum + (parseFloat(l.credit_amount) || 0), 0);
    return { totalDr, totalCr, isBalanced: Math.abs(totalDr - totalCr) < 0.01 && totalDr > 0 };
  }, [lines]);

  const updateLine = (key: string, field: keyof JournalLine, value: string) => {
    setLines((prev) => prev.map((l) => {
      if (l.key !== key) return l;
      const updated = { ...l, [field]: value };
      // Mutually exclusive debit/credit
      if (field === 'debit_amount' && value) updated.credit_amount = '';
      if (field === 'credit_amount' && value) updated.debit_amount = '';
      return updated;
    }));
  };

  const addLine = () => setLines((prev) => [...prev, newLine()]);
  const removeLine = (key: string) => setLines((prev) => prev.length > 2 ? prev.filter((l) => l.key !== key) : prev);

  const submitMutation = useMutation({
    mutationFn: async (status: 'draft' | 'pending_approval') => {
      const payload = {
        voucher_type: (type === 'notes' ? 'credit_note' : type) as VoucherType,
        date,
        narration,
        reference,
        status,
        lines: lines
          .filter((l) => l.ledger && (l.debit_amount || l.credit_amount))
          .map((l) => ({
            ledger: l.ledger,
            debit_amount: l.debit_amount || '0',
            credit_amount: l.credit_amount || '0',
            narration: l.narration,
          })),
      };
      return api.post('/journals/', payload);
    },
    onSuccess: () => {
      toast.success('Voucher saved successfully');
      navigate('/ledger/journals');
    },
    onError: (err) => toast.error(normalizeError(err).message),
  });

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-surface-dark dark:text-white font-display">
          {VOUCHER_LABELS[type || 'journal'] || 'New Voucher'}
        </h1>
        <p className="text-sm text-surface-300 mt-0.5">Record a new transaction. Debit and credit must balance.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Voucher Details</CardTitle>
        </CardHeader>
        <CardBody className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Input label="Date" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          <Input label="Reference No." placeholder="Invoice / Cheque number" value={reference} onChange={(e) => setReference(e.target.value)} />
          <Input label="Narration" placeholder="Brief description" value={narration} onChange={(e) => setNarration(e.target.value)} className="sm:col-span-1" />
        </CardBody>
      </Card>

      <Card>
        <CardHeader className="flex items-center justify-between">
          <CardTitle>Ledger Entries</CardTitle>
          <Button variant="outline" size="sm" leftIcon={<PlusIcon className="w-4 h-4" />} onClick={addLine}>Add Row</Button>
        </CardHeader>
        <CardBody className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-2xs uppercase tracking-wide text-surface-300 border-b border-surface-200 dark:border-surface-dark-border">
                  <th className="px-4 py-2 font-medium w-2/5">Ledger</th>
                  <th className="px-4 py-2 font-medium">Narration</th>
                  <th className="px-4 py-2 font-medium text-right w-32">Debit</th>
                  <th className="px-4 py-2 font-medium text-right w-32">Credit</th>
                  <th className="px-2 py-2 w-10"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-100 dark:divide-surface-dark-border">
                {lines.map((line) => (
                  <tr key={line.key}>
                    <td className="px-4 py-2">
                      <Select
                        placeholder="Select ledger"
                        value={line.ledger}
                        onChange={(e) => updateLine(line.key, 'ledger', e.target.value)}
                        options={ledgerOptions}
                      />
                    </td>
                    <td className="px-4 py-2">
                      <Input
                        placeholder="Optional note"
                        value={line.narration}
                        onChange={(e) => updateLine(line.key, 'narration', e.target.value)}
                      />
                    </td>
                    <td className="px-4 py-2">
                      <Input
                        type="number" step="0.01" placeholder="0.00" className="text-right"
                        value={line.debit_amount}
                        onChange={(e) => updateLine(line.key, 'debit_amount', e.target.value)}
                      />
                    </td>
                    <td className="px-4 py-2">
                      <Input
                        type="number" step="0.01" placeholder="0.00" className="text-right"
                        value={line.credit_amount}
                        onChange={(e) => updateLine(line.key, 'credit_amount', e.target.value)}
                      />
                    </td>
                    <td className="px-2 py-2 text-center">
                      <button onClick={() => removeLine(line.key)} className="text-surface-300 hover:text-danger transition-colors">
                        <TrashIcon className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="border-t border-surface-200 dark:border-surface-dark-border font-semibold">
                  <td className="px-4 py-2.5" colSpan={2}>Total</td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{totals.totalDr.toFixed(2)}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{totals.totalCr.toFixed(2)}</td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
          </div>

          <div className="px-4 py-3 border-t border-surface-200 dark:border-surface-dark-border">
            {totals.isBalanced ? (
              <p className="text-sm text-teal-600 dark:text-teal-400 font-medium">✓ Entry is balanced</p>
            ) : (
              <p className="text-sm text-danger font-medium">
                Out of balance by {Math.abs(totals.totalDr - totals.totalCr).toFixed(2)}
              </p>
            )}
          </div>
        </CardBody>
      </Card>

      <div className="flex justify-end gap-3">
        <Button variant="outline" onClick={() => navigate(-1)}>Cancel</Button>
        <Button variant="ghost" onClick={() => submitMutation.mutate('draft')} isLoading={submitMutation.isPending}>
          Save as Draft
        </Button>
        <Button
          onClick={() => submitMutation.mutate('pending_approval')}
          disabled={!totals.isBalanced}
          isLoading={submitMutation.isPending}
        >
          Submit for Approval
        </Button>
      </div>
    </div>
  );
};

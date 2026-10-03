/**
 * SERENIA ACCOUNTING — pages/ledger/ChartOfAccounts.tsx
 * ========================================================
 * Hierarchical view of Asset/Liability/Capital/Income/Expense
 * groups with nested ledgers. Supports create/edit groups & ledgers.
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronRightIcon, FolderIcon, DocumentTextIcon, PlusIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import api from '../../services/api';
import { Card, CardHeader, CardTitle, Badge, Skeleton, EmptyState, Input } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import type { LedgerGroup, AccountNature } from '../../types';

const NATURE_LABELS: Record<AccountNature, { label: string; color: string }> = {
  assets: { label: 'Assets', color: 'text-blue-500 bg-blue-50 dark:bg-blue-900/20' },
  liabilities: { label: 'Liabilities', color: 'text-red-500 bg-red-50 dark:bg-red-900/20' },
  capital: { label: 'Capital & Equity', color: 'text-purple-500 bg-purple-50 dark:bg-purple-900/20' },
  income: { label: 'Income', color: 'text-teal-500 bg-teal-50 dark:bg-teal-900/20' },
  expenses: { label: 'Expenses', color: 'text-amber-500 bg-amber-50 dark:bg-amber-900/20' },
};

const GroupNode: React.FC<{ group: LedgerGroup; depth: number }> = ({ group, depth }) => {
  const [expanded, setExpanded] = useState(depth < 1);
  const hasChildren = (group.children && group.children.length > 0) || (group.ledger_count && group.ledger_count > 0);

  return (
    <div>
      <button
        onClick={() => setExpanded((e) => !e)}
        className="w-full flex items-center gap-2 py-1.5 px-2 rounded-md hover:bg-surface-50 dark:hover:bg-surface-dark transition-colors text-left"
        style={{ paddingLeft: `${depth * 20 + 8}px` }}
      >
        {hasChildren ? (
          <ChevronRightIcon className={`w-3.5 h-3.5 text-surface-300 shrink-0 transition-transform ${expanded ? 'rotate-90' : ''}`} />
        ) : (
          <span className="w-3.5" />
        )}
        <FolderIcon className="w-4 h-4 text-primary-400 shrink-0" />
        <span className="text-sm font-medium text-surface-dark dark:text-white">{group.name}</span>
        {!!group.ledger_count && (
          <Badge variant="default" className="ml-auto">{group.ledger_count} ledgers</Badge>
        )}
      </button>
      {expanded && group.children?.map((child) => (
        <GroupNode key={child.id} group={child} depth={depth + 1} />
      ))}
    </div>
  );
};

export const ChartOfAccounts: React.FC = () => {
  const [search, setSearch] = useState('');

  const { data: groups, isLoading } = useQuery<LedgerGroup[]>({
    queryKey: ['ledger-groups'],
    queryFn: async () => {
      const { data } = await api.get<LedgerGroup[]>('/ledger/groups/?tree=true');
      return data;
    },
  });

  // Group root nodes by nature for the five-column summary
  const groupedByNature: Record<string, LedgerGroup[]> = {};
  groups?.forEach((g) => {
    if (!g.parent) {
      groupedByNature[g.nature] = groupedByNature[g.nature] || [];
      groupedByNature[g.nature].push(g);
    }
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-surface-dark dark:text-white font-display">Chart of Accounts</h1>
          <p className="text-sm text-surface-300 mt-0.5">Organize your accounts into groups and ledgers</p>
        </div>
        <div className="flex items-center gap-2">
          <Input
            placeholder="Search accounts..."
            leftAddon={<MagnifyingGlassIcon className="w-4 h-4" />}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-56"
          />
          <Button leftIcon={<PlusIcon className="w-4 h-4" />}>New Group</Button>
          <Button variant="secondary" leftIcon={<PlusIcon className="w-4 h-4" />}>New Ledger</Button>
        </div>
      </div>

      {/* Nature summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {(Object.keys(NATURE_LABELS) as AccountNature[]).map((nature) => (
          <Card key={nature} className="p-3.5 text-center">
            <div className={`inline-flex items-center justify-center w-9 h-9 rounded-lg mb-2 ${NATURE_LABELS[nature].color}`}>
              <DocumentTextIcon className="w-5 h-5" />
            </div>
            <p className="text-xs font-medium text-surface-dark dark:text-white">{NATURE_LABELS[nature].label}</p>
            <p className="text-2xs text-surface-300 mt-0.5">{groupedByNature[nature]?.length || 0} groups</p>
          </Card>
        ))}
      </div>

      {/* Hierarchy tree */}
      <Card>
        <CardHeader>
          <CardTitle>Account Hierarchy</CardTitle>
        </CardHeader>
        <div className="p-2">
          {isLoading ? (
            <div className="space-y-2 p-3">
              {Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-8" />)}
            </div>
          ) : groups && groups.length > 0 ? (
            (Object.keys(NATURE_LABELS) as AccountNature[]).map((nature) => (
              groupedByNature[nature]?.length ? (
                <div key={nature} className="mb-2">
                  <div className={`px-2 py-1.5 mb-1 text-2xs font-semibold uppercase tracking-wide rounded-md ${NATURE_LABELS[nature].color} inline-flex items-center`}>
                    {NATURE_LABELS[nature].label}
                  </div>
                  {groupedByNature[nature].map((g) => <GroupNode key={g.id} group={g} depth={0} />)}
                </div>
              ) : null
            ))
          ) : (
            <EmptyState
              icon={<FolderIcon className="w-10 h-10" />}
              title="No account groups yet"
              description="Get started by creating your first account group, or use a standard template (Indian GAAP / IFRS)."
              action={<Button leftIcon={<PlusIcon className="w-4 h-4" />}>Create Account Group</Button>}
            />
          )}
        </div>
      </Card>
    </div>
  );
};

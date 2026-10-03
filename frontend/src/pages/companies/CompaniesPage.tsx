/**
 * SERENIA ACCOUNTING — pages/companies/CompaniesPage.tsx
 * =========================================================
 * Multi-company management: list, create, edit companies,
 * manage branches and financial years.
 */

import React from 'react';
import { PlusIcon, BuildingOffice2Icon } from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import { Card, CardBody, Badge, EmptyState } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';

export const CompaniesPage: React.FC = () => {
  const { companies, activeCompany, switchCompany } = useAuth();

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-surface-dark dark:text-white font-display">Companies</h1>
          <p className="text-sm text-surface-300 mt-0.5">Manage all companies on this platform</p>
        </div>
        <Button leftIcon={<PlusIcon className="w-4 h-4" />}>New Company</Button>
      </div>

      {companies.length === 0 ? (
        <Card>
          <EmptyState
            icon={<BuildingOffice2Icon className="w-10 h-10" />}
            title="No companies yet"
            description="Create your first company to start managing accounts."
            action={<Button leftIcon={<PlusIcon className="w-4 h-4" />}>Create Company</Button>}
          />
        </Card>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {companies.map((company) => (
            <Card key={company.id} hoverable className="overflow-hidden">
              <CardBody>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-11 h-11 rounded-lg bg-gradient-to-br from-primary-400 to-teal-400 flex items-center justify-center text-white font-bold text-lg">
                      {company.name.charAt(0)}
                    </div>
                    <div>
                      <p className="font-semibold text-surface-dark dark:text-white">{company.name}</p>
                      <p className="text-xs text-surface-300">{company.city}{company.city && company.state ? ', ' : ''}{company.state}</p>
                    </div>
                  </div>
                  {activeCompany?.id === company.id && <Badge variant="primary">Active</Badge>}
                </div>

                <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <p className="text-surface-300">GSTIN</p>
                    <p className="font-medium text-surface-dark dark:text-white">{company.gstin || '—'}</p>
                  </div>
                  <div>
                    <p className="text-surface-300">Currency</p>
                    <p className="font-medium text-surface-dark dark:text-white">{company.currency}</p>
                  </div>
                  <div>
                    <p className="text-surface-300">Branches</p>
                    <p className="font-medium text-surface-dark dark:text-white">{company.branches?.length || 0}</p>
                  </div>
                  <div>
                    <p className="text-surface-300">Financial Year</p>
                    <p className="font-medium text-surface-dark dark:text-white">{company.current_fy?.label || '—'}</p>
                  </div>
                </div>

                <div className="mt-4 flex gap-2">
                  {activeCompany?.id !== company.id && (
                    <Button size="sm" variant="outline" className="flex-1" onClick={() => switchCompany(company.id)}>Switch to</Button>
                  )}
                  <Button size="sm" variant="ghost" className="flex-1">Manage</Button>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

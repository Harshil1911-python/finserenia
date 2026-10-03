/**
 * SERENIA ACCOUNTING — components/dashboard/KPICard.tsx
 * ========================================================
 * Reusable dashboard metric card with trend indicator.
 */

import React from 'react';
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/solid';
import { Card } from '../ui/Card';

interface KPICardProps {
  label: string;
  value: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  iconColor?: string;
  trend?: { value: number; isPositive: boolean };
  subtext?: string;
}

export const KPICard: React.FC<KPICardProps> = ({ label, value, icon: Icon, iconColor = 'text-primary-500', trend, subtext }) => {
  return (
    <Card hoverable className="p-4">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-xs font-medium text-surface-300 uppercase tracking-wide">{label}</p>
          <p className="mt-1.5 text-2xl font-bold text-surface-dark dark:text-white tabular-nums">{value}</p>
          {(trend || subtext) && (
            <div className="mt-1.5 flex items-center gap-1.5 text-xs">
              {trend && (
                <span className={`inline-flex items-center gap-0.5 font-medium ${trend.isPositive ? 'text-teal-600 dark:text-teal-400' : 'text-danger'}`}>
                  {trend.isPositive ? <ArrowUpIcon className="w-3 h-3" /> : <ArrowDownIcon className="w-3 h-3" />}
                  {Math.abs(trend.value)}%
                </span>
              )}
              {subtext && <span className="text-surface-300">{subtext}</span>}
            </div>
          )}
        </div>
        <div className={`p-2.5 rounded-lg bg-surface-50 dark:bg-surface-dark ${iconColor}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </Card>
  );
};

/**
 * SERENIA ACCOUNTING — components/ui/Card.tsx
 * ==============================================
 * Card container, Badge, and form Input components.
 */

import React, { HTMLAttributes, InputHTMLAttributes, forwardRef, SelectHTMLAttributes } from 'react';

// ── Card ──────────────────────────────────────────────────────
export const Card: React.FC<HTMLAttributes<HTMLDivElement> & { hoverable?: boolean }> = ({
  children, className = '', hoverable, ...props
}) => (
  <div
    className={`
      bg-white dark:bg-surface-dark-elevated
      border border-surface-200 dark:border-surface-dark-border
      rounded-lg shadow-card
      ${hoverable ? 'transition-shadow hover:shadow-card-hover' : ''}
      ${className}
    `}
    {...props}
  >
    {children}
  </div>
);

export const CardHeader: React.FC<HTMLAttributes<HTMLDivElement>> = ({ children, className = '', ...props }) => (
  <div className={`px-5 py-4 border-b border-surface-200 dark:border-surface-dark-border ${className}`} {...props}>
    {children}
  </div>
);

export const CardBody: React.FC<HTMLAttributes<HTMLDivElement>> = ({ children, className = '', ...props }) => (
  <div className={`px-5 py-4 ${className}`} {...props}>
    {children}
  </div>
);

export const CardTitle: React.FC<HTMLAttributes<HTMLHeadingElement>> = ({ children, className = '', ...props }) => (
  <h3 className={`text-base font-semibold text-surface-dark dark:text-white ${className}`} {...props}>
    {children}
  </h3>
);

// ── Badge ─────────────────────────────────────────────────────
type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'info' | 'primary';

const badgeClasses: Record<BadgeVariant, string> = {
  default: 'bg-surface-100 text-surface-dark dark:bg-surface-dark-border dark:text-surface-100',
  success: 'bg-teal-50 text-teal-700 dark:bg-teal-900/30 dark:text-teal-300',
  warning: 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
  danger: 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-300',
  info: 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  primary: 'bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300',
};

export const Badge: React.FC<HTMLAttributes<HTMLSpanElement> & { variant?: BadgeVariant }> = ({
  children, variant = 'default', className = '', ...props
}) => (
  <span
    className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium ${badgeClasses[variant]} ${className}`}
    {...props}
  >
    {children}
  </span>
);

// ── Input ─────────────────────────────────────────────────────
interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  leftAddon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, leftAddon, className = '', id, ...props }, ref) => {
    const inputId = id || props.name;
    return (
      <div className="w-full">
        {label && (
          <label htmlFor={inputId} className="block text-sm font-medium text-surface-dark dark:text-surface-100 mb-1.5">
            {label}
          </label>
        )}
        <div className="relative flex items-center">
          {leftAddon && <span className="absolute left-3 text-surface-300 text-sm">{leftAddon}</span>}
          <input
            ref={ref}
            id={inputId}
            className={`
              w-full rounded-md border bg-white dark:bg-surface-dark
              px-3 py-2 text-sm text-surface-dark dark:text-white
              placeholder:text-surface-300 dark:placeholder:text-surface-dark-border
              focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-primary-400
              transition-colors
              ${error ? 'border-danger' : 'border-surface-200 dark:border-surface-dark-border'}
              ${leftAddon ? 'pl-8' : ''}
              ${className}
            `}
            {...props}
          />
        </div>
        {error && <p className="mt-1 text-xs text-danger">{error}</p>}
        {hint && !error && <p className="mt-1 text-xs text-surface-300">{hint}</p>}
      </div>
    );
  }
);
Input.displayName = 'Input';

// ── Select ────────────────────────────────────────────────────
interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options: Array<{ value: string; label: string }>;
  placeholder?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, options, placeholder, className = '', id, ...props }, ref) => {
    const selectId = id || props.name;
    return (
      <div className="w-full">
        {label && (
          <label htmlFor={selectId} className="block text-sm font-medium text-surface-dark dark:text-surface-100 mb-1.5">
            {label}
          </label>
        )}
        <select
          ref={ref}
          id={selectId}
          className={`
            w-full rounded-md border bg-white dark:bg-surface-dark
            px-3 py-2 text-sm text-surface-dark dark:text-white
            focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-primary-400
            transition-colors
            ${error ? 'border-danger' : 'border-surface-200 dark:border-surface-dark-border'}
            ${className}
          `}
          {...props}
        >
          {placeholder && <option value="">{placeholder}</option>}
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        {error && <p className="mt-1 text-xs text-danger">{error}</p>}
      </div>
    );
  }
);
Select.displayName = 'Select';

// ── Empty State ───────────────────────────────────────────────
export const EmptyState: React.FC<{ icon?: React.ReactNode; title: string; description?: string; action?: React.ReactNode }> = ({
  icon, title, description, action
}) => (
  <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
    {icon && <div className="mb-4 text-surface-300">{icon}</div>}
    <h3 className="text-base font-semibold text-surface-dark dark:text-white">{title}</h3>
    {description && <p className="mt-1.5 text-sm text-surface-300 max-w-sm">{description}</p>}
    {action && <div className="mt-4">{action}</div>}
  </div>
);

// ── Skeleton Loader ───────────────────────────────────────────
export const Skeleton: React.FC<{ className?: string }> = ({ className = 'h-4 w-full' }) => (
  <div className={`animate-pulse bg-surface-100 dark:bg-surface-dark-border rounded ${className}`} />
);

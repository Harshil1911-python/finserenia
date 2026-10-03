/**
 * SERENIA ACCOUNTING — pages/Login.tsx
 * =======================================
 * Authentication entry point. Distinctive split layout:
 * brand panel + login form.
 */

import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { EyeIcon, EyeSlashIcon, ShieldCheckIcon, ChartBarSquareIcon, CubeTransparentIcon } from '@heroicons/react/24/outline';
import { useAuth, normalizeError } from '../contexts/AuthContext';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Card';
import type { LoginRequest } from '../types';

export const Login: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm<LoginRequest>();

  const onSubmit = async (data: LoginRequest) => {
    setError(null);
    setIsSubmitting(true);
    try {
      await login(data);
      const from = (location.state as { from?: string })?.from || '/';
      navigate(from, { replace: true });
    } catch (err) {
      setError(normalizeError(err).message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-surface-50 dark:bg-surface-dark">
      {/* Brand Panel */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-gradient-to-br from-primary-600 via-primary-500 to-teal-500 p-12 flex-col justify-between">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-lg bg-white/15 backdrop-blur flex items-center justify-center text-white font-bold text-xl">S</div>
            <span className="text-2xl font-display font-bold text-white tracking-tight">Serenia</span>
          </div>
        </div>

        <div className="relative z-10">
          <h1 className="text-4xl font-display font-bold text-white leading-tight max-w-md">
            One ledger. Every business. Total clarity.
          </h1>
          <p className="mt-4 text-white/80 max-w-md text-base">
            Manage multi-company accounting, GST, payroll, audits, and inventory —
            all from a single cloud workspace built for accountants.
          </p>

          <div className="mt-10 space-y-4">
            {[
              { icon: ChartBarSquareIcon, text: 'Real-time financial dashboards & reports' },
              { icon: ShieldCheckIcon, text: 'Role-based access with full audit trails' },
              { icon: CubeTransparentIcon, text: 'GST, TDS, payroll & inventory in one place' },
            ].map((f, i) => (
              <div key={i} className="flex items-center gap-3 text-white/90">
                <div className="w-9 h-9 rounded-lg bg-white/10 flex items-center justify-center shrink-0">
                  <f.icon className="w-5 h-5" />
                </div>
                <span className="text-sm">{f.text}</span>
              </div>
            ))}
          </div>
        </div>

        <p className="text-white/60 text-xs relative z-10">© 2026 Serenia Accounting. All rights reserved.</p>

        {/* Decorative grid pattern */}
        <div className="absolute inset-0 opacity-[0.07]" style={{
          backgroundImage: 'radial-gradient(circle, white 1px, transparent 1px)',
          backgroundSize: '24px 24px',
        }} />
      </div>

      {/* Login Form */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-sm">
          <div className="lg:hidden flex items-center gap-2.5 mb-8">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-primary-500 to-teal-500 flex items-center justify-center text-white font-bold">S</div>
            <span className="text-xl font-display font-bold text-surface-dark dark:text-white">Serenia</span>
          </div>

          <h2 className="text-2xl font-display font-bold text-surface-dark dark:text-white">Sign in to your account</h2>
          <p className="mt-1.5 text-sm text-surface-300">Enter your credentials to access your dashboard</p>

          {error && (
            <div className="mt-4 px-3 py-2.5 rounded-md bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-900/40 text-sm text-danger">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4">
            <Input
              label="Email address"
              type="email"
              placeholder="you@company.com"
              autoComplete="email"
              error={errors.email?.message}
              {...register('email', { required: 'Email is required' })}
            />

            <div className="relative">
              <Input
                label="Password"
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••"
                autoComplete="current-password"
                error={errors.password?.message}
                {...register('password', { required: 'Password is required' })}
              />
              <button
                type="button"
                onClick={() => setShowPassword((s) => !s)}
                className="absolute right-3 top-9 text-surface-300 hover:text-surface-dark dark:hover:text-white"
                tabIndex={-1}
              >
                {showPassword ? <EyeSlashIcon className="w-4 h-4" /> : <EyeIcon className="w-4 h-4" />}
              </button>
            </div>

            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center gap-2 text-surface-300">
                <input type="checkbox" className="rounded border-surface-200 text-primary-500 focus:ring-primary-400" />
                Remember me
              </label>
              <a href="/forgot-password" className="font-medium text-primary-500 hover:text-primary-600">Forgot password?</a>
            </div>

            <Button type="submit" className="w-full" size="lg" isLoading={isSubmitting}>
              Sign In
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-surface-300">
            Need access? <a href="mailto:admin@serenia.app" className="font-medium text-primary-500 hover:text-primary-600">Contact your administrator</a>
          </p>
        </div>
      </div>
    </div>
  );
};

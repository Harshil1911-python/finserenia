/**
 * SERENIA ACCOUNTING — pages/NotFound.tsx
 * ==========================================
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/Button';

export const NotFound: React.FC = () => (
  <div className="flex flex-col items-center justify-center py-24 text-center animate-fade-in">
    <p className="text-6xl font-display font-bold text-primary-500">404</p>
    <h1 className="mt-3 text-xl font-semibold text-surface-dark dark:text-white">Page not found</h1>
    <p className="mt-1.5 text-sm text-surface-300 max-w-sm">
      The page you're looking for doesn't exist or has been moved.
    </p>
    <Link to="/" className="mt-5">
      <Button>Back to Dashboard</Button>
    </Link>
  </div>
);

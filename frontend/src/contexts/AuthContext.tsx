/**
 * SERENIA ACCOUNTING — contexts/AuthContext.tsx
 * ================================================
 * Global authentication state: current user, active company,
 * login/logout, and company switching.
 */

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import api, { tokenStorage, normalizeError } from '../services/api';
import type { User, Company, LoginRequest, AuthTokens } from '../types';

interface AuthContextValue {
  user: User | null;
  activeCompany: Company | null;
  companies: Company[];
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
  switchCompany: (companyId: string) => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [activeCompany, setActiveCompany] = useState<Company | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchUser = useCallback(async () => {
    const { data } = await api.get<User>('/auth/me/');
    setUser(data);
    return data;
  }, []);

  const fetchCompanies = useCallback(async () => {
    const { data } = await api.get<Company[]>('/companies/');
    setCompanies(data);
    return data;
  }, []);

  const loadActiveCompany = useCallback(async (companyId: string) => {
    try {
      const { data } = await api.get<Company>(`/companies/${companyId}/`);
      setActiveCompany(data);
      tokenStorage.setActiveCompanyId(data.id);
    } catch {
      // Active company no longer accessible — clear it
      tokenStorage.clear();
    }
  }, []);

  // ── Initial load: restore session ──────────────────────────
  useEffect(() => {
    const init = async () => {
      const token = tokenStorage.getAccess();
      if (!token) {
        setIsLoading(false);
        return;
      }
      try {
        const userData = await fetchUser();
        const companyList = await fetchCompanies();

        const savedCompanyId = tokenStorage.getActiveCompanyId();
        const targetCompany = companyList.find((c) => c.id === savedCompanyId) || companyList[0];

        if (targetCompany) {
          await loadActiveCompany(targetCompany.id);
        }
      } catch {
        tokenStorage.clear();
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };
    init();
  }, [fetchUser, fetchCompanies, loadActiveCompany]);

  // ── Login ────────────────────────────────────────────────────
  const login = useCallback(async (credentials: LoginRequest) => {
    const { data } = await api.post<{ tokens: AuthTokens; user: User }>('/auth/login/', credentials);
    tokenStorage.setTokens(data.tokens.access, data.tokens.refresh);
    setUser(data.user);

    const companyList = await fetchCompanies();
    if (companyList.length > 0) {
      await loadActiveCompany(companyList[0].id);
    }
  }, [fetchCompanies, loadActiveCompany]);

  // ── Logout ───────────────────────────────────────────────────
  const logout = useCallback(() => {
    const refresh = tokenStorage.getRefresh();
    if (refresh) {
      api.post('/auth/logout/', { refresh }).catch(() => {});
    }
    tokenStorage.clear();
    setUser(null);
    setActiveCompany(null);
    setCompanies([]);
    window.location.href = '/login';
  }, []);

  // ── Switch active company ────────────────────────────────────
  const switchCompany = useCallback(async (companyId: string) => {
    await loadActiveCompany(companyId);
  }, [loadActiveCompany]);

  const refreshUser = useCallback(async () => {
    await fetchUser();
  }, [fetchUser]);

  const value: AuthContextValue = {
    user,
    activeCompany,
    companies,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    switchCompany,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextValue => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};

export { normalizeError };

/**
 * SERENIA ACCOUNTING — services/api.ts
 * ======================================
 * Axios instance with JWT auth interceptors, automatic token
 * refresh, and multi-company context header injection.
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// ── Token storage helpers ──────────────────────────────────────
export const tokenStorage = {
  getAccess: () => sessionStorage.getItem('serenia_access_token'),
  getRefresh: () => sessionStorage.getItem('serenia_refresh_token'),
  setTokens: (access: string, refresh: string) => {
    sessionStorage.setItem('serenia_access_token', access);
    sessionStorage.setItem('serenia_refresh_token', refresh);
  },
  clear: () => {
    sessionStorage.removeItem('serenia_access_token');
    sessionStorage.removeItem('serenia_refresh_token');
    sessionStorage.removeItem('serenia_active_company');
  },
  getActiveCompanyId: () => sessionStorage.getItem('serenia_active_company'),
  setActiveCompanyId: (id: string) => sessionStorage.setItem('serenia_active_company', id),
};

// ── Request interceptor: attach JWT + company context ──────────
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStorage.getAccess();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  const companyId = tokenStorage.getActiveCompanyId();
  if (companyId) {
    config.headers['X-Company-Id'] = companyId;
  }
  return config;
});

// ── Response interceptor: auto-refresh on 401 ──────────────────
let isRefreshing = false;
let refreshQueue: Array<() => void> = [];

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = tokenStorage.getRefresh();
      if (!refreshToken) {
        tokenStorage.clear();
        window.location.href = '/login';
        return Promise.reject(error);
      }

      if (isRefreshing) {
        // Queue requests while refresh is in progress
        return new Promise((resolve) => {
          refreshQueue.push(() => resolve(api(originalRequest)));
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const { data } = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
          refresh: refreshToken,
        });
        tokenStorage.setTokens(data.access, refreshToken);
        refreshQueue.forEach((cb) => cb());
        refreshQueue = [];
        isRefreshing = false;
        return api(originalRequest);
      } catch (refreshError) {
        tokenStorage.clear();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// ── Error normalizer ─────────────────────────────────────────
export function normalizeError(error: unknown): { message: string; errors?: Record<string, string[]> } {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data;
    if (typeof data === 'object' && data !== null) {
      if ('error' in data) return { message: String(data.error) };
      if ('detail' in data) return { message: String(data.detail) };
      // Field-level validation errors
      const errors: Record<string, string[]> = {};
      let firstMessage = 'Validation failed';
      Object.entries(data).forEach(([key, val]) => {
        errors[key] = Array.isArray(val) ? val.map(String) : [String(val)];
        if (errors[key][0]) firstMessage = errors[key][0];
      });
      return { message: firstMessage, errors };
    }
    return { message: error.message || 'Network error occurred' };
  }
  return { message: 'An unexpected error occurred' };
}

export default api;

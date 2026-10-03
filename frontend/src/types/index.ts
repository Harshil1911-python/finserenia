/**
 * SERENIA ACCOUNTING — types/index.ts
 * =====================================
 * Shared TypeScript interfaces mirroring Django models.
 * Used across all components and API services.
 */

// ── Enums ─────────────────────────────────────────────────────
export type UserRole = 'super_admin' | 'admin' | 'ca' | 'accountant' | 'auditor' | 'manager' | 'viewer';
export type VoucherType = 'payment' | 'receipt' | 'contra' | 'journal' | 'sales' | 'purchase' | 'credit_note' | 'debit_note';
export type VoucherStatus = 'draft' | 'pending_approval' | 'approved' | 'posted' | 'rejected' | 'cancelled';
export type AccountNature = 'assets' | 'liabilities' | 'capital' | 'income' | 'expenses';

// ── Auth ──────────────────────────────────────────────────────
export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginRequest {
  email: string;
  password: string;
  company_id?: string;
}

export interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  activeCompany: Company | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// ── User ──────────────────────────────────────────────────────
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: UserRole;
  phone?: string;
  qualification?: string;
  membership_number?: string;
  avatar?: string;
  bio?: string;
  is_active: boolean;
  is_verified: boolean;
  date_joined: string;
  timezone: string;
  date_format: string;
  theme: 'light' | 'dark' | 'system';
  company_accesses: UserCompanyAccess[];
}

export interface UserCompanyAccess {
  id: string;
  company_id: string;
  company_name: string;
  company_gstin: string;
  role: UserRole;
  branch_name?: string;
  is_active: boolean;
}

// ── Company ───────────────────────────────────────────────────
export interface Company {
  id: string;
  name: string;
  legal_name: string;
  company_type: string;
  gstin: string;
  pan: string;
  tan: string;
  cin: string;
  email: string;
  phone?: string;
  website?: string;
  address_line1: string;
  address_line2?: string;
  city: string;
  state: string;
  state_code: string;
  pincode: string;
  country: string;
  logo?: string;
  currency: string;
  fiscal_year_start: number;
  accounting_method: 'accrual' | 'cash';
  is_active: boolean;
  created_at: string;
  updated_at: string;
  branches: Branch[];
  financial_years: FinancialYear[];
  current_fy?: FinancialYear;
}

export interface Branch {
  id: string;
  company: string;
  name: string;
  code: string;
  gstin?: string;
  address_line1?: string;
  city?: string;
  state?: string;
  is_head_office: boolean;
  is_active: boolean;
  created_at: string;
}

export interface FinancialYear {
  id: string;
  company: string;
  label: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
  is_closed: boolean;
  closed_at?: string;
}

// ── Ledger ────────────────────────────────────────────────────
export interface LedgerGroup {
  id: string;
  company: string;
  name: string;
  code?: string;
  nature: AccountNature;
  group_type?: string;
  parent?: string;
  parent_name?: string;
  affects_gross_profit: boolean;
  is_system_group: boolean;
  sort_order: number;
  description?: string;
  children?: LedgerGroup[];
  ledger_count?: number;
}

export interface Ledger {
  id: string;
  company: string;
  group: string;
  group_name?: string;
  name: string;
  code?: string;
  alias?: string;
  gstin?: string;
  gst_registration_type?: string;
  is_tds_applicable: boolean;
  tds_rate?: number;
  tds_section?: string;
  opening_balance: string;
  opening_balance_type: 'Dr' | 'Cr';
  is_party_ledger: boolean;
  contact_name?: string;
  email?: string;
  phone?: string;
  credit_limit?: string;
  credit_days: number;
  is_bank_account: boolean;
  bank_name?: string;
  account_number?: string;
  ifsc_code?: string;
  currency: string;
  is_active: boolean;
  description?: string;
  created_at: string;
  current_balance?: string;
  current_balance_type?: 'Dr' | 'Cr';
}

// ── Vouchers / Journal ────────────────────────────────────────
export interface JournalLine {
  id?: string;
  ledger: string;
  ledger_name?: string;
  debit_amount: string;
  credit_amount: string;
  narration?: string;
  cost_center?: string;
  project?: string;
}

export interface JournalEntry {
  id: string;
  company: string;
  financial_year: string;
  branch?: string;
  voucher_type: VoucherType;
  voucher_number: string;
  date: string;
  narration?: string;
  reference?: string;
  party?: string;
  party_name?: string;
  status: VoucherStatus;
  approved_by?: string;
  approved_at?: string;
  currency: string;
  exchange_rate: string;
  is_gst_transaction: boolean;
  is_recurring: boolean;
  attachments: string[];
  lines: JournalLine[];
  total_amount: string;
  created_by?: string;
  created_at: string;
}

// ── Reports ───────────────────────────────────────────────────
export interface TrialBalanceRow {
  ledger_id: string;
  ledger_name: string;
  ledger_code: string;
  group: string;
  nature: AccountNature;
  debit: string;
  credit: string;
  balance: string;
  balance_type: 'Dr' | 'Cr';
}

export interface TrialBalance {
  company: string;
  financial_year: string;
  as_of_date: string;
  rows: TrialBalanceRow[];
  totals: {
    debit: string;
    credit: string;
    difference: string;
    is_balanced: boolean;
  };
}

export interface DashboardSummary {
  revenue: string;
  expenses: string;
  profit: string;
  profit_percent: string;
  cash_position: string;
  receivables: string;
  payables: string;
  tax_liability: string;
  inventory_value: string;
  payroll_this_month: string;
  bank_balance: string;
  recent_transactions: JournalEntry[];
  monthly_trend: Array<{ month: string; revenue: number; expenses: number; profit: number }>;
  top_ledgers_by_balance: Array<{ name: string; balance: string; type: 'Dr' | 'Cr' }>;
}

// ── API Response Wrappers ─────────────────────────────────────
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiError {
  message: string;
  errors?: Record<string, string[]>;
  status: number;
}

// ── Developer Mode ────────────────────────────────────────────
export interface SystemSetting {
  id: string;
  category: string;
  key: string;
  label: string;
  value: string;
  value_type: string;
  description?: string;
  is_public: boolean;
}

export interface Theme {
  id: string;
  name: string;
  is_active: boolean;
  mode: 'light' | 'dark' | 'system';
  color_primary: string;
  color_secondary: string;
  color_accent: string;
  color_danger: string;
  color_success: string;
  color_bg: string;
  color_surface: string;
  color_text: string;
  font_family_heading: string;
  font_family_body: string;
}

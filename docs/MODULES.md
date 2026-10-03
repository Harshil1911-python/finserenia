# Serenia Accounting — Module Dependency Guide

This document maps inter-module dependencies so future development
(human or AI) understands what breaks if a module is disabled, removed,
or refactored.

## Dependency Graph

```
accounts (core)
  └── ledger ────────────────┬─────────────┬──────────────┬───────────────┐
        │                     │             │              │               │
        ▼                     ▼             ▼              ▼               ▼
   taxation              inventory      payroll        banking          audit
        │                     │             │              │               │
        └─────────────────────┴─────────────┴──────────────┴───────────────┘
                                       │
                                       ▼
                                   reports
                                       │
                                       ▼
                                  compliance

developer_mode — standalone, no dependencies on business modules
```

## `apps.accounts` (foundation — required by everything)
Provides: `User`, `Company`, `Branch`, `FinancialYear`,
`UserCompanyAccess`, `AuditLog`.

- Every other app's models FK to `Company` and/or `User`.
- `CompanyContextMiddleware` and `CompanyScopedViewSet` (defined in
  `apps.ledger.views` but used by nearly all apps) depend on
  `UserCompanyAccess` for permission resolution.
- **Cannot be disabled.**

## `apps.ledger` (accounting core — required by most modules)
Provides: `LedgerGroup`, `Ledger`, `JournalEntry`, `JournalLine`,
`CostCenter`, `Project`, `CurrencyRate`, plus the shared
`CompanyScopedViewSet` base class.

Depended on by:
- **taxation**: `GSTTransaction`/`TDSTransaction` are 1:1 with
  `JournalEntry`.
- **inventory**: `PurchaseOrder.supplier` is a `Ledger`;
  `StockEntry.journal_entry` links stock movements to accounting
  entries.
- **payroll**: `PayrollRun.journal_entry` (the consolidated payroll
  posting); `apps.payroll.tasks.process_payroll_run` looks up specific
  ledgers by name (`"Salaries"`, `"PF Payable"`, etc.) — **renaming
  these system ledgers breaks payroll posting**.
- **banking**: `BankStatementLine.matched_journal_line` →
  `JournalLine`; reconciliation requires `Ledger.is_bank_account=True`.
- **reports**: all report views (`TrialBalanceView`, `ProfitAndLossView`,
  `BalanceSheetView`, `LedgerReportView`) query `JournalLine` and
  `LedgerGroup.nature`/`affects_gross_profit` directly.
- **core.dashboard**: `DashboardSummaryView` aggregates `JournalLine`
  and `Ledger.get_balance()`.

**`apps.ledger.bootstrap.create_standard_chart_of_accounts`** runs on
company creation (`CompanyViewSet.perform_create`) and seeds the ledger
names that `apps.payroll.tasks` and `apps.core.urls.dashboard` rely on
by string match (e.g. `name__icontains='Salaries'`,
`name__iregex=r'(gst|igst|cgst|sgst|tds)'`). If you change the seed
template in `bootstrap.py`, update those lookups too.

## `apps.taxation`
Depends on: `ledger` (JournalEntry, Ledger), `accounts` (FinancialYear).
Independent of: inventory, payroll, banking, audit.
Feeds: `reports` (tax liability is included in dashboard summary via
ledger name matching, not a direct FK).

## `apps.inventory`
Depends on: `ledger` (Ledger for suppliers, JournalEntry for stock
postings — currently optional/nullable FK).
Independent of: taxation, payroll, banking, audit, compliance.
The dashboard's `inventory_value` KPI sums `Item.purchase_price` — a
simplification; a production system should value stock via
`StockEntry` aggregation per `valuation_method`.

## `apps.payroll`
Depends on: `ledger` (posts consolidated journal via Celery task),
`accounts` (FinancialYear, User for employee linkage).
**Celery dependency**: `process_payroll_run` and
`send_payslip_notifications` run on the `payroll` queue — the `celery`
worker service must be running for payroll processing to complete
(the API call only enqueues the task and returns a `task_id`).
Independent of: taxation, inventory, banking, audit.

## `apps.banking`
Depends on: `ledger` (Ledger.is_bank_account, JournalLine for matching).
CSV import (`upload_csv`) is synchronous for simplicity; for large
statements, move parsing to a Celery task on the `reports` queue.
Independent of: taxation, inventory, payroll, audit.

## `apps.audit`
Depends on: `accounts` (FinancialYear, User — `lead_auditor`,
`team_members`).
Loosely coupled to `ledger` — `materiality_threshold` is a plain
decimal, not derived from ledger balances (future enhancement could
compute suggested materiality from `BalanceSheetView` totals).
Permission-gated by `CanAccessAuditModule` (ca/auditor/admin/
super_admin only).

## `apps.compliance`
Depends on: `accounts` (Company, User). Conceptually related to
`apps.taxation` (GST/TDS filing deadlines) and `apps.audit` (ROC
filings) but has **no FK dependency** — `ComplianceTask.category`
is a free-text choice field. A future integration could auto-create
`ComplianceTask` rows when a `GSTRFiling` or `TDSTransaction` return
period opens (via `celery_beat`).

## `apps.reports`
Has **no models** — purely a view layer over `apps.ledger` and
`apps.accounts`. Removing any ledger model breaks the corresponding
report. PDF/Excel generation (`apps.reports.generators`) depends on
`reportlab` and `openpyxl` (see `requirements.txt`).

## `apps.developer_mode`
**Fully independent.** No FKs to business modules. Safe to disable
(`ENABLE_DEVELOPER_MODE=False`) without breaking accounting
functionality — only removes the Super Admin customization UI.
`SystemSetting.get()`/`Theme.active()` are read by the frontend at
boot for branding; if unavailable, the frontend should fall back to
hardcoded defaults (current frontend does this via
`tailwind.config.js` defaults).

## Frontend Module Map

`frontend/src/App.tsx` routes correspond 1:1 with backend apps:

| Route prefix | Backend app | Page components |
|---|---|---|
| `/ledger/*` | `apps.ledger` | `ChartOfAccounts`, `LedgerList`, `JournalList` |
| `/vouchers/*` | `apps.ledger` (JournalEntry) | `VoucherForm` |
| `/reports/*` | `apps.reports` | `TrialBalanceReport`, `ProfitAndLossReport`, `BalanceSheetReport` |
| `/taxation/*` | `apps.taxation` | *(stubs — implement next)* |
| `/inventory/*` | `apps.inventory` | *(stubs — implement next)* |
| `/banking/*` | `apps.banking` | *(stubs — implement next)* |
| `/payroll/*` | `apps.payroll` | *(stubs — implement next)* |
| `/audit/*` | `apps.audit` | *(stubs — implement next)* |
| `/compliance/*` | `apps.compliance` | *(stubs — implement next)* |
| `/companies` | `apps.accounts` | `CompaniesPage` |
| `/developer` | `apps.developer_mode` | `DeveloperMode` |
| `/settings` | `apps.accounts` (User) | `SettingsPage` |

When implementing a stub page, follow the existing pattern in
`LedgerList.tsx` / `JournalList.tsx`: TanStack Query for data fetching,
`Card`/`Badge`/`Skeleton`/`EmptyState` from `components/ui/Card.tsx`,
and `Button` from `components/ui/Button.tsx`.

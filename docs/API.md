# Serenia Accounting — API Reference

Base URL: `/api/v1/`
All endpoints (except `/auth/login/`, `/auth/token/refresh/`,
`/health/`, and `/developer/public-settings/`) require:

```
Authorization: Bearer <access_token>
X-Company-Id: <company_uuid>   (required for company-scoped resources)
```

Interactive Swagger UI is available at `/api/docs/` (schema at
`/api/schema/`).

---

## Authentication

| Method | Path | Description |
|---|---|---|
| POST | `/auth/login/` | `{email, password}` → `{tokens: {access, refresh}, user}` |
| POST | `/auth/logout/` | `{refresh}` → blacklists refresh token |
| POST | `/auth/token/refresh/` | `{refresh}` → `{access}` |
| GET | `/auth/me/` | Current user profile + company accesses |
| PATCH | `/auth/me/` | Update own profile fields |
| POST | `/auth/change-password/` | `{current_password, new_password, confirm_password}` |

## Companies & Users

| Method | Path | Description |
|---|---|---|
| GET/POST | `/companies/` | List/create companies (scoped to user access) |
| GET/PUT/PATCH/DELETE | `/companies/{id}/` | Company detail |
| POST | `/companies/{id}/grant_access/` | `{user_id, company_id, role, branch_id?}` |
| GET | `/companies/{id}/users/` | Users with access to this company |
| GET/POST | `/companies/branches/` | Branches (X-Company-Id scoped) |
| GET/POST | `/companies/financial-years/` | Financial years |
| POST | `/companies/financial-years/{id}/close/` | Close FY for postings |
| GET/POST | `/users/` | Platform users (admin/super_admin only) |

## Ledger & Chart of Accounts

| Method | Path | Description |
|---|---|---|
| GET/POST | `/ledger/groups/` | Ledger groups; `?tree=true` for hierarchy |
| GET/POST | `/ledger/ledgers/` | Ledgers; filters: `is_party_ledger`, `is_bank_account`, `nature`, `search` |
| GET | `/ledger/ledgers/{id}/reconcile_statement/` | Bank ledger transaction list for reconciliation |
| GET/POST | `/cost-centers/` | Cost centers |
| GET/POST | `/cost-centers/projects/` | Projects |
| GET/POST | `/ledger/currency-rates/` | Exchange rates |

## Journal Entries & Vouchers

| Method | Path | Description |
|---|---|---|
| GET/POST | `/journals/` | List/create. Filters: `voucher_type`, `status`, `date_after`, `date_before` |
| GET/PUT/PATCH | `/journals/{id}/` | Detail (immutable once posted) |
| POST | `/journals/{id}/approve/` | Approve & post (requires CanApproveVouchers) |
| POST | `/journals/{id}/reject/` | `{reason}` — reject pending entry |
| * | `/vouchers/...` | Alias of `/journals/` for voucher-type-specific UIs |

**Create payload:**
```json
{
  "voucher_type": "payment",
  "date": "2026-06-13",
  "narration": "Office rent for June",
  "reference": "CHQ-001234",
  "status": "pending_approval",
  "lines": [
    {"ledger": "<uuid>", "debit_amount": "25000.00", "credit_amount": "0"},
    {"ledger": "<uuid>", "debit_amount": "0", "credit_amount": "25000.00"}
  ]
}
```

## Reports

| Method | Path | Description |
|---|---|---|
| GET | `/reports/trial-balance/?as_of_date=&format=json\|pdf\|excel` | Trial balance |
| GET | `/reports/profit-and-loss/?fy_id=` | P&L statement |
| GET | `/reports/balance-sheet/?fy_id=` | Balance sheet |
| GET | `/reports/ledger/{ledger_id}/?from_date=&to_date=` | Ledger statement with running balance |

## Taxation

| Method | Path | Description |
|---|---|---|
| GET/POST | `/taxation/gst-transactions/` | GST transaction records |
| GET | `/taxation/gst-transactions/gstr1_summary/?period=MMYYYY` | GSTR-1 summary by supply type |
| GET | `/taxation/gst-transactions/gstr3b_summary/?period=MMYYYY` | GSTR-3B outward/ITC summary |
| GET/POST | `/taxation/gstr-filings/` | Filing tracker |
| POST | `/taxation/gstr-filings/{id}/mark_filed/` | `{arn_number}` |
| GET/POST | `/taxation/tds-transactions/` | TDS records |
| GET | `/taxation/tds-transactions/section_summary/` | TDS by section |

## Payroll

| Method | Path | Description |
|---|---|---|
| GET/POST | `/payroll/employees/` | Employee master |
| GET/POST | `/payroll/salary-structures/` | Salary structure templates |
| GET/POST | `/payroll/runs/` | Payroll runs |
| POST | `/payroll/runs/{id}/process/` | Triggers Celery payroll processing → `{task_id}` |

## Inventory

| Method | Path | Description |
|---|---|---|
| GET/POST | `/inventory/items/` | Item master; `search`, `category`, `item_type` |
| GET | `/inventory/items/low_stock/` | Items at/below reorder level |
| GET/POST | `/inventory/categories/`, `/units/`, `/warehouses/` | Supporting masters |
| GET/POST | `/inventory/stock-entries/` | Stock in/out/transfer/adjustment |
| GET/POST | `/inventory/purchase-orders/` | PO with line items |
| POST | `/inventory/purchase-orders/{id}/receive/` | `{lines: [{line_id, quantity}], date}` |

## Banking

| Method | Path | Description |
|---|---|---|
| GET/POST | `/banking/statement-imports/` | Bank statement import batches |
| POST | `/banking/statement-imports/{id}/upload_csv/` | Multipart CSV upload |
| GET | `/banking/statement-lines/` | Filter by `match_status`, `statement_import` |
| POST | `/banking/statement-lines/{id}/confirm_match/` | `{journal_line_id?}` |
| POST | `/banking/statement-lines/{id}/ignore/` | Mark line as ignored |

## Audit (CA/Auditor/Admin/Super Admin only)

| Method | Path | Description |
|---|---|---|
| GET/POST | `/audit/plans/` | Audit plans |
| GET | `/audit/plans/{id}/report/` | Consolidated audit report summary |
| GET/POST | `/audit/risk-assessments/` | Risk assessments |
| GET/POST | `/audit/working-papers/` | Working papers |
| POST | `/audit/working-papers/{id}/review/` | `{comments}` |
| GET/POST | `/audit/checklist-items/` | Compliance checklist |
| POST | `/audit/checklist-items/{id}/mark_checked/` | `{status, remarks}` |
| GET/POST | `/audit/observations/` | Audit observations |
| POST | `/audit/observations/{id}/resolve/` | `{management_response}` |

## Compliance

| Method | Path | Description |
|---|---|---|
| GET/POST | `/compliance/tasks/` | Compliance tasks; filters: `category`, `status`, `frequency` |
| GET | `/compliance/tasks/upcoming/` | Tasks due in next 30 days + overdue |
| POST | `/compliance/tasks/{id}/mark_filed/` | `{reference_number}` |

## Dashboard

| Method | Path | Description |
|---|---|---|
| GET | `/dashboard/summary/` | KPIs, trends, recent transactions (cached 5 min) |

## Developer Mode (Super Admin only)

| Method | Path | Description |
|---|---|---|
| GET/PATCH | `/developer/settings/{key}/` | System settings |
| GET | `/developer/public-settings/` | Public branding settings (no auth) |
| GET/POST/PATCH | `/developer/theme/` | Theme profiles |
| GET | `/developer/theme/active/` | Active theme (no auth) |
| POST | `/developer/theme/{id}/activate/` | Set as active theme |
| GET/POST | `/developer/navigation/` | Navigation menu items |
| GET | `/developer/navigation/public/?location=header\|footer` | Public nav (no auth) |
| GET/POST/PATCH | `/developer/content/{section}/` | Landing page CMS content |
| GET | `/developer/content/public/` | Public page content (no auth) |

---

## Error Format

```json
{ "error": "Human-readable message" }
```
or for field validation errors:
```json
{ "field_name": ["Error detail 1", "Error detail 2"] }
```

## Pagination

List endpoints return:
```json
{ "count": 123, "next": "...", "previous": null, "results": [...] }
```
Use `?page=` and `?page_size=` (max 500).

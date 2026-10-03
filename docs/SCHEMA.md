# Serenia Accounting — Database Schema Documentation

PostgreSQL 15. All primary keys are UUIDs (`uuid4`). Money fields use
`DECIMAL(20,2)` (or `(5,2)` for rates/percentages) — never floats.

## Core / Accounts (`apps.accounts`)

### `auth_users`
Custom user model (`AUTH_USER_MODEL = accounts.User`), email as username.
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| email | varchar, unique, indexed | |
| first_name, last_name | varchar | |
| role | varchar(20) | super_admin / admin / ca / accountant / auditor / manager / viewer |
| phone | phonenumber | |
| qualification, membership_number | varchar | CA/ICAI details |
| is_active, is_staff, is_verified | bool | |
| failed_login_attempts, locked_until | int, datetime | brute-force lockout |
| timezone, date_format, theme | varchar | user preferences |

### `companies`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| name, legal_name | varchar | |
| company_type | varchar(20) | pvt_ltd / pub_ltd / partnership / proprietorship / llp / ngo / trust / other |
| gstin, pan, tan, cin | varchar | India tax identifiers, indexed (gstin) |
| address fields, state_code, pincode, country | varchar | |
| logo | image | |
| currency | varchar(3) | default INR |
| fiscal_year_start | int | month number, default 4 (April) |
| accounting_method | varchar | accrual / cash |
| created_by | FK → auth_users | |

### `branches`
FK `company`. Unique `(company, code)`. `is_head_office` flag.

### `financial_years`
FK `company`. Unique `(company, label)`. `start_date`, `end_date`,
`is_current`, `is_closed`, `closed_by` FK → auth_users.

### `user_company_access`
Maps `user` ↔ `company` with a `role` (per-company role override),
optional `branch` FK, `permissions` JSONB for granular overrides.
Unique `(user, company)`.

### `audit_logs`
Immutable. FK `user`, `company` (nullable — survives deletion via
SET_NULL). `action`, `model_name`, `object_id`, `object_repr`,
`changes` JSONB, `ip_address`, `user_agent`, `timestamp` (indexed).

---

## Ledger (`apps.ledger`)

### `ledger_groups`
Self-referential hierarchy (`parent` FK → self, PROTECT). FK `company`.
| Column | Notes |
|---|---|
| nature | assets / liabilities / capital / income / expenses |
| group_type | e.g. current_assets, sales, indirect_expenses (see `AccountGroup`) |
| affects_gross_profit | bool — determines Trading A/C vs P&L placement |
| is_system_group | bool — seeded groups, protected from deletion |

Unique `(company, name)`.

### `ledgers`
The individual chart-of-accounts entries. FK `company`, `group`
(PROTECT). Unique `(company, name)`.
Key fields: `opening_balance` + `opening_balance_type` (Dr/Cr),
`is_party_ledger` (customer/supplier), `is_bank_account` +
bank details, `is_tds_applicable` + `tds_rate`/`tds_section`,
`gstin`, `currency`, `credit_limit`/`credit_days`.

Indexes: `(company, name)`, `(company, code)`, `is_party_ledger`,
`is_bank_account`.

### `journal_entries`
The voucher header. FK `company`, `financial_year` (PROTECT), `branch`,
`party` (Ledger, nullable). Unique `(company, voucher_type,
voucher_number)`.
| Column | Notes |
|---|---|
| voucher_type | payment / receipt / contra / journal / sales / purchase / credit_note / debit_note / opening_balance |
| status | draft / pending_approval / approved / posted / rejected / cancelled |
| voucher_number | auto-generated: `{TYPE_PREFIX}-{FY}-{seq:05d}` |
| currency, exchange_rate | multi-currency support |
| is_gst_transaction, gst_data | JSONB |
| is_recurring, recurring_config | JSONB; `parent_recurring` self-FK |
| attachments | JSONB array of file URLs |

Indexes: `(company, date)`, `(company, voucher_type, date)`, `status`,
`(financial_year, date)`.

### `journal_lines`
FK `journal` (CASCADE), `ledger` (PROTECT), optional `cost_center`,
`project`. Exactly one of `debit_amount`/`credit_amount` is non-zero
(enforced in serializer). GST fields: `gst_category`, `tax_rate`.
Multi-currency: `foreign_currency`, `foreign_amount`.

Indexes: `(ledger, journal)`, `journal`.

### `cost_centers`, `projects`
Department/profit-center and project-wise cost allocation, referenced
from `journal_lines`.

### `currency_rates`
FK `company`. Unique `(company, from_currency, to_currency, date)`.

---

## Taxation (`apps.taxation`)

### `gst_transactions`
One-to-one with `journal_entries`. FK `company`, `financial_year`.
Captures party GSTIN/state, `supply_type` (b2b/b2cl/b2cs/exports/nil/cdn),
HSN/SAC, taxable value, CGST/SGST/IGST/CESS rates & amounts (auto-computed
`total_tax` on save), ITC eligibility, and GSTR-1/3B filing period flags.

### `gstr_filings`
FK `company`. Unique `(company, return_type, period)`. Tracks
draft/ready/filed/error status, ARN number, filing date.

### `tds_transactions`
FK `company`, `financial_year`, optional `journal` (1:1). Deductee
ledger + PAN, `section` (194C/194J/194I/etc.), rate, computed
`total_tax_deducted`, challan/deposit tracking, Form 16 status.

---

## Payroll (`apps.payroll`)

### `employees`
FK `company`, optional `user` (1:1, links to platform login).
Personal/employment fields, FK `salary_structure`, bank & statutory
(PF/ESI/UAN) numbers. Unique `(company, employee_code)`.

### `salary_structures`
FK `company`. Percentage-based CTC breakdown (basic/HRA/special as % of
CTC), fixed transport/medical allowances, PF/ESI/PT applicability flags.

### `payroll_runs`
FK `company`, `financial_year`. Unique `(company, month, year)`.
Aggregates `total_gross`/`total_deductions`/`total_net`, links to the
consolidated `journal_entry` (1:1) created on processing.

### `payslips`
FK `payroll_run` (CASCADE), `employee` (PROTECT). Unique
`(payroll_run, employee)`. Full earnings/deductions breakdown,
`net_salary`, `is_paid`.

---

## Inventory (`apps.inventory`)

### `items`
FK `company`, optional `category`, `unit`/`alternate_unit`. Pricing
(purchase/selling/MRP), GST (`hsn_sac_code`, `gst_rate`), valuation
method (FIFO/LIFO/weighted_avg/specific), `reorder_level`,
batch/serial tracking flags. Unique `(company, code)`.

### `item_categories`, `units`, `warehouses`
Supporting masters, FK `company`.

### `stock_entries`
FK `company`, `item` (PROTECT), `warehouse` (PROTECT), optional
`destination_warehouse` (for transfers), optional `journal_entry`.
`entry_type`: in / out / transfer / adjustment / opening. `amount` =
`quantity * rate` (computed on save).

### `purchase_orders` + `purchase_order_lines`
FK `company`, `supplier` (Ledger, PROTECT), `warehouse` (PROTECT).
Unique `(company, po_number)`. Lines track `received_quantity` for
partial-receipt status.

---

## Banking (`apps.banking`)

### `bank_statement_imports`
FK `company`, `bank_ledger`. Tracks CSV upload metadata, status,
total/matched record counts.

### `bank_statement_lines`
FK `statement_import` (CASCADE). `match_status`: unmatched / matched /
suggested / ignored. Optional `matched_journal_line` FK →
`journal_lines`.

---

## Audit (`apps.audit`)

### `audit_plans`
FK `company`, `financial_year` (PROTECT). `audit_type`: statutory /
internal / tax / gst / stock / special. M2M `team_members` → users.

### `audit_risk_assessments`, `audit_working_papers`,
### `audit_compliance_checklist`, `audit_observations`
All FK `audit_plan` (CASCADE). Working papers have unique
`(audit_plan, reference_number)`. Observations have `severity`
(low/medium/high/critical) and workflow `status` (open → 
management_response → resolved → closed).

---

## Compliance (`apps.compliance`)

### `compliance_tasks`
FK `company`, optional `assigned_to`/`completed_by`. `category`: gst /
tds / income_tax / roc / pf_esi / professional_tax / other. `frequency`:
monthly / quarterly / half_yearly / annually / one_time. Indexed
`(company, due_date, status)` for the upcoming-deadlines dashboard.

---

## Developer Mode (`apps.developer_mode`)

### `system_settings`
Generic key-value store. Unique `key`. `category` groups settings
(branding/theme/features/smtp/security/storage/api/content/landing/
navigation/seo/integrations). `is_public` exposes the value via
`/developer/public-settings/` without auth. Cached in Redis
(`SystemSetting.get()`/`.set()`).

### `themes`
Only one row has `is_active=True` at a time (enforced in `save()`).
Full color palette (primary/secondary/accent/danger/success + light &
dark surface colors), typography (`font_family_heading/body`,
`font_size_base`), border radii.

### `navigation_items`
Self-referential (`parent`) for nested menus. `location`:
header/footer/both.

### `page_content`
Unique `section` (hero/features/pricing/testimonials/cta/about/
contact/footer/faq/announcement). `body` JSONB for flexible structured
content (lists, rich text blocks, etc.).

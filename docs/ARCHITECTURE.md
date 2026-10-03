# Serenia Accounting — Architecture Documentation

## Overview

Serenia Accounting is a multi-tenant (multi-company) cloud ERP built as a
decoupled SPA + REST API. The frontend (React/TypeScript) communicates with
the backend (Django REST Framework) exclusively via versioned JSON APIs
under `/api/v1/`.

```
┌──────────────────┐        HTTPS / JSON         ┌───────────────────────┐
│  React SPA (TS)  │ ───────────────────────────▶│  Django REST API      │
│  Nginx static     │ ◀─────────────────────────  │  (Gunicorn)           │
└──────────────────┘                              └─────────┬─────────────┘
                                                              │
                  ┌───────────────────────────────────────────┼──────────────┐
                  │                                           │              │
           ┌──────▼──────┐                            ┌───────▼──────┐ ┌─────▼─────┐
           │ PostgreSQL  │                            │     Redis     │ │  Celery   │
           │ (primary DB)│                            │ cache+broker  │ │  workers  │
           └─────────────┘                            └───────────────┘ └───────────┘
```

## Multi-Company Data Model

Every business-data model (Ledger, JournalEntry, Item, Employee, etc.) has
a `company = ForeignKey(Company)` field. The frontend sends the active
company's UUID in the `X-Company-Id` header on every request.

- `CompanyContextMiddleware` resolves this header into `request.company`
  and verifies the authenticated user has an active `UserCompanyAccess`
  record for that company (Super Admins bypass this check).
- All viewsets extend `CompanyScopedViewSet` (in `apps.ledger.views`),
  which filters querysets by `company_id` from the header and auto-injects
  it on create.

## Authentication & Authorization

- **JWT** via `djangorestframework-simplejwt`. Access tokens last 60
  minutes (configurable), refresh tokens 7 days, with rotation and
  blacklisting on logout.
- **Roles** (`apps.accounts.models.UserRole`): `super_admin`, `admin`, `ca`,
  `accountant`, `auditor`, `manager`, `viewer`. A single user can hold
  different roles in different companies via `UserCompanyAccess`.
- **Permission classes** (`apps.core.permissions`):
  - `CompanyPermission` — requires valid company context
  - `CanApproveVouchers` — admin/ca/manager/super_admin
  - `CanAccessAuditModule` — ca/auditor/admin/super_admin
  - `IsSuperAdmin` — Developer Mode only
  - `IsReadOnlyOrViewerSafe` — viewers get read-only access

## Double-Entry Accounting Engine

`apps.ledger.models.JournalEntry` + `JournalLine` implement double-entry
bookkeeping:
- Every entry has 2+ lines; the sum of `debit_amount` must equal the sum
  of `credit_amount` (enforced in `JournalEntrySerializer.validate_lines`
  and `JournalEntry.clean()`).
- Entries start as `draft` → `pending_approval` → `approved`/`posted`
  (or `rejected`). Only users with `CanApproveVouchers` can approve.
- Once `posted`/`approved`, entries are immutable (edits raise
  `ValidationError` — corrections require a reversing entry).
- `Ledger.get_balance()` computes running balances by summing posted
  `JournalLine` debit/credit plus `opening_balance`.

## Caching Strategy (Redis)

| Cache key pattern              | TTL    | Invalidated on                          |
|---------------------------------|--------|------------------------------------------|
| `dashboard_summary:{company_id}`| 5 min  | New/approved journal entries, ledger edits|
| `trial_balance:{company_id}:*`  | 10 min | Ledger/journal mutations                  |
| `sys_setting:{key}`             | 1 hour | SystemSetting.set() / viewset update      |
| `active_theme`                  | 1 hour | Theme.save()                              |

Sessions also use the Redis cache backend (`SESSION_ENGINE =
django.contrib.sessions.backends.cache`).

## Background Jobs (Celery)

Three queues, routed via `CELERY_TASK_ROUTES`:
- `reports` — heavy PDF/Excel generation, scheduled backups
- `payroll` — `apps.payroll.tasks.process_payroll_run` (payslip calculation
  + consolidated journal posting + email notifications)
- `notifications` — transactional emails, compliance reminders

`django_celery_beat` provides the scheduler for recurring tasks (e.g.
nightly backups, compliance deadline reminders) configured via Django admin
or a data migration.

## Developer Mode

Super-Admin-only panel (`apps.developer_mode`) backed by:
- `SystemSetting` — generic key/value config (branding, SMTP, feature
  flags, security), cached in Redis, with a `is_public` flag exposing
  non-sensitive values to the unauthenticated landing page via
  `/api/v1/developer/public-settings/`.
- `Theme` — color palette, typography, mode (light/dark). Only one theme
  is `is_active` at a time; `/api/v1/developer/theme/active/` is a public
  endpoint the frontend polls to apply CSS variables app-wide.
- `NavigationItem`, `PageContent` — CMS for the public marketing site.

## Frontend Architecture

- **State**: `AuthContext` (user, active company, companies list, JWT
  lifecycle) + `ThemeContext` (dark/light mode, persisted to
  `localStorage`). Server state via TanStack Query (`@tanstack/react-query`).
- **API layer** (`services/api.ts`): single Axios instance with request
  interceptor injecting `Authorization` and `X-Company-Id` headers, and a
  response interceptor that transparently refreshes expired access tokens
  (queuing concurrent requests during refresh).
- **Routing**: React Router v6, all authenticated routes wrapped in
  `AppLayout` (Sidebar + Topbar). `SuperAdminRoute` gates `/developer`.
- **Design system**: Tailwind CSS with a custom palette (`primary` = purple
  `#6C5CE7`, `teal` = `#00B894`) defined in `tailwind.config.js`. Dark mode
  via the `class` strategy.

## Continuing Development

Each Django app under `backend/apps/` is self-contained: `models.py`,
`serializers.py` (or `views.py` for `reports`), and a `urls.py`/`urls/`
package wired into `config/urls.py`. To add a new module:

1. Create `apps/<name>/{models,serializers,urls}.py` following the
   `CompanyScopedViewSet` pattern in `apps.ledger.views`.
2. Add `'apps.<name>'` to `LOCAL_APPS` in `config/settings/production.py`.
3. Wire `path('api/v1/<name>/', include('apps.<name>.urls'))` in
   `config/urls.py`.
4. Run `python manage.py makemigrations <name> && migrate`.
5. On the frontend, add types to `src/types/index.ts`, a page under
   `src/pages/<name>/`, and a route in `src/App.tsx`.

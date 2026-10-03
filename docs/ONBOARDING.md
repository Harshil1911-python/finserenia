# Serenia Accounting — Developer Onboarding

Welcome. This guide gets a new developer (or AI agent) productive on
the Serenia Accounting codebase quickly.

## 1. Local Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt --break-system-packages  # or omit flag inside venv

cp ../.env.example ../.env
# Edit .env: set DATABASE_URL to a local Postgres, REDIS_URL to local Redis
export DJANGO_SETTINGS_MODULE=config.settings.development

python manage.py migrate
python manage.py seed_initial_data
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
# Create .env.local with: REACT_APP_API_URL=http://localhost:8000/api/v1
npm start
```

### Full stack (Docker)
```bash
docker-compose up --build
```
See [DEPLOYMENT.md](DEPLOYMENT.md) for details.

## 2. Codebase Tour

```
serenia/
├── backend/
│   ├── config/                  # Django project: settings, urls, celery, wsgi
│   │   └── settings/
│   │       ├── production.py    # ALL settings live here
│   │       └── development.py   # local overrides (DEBUG=True etc.)
│   ├── apps/
│   │   ├── core/                 # Middleware, permissions, pagination, exceptions, dashboard
│   │   ├── accounts/              # User, Company, Branch, FinancialYear, auth views
│   │   ├── ledger/                 # Chart of Accounts, Journals, Vouchers (THE CORE)
│   │   ├── taxation/               # GST, TDS
│   │   ├── payroll/                # Employees, payroll runs (+ Celery tasks)
│   │   ├── inventory/              # Items, warehouses, purchase orders
│   │   ├── banking/                 # Statement import & reconciliation
│   │   ├── audit/                   # Audit plans, working papers, observations
│   │   ├── compliance/              # Filing calendar
│   │   ├── reports/                  # Trial Balance / P&L / Balance Sheet (view-only, no models)
│   │   └── developer_mode/           # Super Admin branding/theme/settings
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── types/index.ts          # Shared TS interfaces — mirror Django serializers
│       ├── services/api.ts          # Axios instance + JWT refresh logic
│       ├── contexts/                 # AuthContext, ThemeContext
│       ├── components/
│       │   ├── ui/                    # Button, Card, Input, Select, Badge, Skeleton...
│       │   ├── layout/                 # Sidebar, Topbar, AppLayout
│       │   └── dashboard/               # KPICard
│       └── pages/                       # One folder per module
├── docker/                                # Dockerfiles
├── docs/                                   # You are here
├── docker-compose.yml
├── render.yaml
└── .env.example
```

## 3. Key Conventions

### Backend
- **Every business model has `company = ForeignKey(Company)`.** New
  models must follow this.
- **Use `CompanyScopedViewSet`** (in `apps.ledger.views`) as the base
  class for new viewsets — it handles `X-Company-Id` filtering and
  injection automatically. Set `company_field = None` if the model is
  scoped via a parent FK instead (see `apps.audit.serializers`).
- **UUID primary keys everywhere**: `models.UUIDField(primary_key=True,
  default=uuid.uuid4, editable=False)`.
- **Money = `DecimalField(max_digits=20, decimal_places=2)`**. Never
  use `FloatField` for currency.
- **Audit everything**: state-changing actions should call
  `AuditLog.objects.create(...)` (see examples in
  `apps.ledger.views.JournalEntryViewSet`).
- **Cache invalidation**: any write that affects dashboard/report
  numbers must `cache.delete(f"dashboard_summary:{company_id}")` (see
  `LedgerViewSet._invalidate_dashboard_cache`).

### Frontend
- **TanStack Query for all server data** — `useQuery`/`useMutation`,
  never raw `useEffect` + `fetch`.
- **`api` instance from `services/api.ts`** — never instantiate axios
  directly; it handles auth headers and token refresh.
- **UI components from `components/ui/Card.tsx` and `Button.tsx`** —
  don't write raw `<button>`/`<div className="card">`; reuse `Card`,
  `Badge`, `Input`, `Select`, `EmptyState`, `Skeleton`.
- **Formatting**: use the local `formatCurrency` helper pattern (seen
  in `Dashboard.tsx`, `TrialBalanceReport.tsx`) —
  `Intl.NumberFormat('en-IN', { style: 'currency', currency, ... })`.
- **Tailwind only** — colors come from `tailwind.config.js`
  (`primary`, `teal`, `surface`, `danger`, etc.). Dark mode via
  `dark:` variants (class strategy).

## 4. Adding a New Feature — Worked Example

Say you need to implement **"Sales Orders"** (currently a stub route).

1. **Model** (`apps/inventory/models.py`): add `SalesOrder` +
   `SalesOrderLine`, mirroring `PurchaseOrder`/`PurchaseOrderLine` but
   with `customer` instead of `supplier`.
2. **Migration**: `python manage.py makemigrations inventory`
3. **Serializer + ViewSet** (`apps/inventory/serializers.py`): copy
   `PurchaseOrderSerializer`/`PurchaseOrderViewSet` pattern — auto
   voucher numbering (`SO-00001`), line-level tax calculation.
4. **URL**: register in `apps/inventory/urls.py` router.
5. **Frontend type**: add `SalesOrder`/`SalesOrderLine` to
   `frontend/src/types/index.ts`.
6. **Frontend page**: create `frontend/src/pages/inventory/
   SalesOrderList.tsx` and `SalesOrderForm.tsx`, following
   `JournalList.tsx`/`VoucherForm.tsx` patterns.
7. **Route**: replace the stub in `App.tsx`:
   ```tsx
   <Route path="inventory/sales-orders" element={<SalesOrderList />} />
   ```
8. **Sidebar**: already has the nav entry (`Sidebar.tsx` →
   Inventory → Sales Orders) — no change needed.

## 5. Testing

- Backend: `pytest` (configured via `pytest-django`,
  `factory-boy`/`Faker` available for fixtures). Place tests in
  `apps/<name>/tests/`.
- Run: `pytest apps/ledger/`

## 6. Common Pitfalls

- **Forgetting `X-Company-Id` header** → `CompanyScopedViewSet`
  returns an empty queryset (not an error) if the header is missing.
  Always check `activeCompany` is set on the frontend before querying.
- **Editing posted journal entries** → raises `ValidationError` by
  design (`JournalEntrySerializer.update`). Create a reversing entry
  instead.
- **Renaming seed ledgers** (`bootstrap.py`) → breaks string-matching
  lookups in `apps.payroll.tasks` and `apps.core.urls.dashboard`. See
  [MODULES.md](MODULES.md).
- **New Celery tasks** → must be added to `CELERY_TASK_ROUTES` in
  `production.py` if they need a specific queue, and the relevant
  worker (`celery` service in `docker-compose.yml`) must listen on
  that queue (`-Q default,reports,payroll,notifications`).

## 7. Where to Go Next

- [ARCHITECTURE.md](ARCHITECTURE.md) — system design, caching, auth
- [API.md](API.md) — full endpoint reference
- [SCHEMA.md](SCHEMA.md) — database tables and relationships
- [MODULES.md](MODULES.md) — inter-module dependencies
- [DEPLOYMENT.md](DEPLOYMENT.md) — Render & Docker deploy steps
- [ENV_GUIDE.md](ENV_GUIDE.md) — every environment variable explained

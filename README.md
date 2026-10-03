# Serenia Accounting — Enterprise Cloud ERP Platform

> Production-grade multi-company accounting and ERP platform for Chartered Accountants,
> Auditors, Business Owners, and Administrators.

---

## Technology Stack

| Layer       | Technology                                   |
|-------------|----------------------------------------------|
| Frontend    | React 18 + TypeScript + Tailwind CSS         |
| Backend     | Django 4.2 + Django REST Framework           |
| Database    | PostgreSQL 15                                |
| Cache       | Redis 7                                      |
| Task Queue  | Celery + Redis broker                        |
| Auth        | JWT (SimpleJWT)                              |
| Deployment  | Render / Docker                              |

---

## Modules

1. Company Management
2. Chart of Accounts
3. Ledger Management
4. Journal Entries
5. Voucher Management (Payment, Receipt, Contra, Journal, Sales, Purchase, CN, DN)
6. Final Accounts (Trial Balance, P&L, Balance Sheet, Cash Flow)
7. Financial Reporting
8. GST / TDS / TCS Taxation
9. Audit Module
10. Payroll Management
11. Inventory Management
12. Cost Centers
13. Multi-Currency Support
14. Banking & Reconciliation
15. Compliance Module
16. Corporate Advisory & KPI Dashboard
17. Developer Mode (Super Admin)

---

## Quick Start

```bash
# Clone and configure
cp .env.example .env
# Fill in .env values

# Docker
docker-compose up --build

# Or Render: push to GitHub → connect Render → deploy
```

---

## Folder Structure

```
serenia/
├── frontend/          # React + TypeScript SPA
├── backend/           # Django REST API
│   └── apps/          # Feature-based Django apps
├── docker/            # Dockerfiles
├── docs/              # Architecture & API docs
├── docker-compose.yml
├── render.yaml
└── .env.example
```

---

## Default Credentials (Development)

| Role            | Email                     | Password      |
|-----------------|---------------------------|---------------|
| Super Admin     | superadmin@serenia.app    | Serenia@2024  |
| Admin           | admin@serenia.app         | Serenia@2024  |
| Accountant      | accountant@serenia.app    | Serenia@2024  |
| Auditor         | auditor@serenia.app       | Serenia@2024  |

**Change all credentials before production deployment.**

---

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [Database Schema](docs/SCHEMA.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Environment Variables](docs/ENV_GUIDE.md)
- [Module Dependencies](docs/MODULES.md)
- [Developer Onboarding](docs/ONBOARDING.md)

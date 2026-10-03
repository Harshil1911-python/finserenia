# Serenia Accounting — Deployment Guide

## Option A: Deploy to Render (recommended)

Render reads `render.yaml` at the repo root and provisions everything
automatically (Blueprint deploy).

### Steps

1. **Push this repository to GitHub** (or GitLab/Bitbucket).
2. In the Render dashboard: **New → Blueprint** → connect your repo.
   Render detects `render.yaml` and proposes:
   - `serenia-db` (PostgreSQL, starter plan)
   - `serenia-redis` (Redis, starter plan)
   - `serenia-api` (Django web service)
   - `serenia-celery` (Celery worker)
   - `serenia-beat` (Celery beat scheduler)
   - `serenia-frontend` (React static site)

   `SECRET_KEY` and `DJANGO_SETTINGS_MODULE` are defined once in the
   `serenia-shared` env var group and automatically shared by all three
   Python services — no manual copying needed.

3. **Set secrets** marked `sync: false` in `render.yaml`, per service
   (Render dashboard → service → Environment), after the first deploy:
   - `SUPERADMIN_EMAIL` / `SUPERADMIN_PASSWORD` on `serenia-api` —
     overrides the defaults before the seed command runs. If left
     unset, defaults to `superadmin@serenia.app` / `Serenia@2024`
     (**change immediately after first login**).
   - `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` on `serenia-api` and
     `serenia-celery` if payroll/notification emails are needed.
   - `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` on `serenia-api` (and
     set `USE_S3=True`) if you need durable media storage — required
     for production logo/avatar uploads since Render web services have
     ephemeral disks.

4. **Update CORS / CSRF**: once `serenia-frontend` has its
   `.onrender.com` URL, confirm `CORS_ALLOWED_ORIGINS` and
   `CSRF_TRUSTED_ORIGINS` on all three Python services match it (the
   defaults in `render.yaml` assume the default service names
   `serenia-frontend`/`serenia-api` — update if you renamed services).

5. **Deploy**. For `serenia-api`, Render runs in order:
   - **Build**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Pre-deploy** (runs once before the new instance takes traffic):
     `python manage.py migrate --noinput && python manage.py seed_initial_data`
   - **Start**: Gunicorn

   Both the migration and seed command are idempotent — safe to run on
   every deploy.

6. Visit `serenia-frontend`'s URL and log in with the seeded Super Admin
   credentials. **Change the password immediately** via Settings →
   Change Password.

### Generating a frontend lockfile (recommended)
`render.yaml` and `Dockerfile.frontend` use `npm install` since no
`package-lock.json` is committed. For reproducible builds, run
`npm install` locally once, commit the generated `package-lock.json`,
then switch both build commands to `npm ci`.

### Health Checks
`serenia-api` exposes `GET /api/v1/health/` (checks DB + Redis
connectivity) — configured as Render's `healthCheckPath`.

---

## Option B: Docker Compose (local / self-hosted)

### Prerequisites
- Docker & Docker Compose v2
- 4GB+ RAM recommended

### Steps

```bash
# 1. Clone and configure environment
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY to a long random string

# 2. Build and start all services
docker-compose up --build -d

# 3. Watch logs (migrations + seed run automatically via the api service's command)
docker-compose logs -f api

# 4. Access the application
# Frontend:  http://localhost:3000
# API:       http://localhost:8000/api/v1/
# API docs:  http://localhost:8000/api/docs/
```

### Service breakdown
| Service | Port | Purpose |
|---|---|---|
| `db` | 5432 | PostgreSQL 15 |
| `redis` | 6379 | Cache, sessions, Celery broker |
| `api` | 8000 | Django + Gunicorn (runs migrate, collectstatic, seed on start) |
| `celery` | — | Background worker (default, reports, payroll, notifications queues) |
| `celery_beat` | — | Scheduled task dispatcher |
| `frontend` | 3000 → 80 | React build served via Nginx |

### Stopping / Resetting
```bash
docker-compose down            # stop containers, keep volumes (data persists)
docker-compose down -v         # stop and DELETE all data (fresh start)
```

---

## Production Checklist

- [ ] Change `SECRET_KEY` to a unique, long, random value
- [ ] Change the Super Admin password immediately after first login
- [ ] Set `DEBUG=False` (already default in `production.py`)
- [ ] Configure real SMTP credentials for email notifications
- [ ] Set `CORS_ALLOWED_ORIGINS` to your actual frontend domain(s) only
- [ ] Enable `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`,
      `CSRF_COOKIE_SECURE` (default `True` in production)
- [ ] Configure `AWS_*` / `USE_S3=True` if you need durable media
      storage beyond the container filesystem (Render web services have
      ephemeral disks — **required** for production logo/avatar uploads)
- [ ] Set up automated PostgreSQL backups (Render Postgres includes
      daily backups on paid plans; for Docker, schedule `pg_dump` via
      `celery_beat`)
- [ ] Review `AXES_FAILURE_LIMIT` / `AXES_COOLOFF_TIME` for your security
      policy
- [ ] Add a monitoring/error-tracking DSN (`sentry-sdk` is included in
      requirements — set `SENTRY_DSN` and wire it in
      `config/settings/production.py` if desired)

## Scaling Notes

- **API**: increase Gunicorn `--workers` (rule of thumb: `2 * CPU + 1`)
  or scale horizontally — stateless except for Redis-backed sessions.
- **Celery**: scale worker replicas independently per queue; the
  `payroll` queue is typically low-volume, `reports` can spike during
  month-end.
- **Database**: add read replicas for reporting queries once the
  dataset grows; the report views (`apps.reports.views`) are
  read-heavy and cache-friendly.
- **Redis**: monitor `maxmemory` usage — dashboard/report caches are
  capped via TTLs, but a high-cardinality multi-tenant deployment may
  need a larger plan.
